from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import Dataset, Feature

router = APIRouter()

# ── Schemas de respuesta (lo que devuelve la API en JSON) ──────────────────

class FeatureOut(BaseModel):
    id:              int
    dataset_id:      int
    nombre_variable: str
    tipo_dato:       str
    es_categorica:   bool
    rango_valores:   Optional[str]
    created_at:      datetime

    class Config:
        from_attributes = True

class DatasetOut(BaseModel):
    id:          int
    nombre:      str
    dominio:     str
    descripcion: Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True

class DatasetDetail(DatasetOut):
    total_features: int

# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "service": "ms1-features"}


@router.get("/datasets", response_model=List[DatasetDetail], tags=["Datasets"],
            summary="Lista todos los datasets",
            description="Devuelve todos los datasets registrados con el conteo de features.")
def list_datasets(
    dominio: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(
        Dataset,
        func.count(Feature.id).label("total_features")
    ).outerjoin(Feature).group_by(Dataset.id)

    if dominio:
        query = query.filter(Dataset.dominio == dominio)

    results = query.offset(skip).limit(limit).all()

    return [
        DatasetDetail(
            **{c.name: getattr(ds, c.name) for c in Dataset.__table__.columns},
            total_features=count
        )
        for ds, count in results
    ]


@router.get("/datasets/{dataset_id}", response_model=DatasetOut, tags=["Datasets"],
            summary="Obtiene un dataset por ID")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return ds


@router.get("/datasets/{dataset_id}/features", response_model=List[FeatureOut],
            tags=["Features"],
            summary="Lista las features de un dataset")
def list_features(
    dataset_id: int,
    tipo_dato: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")

    query = db.query(Feature).filter(Feature.dataset_id == dataset_id)
    if tipo_dato:
        query = query.filter(Feature.tipo_dato == tipo_dato)

    return query.offset(skip).limit(limit).all()


@router.get("/features/{feature_id}", response_model=FeatureOut, tags=["Features"],
            summary="Obtiene una feature por ID")
def get_feature(feature_id: int, db: Session = Depends(get_db)):
    feat = db.query(Feature).filter(Feature.id == feature_id).first()
    if not feat:
        raise HTTPException(status_code=404, detail="Feature no encontrada")
    return feat


@router.get("/stats", tags=["Stats"],
            summary="Estadísticas generales del Feature Store")
def get_stats(db: Session = Depends(get_db)):
    total_datasets  = db.query(func.count(Dataset.id)).scalar()
    total_features  = db.query(func.count(Feature.id)).scalar()
    dominios        = db.query(Dataset.dominio, func.count(Dataset.id))\
                        .group_by(Dataset.dominio).all()
    tipos           = db.query(Feature.tipo_dato, func.count(Feature.id))\
                        .group_by(Feature.tipo_dato).all()

    return {
        "total_datasets": total_datasets,
        "total_features": total_features,
        "datasets_por_dominio": {d: c for d, c in dominios},
        "features_por_tipo":    {t: c for t, c in tipos}
    }
