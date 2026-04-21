import os
import httpx
from dotenv import load_dotenv

load_dotenv()

MS2_URL = os.getenv("MS2_URL")
MS3_URL = os.getenv("MS3_URL")

# Cliente HTTP reutilizable con timeout de 10 segundos
_client = httpx.AsyncClient(timeout=10.0)


async def get_model(modelo_id: int) -> dict | None:
    """
    Consulta MS2 para verificar que el modelo existe y está en production.
    Devuelve el modelo si existe, None si no.
    """
    try:
        response = await _client.get(f"{MS2_URL}/api/v1/models/{modelo_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except httpx.RequestError as e:
        raise ConnectionError(f"MS2 no disponible: {e}")


async def save_log(payload: dict) -> dict:
    """
    Llama a MS3 para guardar el log de predicción.
    Devuelve el log creado con su log_id.
    """
    try:
        response = await _client.post(
            f"{MS3_URL}/api/v1/logs",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        raise ConnectionError(f"MS3 no disponible: {e}")


async def check_service(url: str, name: str) -> dict:
    """
    Verifica si un microservicio está respondiendo.
    Lo usa el endpoint /health/deep.
    """
    try:
        response = await _client.get(f"{url}/api/v1/health", timeout=3.0)
        if response.status_code == 200:
            return {"service": name, "status": "ok"}
        return {"service": name, "status": "degraded"}
    except Exception:
        return {"service": name, "status": "down"}
