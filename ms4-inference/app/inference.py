import random
import time


def predict(features: dict, modelo_id: int) -> dict:
    """
    Simula la inferencia de un modelo de scoring crediticio.
    Usa las features para calcular un score coherente.
    """
    start = time.time()

    # Factores que influyen en el score (lógica simulada)
    score = 0.5  # base

    # Edad: entre 25 y 55 es el rango más confiable
    edad = features.get("edad", 35)
    if 25 <= edad <= 55:
        score += 0.05
    elif edad < 20 or edad > 70:
        score -= 0.1

    # Ingreso mensual: más ingreso → más probabilidad de aprobación
    ingreso = features.get("ingreso_mensual", 2000)
    if ingreso > 8000:
        score += 0.2
    elif ingreso > 4000:
        score += 0.1
    elif ingreso < 1000:
        score -= 0.15

    # Score historial crediticio previo
    historial = features.get("score_historial", 0.5)
    score += (historial - 0.5) * 0.3

    # Deuda actual vs ingreso (ratio deuda/ingreso)
    deuda    = features.get("deuda_actual", 0)
    if ingreso > 0:
        ratio_deuda = deuda / ingreso
        if ratio_deuda > 5:
            score -= 0.2
        elif ratio_deuda > 2:
            score -= 0.1

    # Años de empleo
    años_empleo = features.get("años_empleo", 2)
    if años_empleo >= 3:
        score += 0.05

    # Pequeño factor aleatorio para que no sea completamente determinista
    score += random.uniform(-0.05, 0.05)

    # Clamp entre 0.01 y 0.99
    score = max(0.01, min(0.99, score))
    score = round(score, 4)

    latencia_ms = int((time.time() - start) * 1000) + random.randint(10, 80)

    return {
        "prediccion_output": score,
        "prediccion_label":  "aprobado" if score >= 0.5 else "rechazado",
        "latencia_ms":       latencia_ms,
        # Simula qué features influyeron más en la decisión
        "features_relevantes": _top_features(features)
    }


def _top_features(features: dict) -> list:
    """Devuelve las 3 features más relevantes para explicar la predicción."""
    ranking = {
        "score_historial":   features.get("score_historial", 0) * 100,
        "ingreso_mensual":   min(features.get("ingreso_mensual", 0) / 150, 100),
        "deuda_actual":      max(0, 100 - features.get("deuda_actual", 0) / 500),
        "edad":              50 if 25 <= features.get("edad", 35) <= 55 else 20,
        "años_empleo":       min(features.get("años_empleo", 0) * 10, 50),
    }
    top = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:3]
    return [{"feature": k, "importancia": round(v, 2)} for k, v in top]
