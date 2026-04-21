import random
from faker import Faker
from sqlalchemy.orm import Session
from app.models import Dataset, Feature

fake = Faker("es_MX")

DOMINIOS = [
    "scoring_crediticio", "deteccion_fraude", "churn_prediction",
    "recomendacion", "computer_vision", "nlp", "forecasting",
    "segmentacion_clientes", "pricing_dinamico", "deteccion_anomalias"
]

TIPOS_DATO = ["float", "int", "bool", "string", "datetime", "categorical"]

PREFIJOS_FEATURE = [
    "edad", "ingreso", "score", "ratio", "tasa", "promedio",
    "total", "cantidad", "dias", "meses", "nivel", "flag",
    "porcentaje", "monto", "frecuencia", "conteo", "ultima"
]

def run_seed(db: Session):
    existing = db.query(Dataset).count()
    if existing > 0:
        print(f"[seed] BD ya tiene {existing} datasets. Omitiendo seed.")
        return

    print("[seed] Iniciando generación de 500 datasets y 20,000 features...")

    datasets_creados = []
    for i in range(500):
        dominio = random.choice(DOMINIOS)
        ds = Dataset(
            nombre      = f"dataset_{dominio}_{fake.bothify('??##')}",
            dominio     = dominio,
            descripcion = fake.sentence(nb_words=12)
        )
        db.add(ds)
        datasets_creados.append(ds)

        # Guardamos cada 50 para no saturar la memoria
        if (i + 1) % 50 == 0:
            db.flush()
            print(f"[seed] {i + 1} datasets creados...")

    db.flush()

    print("[seed] Generando 40 features por dataset (20,000 total)...")
    feature_count = 0
    for ds in datasets_creados:
        for j in range(40):
            prefijo = random.choice(PREFIJOS_FEATURE)
            tipo    = random.choice(TIPOS_DATO)
            es_cat  = tipo == "categorical"
            rango   = None

            if tipo == "float":
                lo, hi = sorted([round(random.uniform(0, 100), 2) for _ in range(2)])
                rango = f"{lo}-{hi}"
            elif tipo == "int":
                lo, hi = sorted(random.sample(range(0, 10000), 2))
                rango = f"{lo}-{hi}"
            elif es_cat:
                cats = [fake.word() for _ in range(random.randint(3, 8))]
                rango = ",".join(cats)

            feat = Feature(
                dataset_id      = ds.id,
                nombre_variable = f"{prefijo}_{fake.bothify('????##')}",
                tipo_dato       = tipo,
                es_categorica   = es_cat,
                rango_valores   = rango
            )
            db.add(feat)
            feature_count += 1

        if feature_count % 2000 == 0:
            db.flush()
            print(f"[seed] {feature_count} features creadas...")

    db.commit()
    print(f"[seed]  Seed completo: 500 datasets y {feature_count} features.")
