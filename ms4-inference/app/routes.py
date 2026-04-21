from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from app.clients import get_model, save_log, check_service
from app.inference import predict

router = APIRouter()

MS2_URL = os.getenv("MS2_URL", "")
MS3_URL = os.getenv("MS3_URL", "")


# ── Schemas ────────────────────────────────────────────────────────────────

class InferRequest(BaseModel):
    modelo_id: int
    features:  dict

    class Config:
        json_schema_extra = {
            "example": {
                "modelo_id": 1,
                "features": {
                    "edad": 32,
                    "ingreso_mensual": 4500,
                    "score_historial": 0.72,
                    "deuda_actual": 8000,
                    "años_empleo": 5
                }
            }
        }


class BatchInferRequest(BaseModel):
    modelo_id: int
    casos:     list[dict]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "service": "ms4-inference"}


@router.get("/health/deep", tags=["Sistema"],
            summary="Verifica el estado de todos los microservicios dependientes")
async def health_deep():
    ms2_status = await check_service(MS2_URL, "ms2-models")
    ms3_status = await check_service(MS3_URL, "ms3-logs")

    overall = "ok" if all(
        s["status"] == "ok" for s in [ms2_status, ms3_status]
    ) else "degraded"

    return {
        "status":   overall,
        "services": [ms2_status, ms3_status]
    }


@router.post("/infer", tags=["Inferencia"],
             summary="Realiza una predicción de scoring crediticio",
             description="""
Flujo completo:
1. Verifica que el modelo existe y está en estado **production** (MS2)
2. Calcula el score crediticio con las features recibidas
3. Guarda el log de predicción (MS3)
4. Devuelve el resultado con explicación de features relevantes
""")
async def infer(request: InferRequest):

    # Paso 1 — Verificar modelo en MS2
    try:
        modelo = await get_model(request.modelo_id)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if modelo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Modelo {request.modelo_id} no encontrado en MS2"
        )

    if modelo.get("estado") != "production":
        raise HTTPException(
            status_code=400,
            detail=f"Modelo {request.modelo_id} no está en production (estado actual: {modelo.get('estado')})"
        )

    # Paso 2 — Generar predicción
    resultado = predict(request.features, request.modelo_id)

    # Paso 3 — Guardar log en MS3
    try:
        log = await save_log({
            "modelo_id":         request.modelo_id,
            "modelo_version":    modelo.get("version", "v1.0"),
            "input_features":    request.features,
            "prediccion_output": resultado["prediccion_output"],
            "prediccion_label":  resultado["prediccion_label"],
            "latencia_ms":       resultado["latencia_ms"]
        })
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Paso 4 — Respuesta enriquecida
    return {
        "log_id":              log.get("log_id"),
        "modelo_id":           request.modelo_id,
        "modelo_nombre":       modelo.get("nombre"),
        "modelo_version":      modelo.get("version"),
        "prediccion_output":   resultado["prediccion_output"],
        "prediccion_label":    resultado["prediccion_label"],
        "latencia_ms":         resultado["latencia_ms"],
        "features_relevantes": resultado["features_relevantes"]
    }


@router.post("/infer/batch", tags=["Inferencia"],
             summary="Procesa múltiples casos en una sola petición")
async def infer_batch(request: BatchInferRequest):

    # Verificar modelo una sola vez para todo el batch
    try:
        modelo = await get_model(request.modelo_id)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if modelo is None:
        raise HTTPException(status_code=404, detail=f"Modelo {request.modelo_id} no encontrado")

    if modelo.get("estado") != "production":
        raise HTTPException(status_code=400, detail=f"Modelo no está en production")

    if len(request.casos) > 100:
        raise HTTPException(status_code=400, detail="Máximo 100 casos por batch")

    resultados = []
    for features in request.casos:
        resultado = predict(features, request.modelo_id)
        try:
            log = await save_log({
                "modelo_id":         request.modelo_id,
                "modelo_version":    modelo.get("version", "v1.0"),
                "input_features":    features,
                "prediccion_output": resultado["prediccion_output"],
                "prediccion_label":  resultado["prediccion_label"],
                "latencia_ms":       resultado["latencia_ms"]
            })
            resultados.append({
                "log_id":            log.get("log_id"),
                "prediccion_output": resultado["prediccion_output"],
                "prediccion_label":  resultado["prediccion_label"]
            })
        except Exception:
            resultados.append({
                "error": "No se pudo guardar el log",
                "prediccion_output": resultado["prediccion_output"],
                "prediccion_label":  resultado["prediccion_label"]
            })

    return {
        "modelo_id":    request.modelo_id,
        "total_casos":  len(resultados),
        "aprobados":    sum(1 for r in resultados if r.get("prediccion_label") == "aprobado"),
        "rechazados":   sum(1 for r in resultados if r.get("prediccion_label") == "rechazado"),
        "resultados":   resultados
    }


@router.get("/models/active", tags=["Modelos"],
            summary="Lista modelos activos en production (proxy a MS2)")
async def active_models():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MS2_URL}/api/v1/models?estado=production")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MS2 no disponible: {e}")
