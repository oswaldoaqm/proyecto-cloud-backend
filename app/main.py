from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models import Base
from app.routes import router
from app.seed import run_seed

app = FastAPI(
    title="MS1 — Feature Catalog",
    description="Feature Store para la plataforma MLOps Lite. Registra datasets y sus variables.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
def startup():
    print("[startup] Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    print("[startup] Tablas listas. Ejecutando seed...")
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    print("[startup] MS1 listo.")
