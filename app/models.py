from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Dataset(Base):
    __tablename__ = "dataset"

    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(200), nullable=False)
    dominio     = Column(String(100), nullable=False)
    descripcion = Column(Text)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    features = relationship("Feature", back_populates="dataset", cascade="all, delete")

class Feature(Base):
    __tablename__ = "feature"

    id              = Column(Integer, primary_key=True, index=True)
    dataset_id      = Column(Integer, ForeignKey("dataset.id"), nullable=False)
    nombre_variable = Column(String(200), nullable=False)
    tipo_dato       = Column(String(50),  nullable=False)
    es_categorica   = Column(Boolean, default=False)
    rango_valores   = Column(Text)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="features")
