from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes import router

load_dotenv()

app = FastAPI(
    title="MS4 — Inference Gateway",
    description="""
Orquestador central de la plataforma MLOps Lite.

**No tiene base de datos propia.** Coordina:
- **MS2** (Model Registry): verifica que el modelo exista y esté en production
- **MS3** (Prediction Logs): guarda cada predicción realizada
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
