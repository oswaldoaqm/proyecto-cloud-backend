package seed

import (
    "fmt"
    "log"
    "math/rand"
    "ms2-models/models"
    "time"

    "gorm.io/gorm"
)

var frameworks  = []string{"pytorch", "tensorflow", "sklearn", "xgboost", "lightgbm"}
var estados     = []string{"en_prueba", "staging", "production", "deprecado"}
var tiposMetrica = []string{"accuracy", "f1", "rmse", "mae", "convergencia_ms", "precision", "recall"}

func Run(db *gorm.DB) {
    var count int64
    db.Model(&models.Experiment{}).Count(&count)
    if count > 0 {
        log.Printf("[seed] BD ya tiene %d experimentos. Omitiendo seed.", count)
        return
    }

    rng := rand.New(rand.NewSource(time.Now().UnixNano()))
    log.Println("[seed] Generando 50 experimentos, 1000 modelos y 20000 métricas...")

    for i := 1; i <= 50; i++ {
        exp := models.Experiment{
            Nombre:   fmt.Sprintf("Experimento_%02d_%s", i, frameworks[rng.Intn(len(frameworks))]),
            Objetivo: fmt.Sprintf("Optimizar %s para dataset_%03d", tiposMetrica[rng.Intn(3)], i),
            Status:   "activo",
        }
        db.Create(&exp)

        // 20 modelos por experimento = 1000 total
        for j := 1; j <= 20; j++ {
            framework := frameworks[rng.Intn(len(frameworks))]
            estado    := estados[rng.Intn(len(estados))]
            // Al menos 1 modelo en production por experimento
            if j == 1 {
                estado = "production"
            }

            mod := models.Modelo{
                ExperimentID: exp.ID,
                Nombre:       fmt.Sprintf("%s_model_%03d_%02d", framework, i, j),
                Version:      fmt.Sprintf("v%d.%d", rng.Intn(3)+1, rng.Intn(10)),
                Framework:    framework,
                Estado:       estado,
                DatasetID:    uint(rng.Intn(500) + 1), // Referencia a MS1
            }
            db.Create(&mod)

            // Artifact simulado en S3
            artifact := models.ModelArtifact{
                ModeloID:    mod.ID,
                ArtifactURL: fmt.Sprintf("s3://mlops-bucket/models/%s/%s.pkl", mod.Nombre, mod.Version),
                Checksum:    fmt.Sprintf("%x", rng.Int63()),
                TamanioMB:   float64(rng.Intn(500)+10) / 10.0,
            }
            db.Create(&artifact)

            // 20 métricas por modelo = 20000 total
            for k := 0; k < 20; k++ {
                tipo  := tiposMetrica[rng.Intn(len(tiposMetrica))]
                valor := 0.0
                switch tipo {
                case "accuracy", "f1", "precision", "recall":
                    valor = 0.5 + rng.Float64()*0.49 // Entre 0.5 y 0.99
                case "rmse", "mae":
                    valor = rng.Float64() * 100
                case "convergencia_ms":
                    valor = float64(rng.Intn(5000) + 100)
                }

                db.Create(&models.Metrica{
                    ModeloID:    mod.ID,
                    TipoMetrica: tipo,
                    Valor:       valor,
                    Epoch:       rng.Intn(100) + 1,
                })
            }
        }

        if i%10 == 0 {
            log.Printf("[seed] %d experimentos procesados...", i)
        }
    }

    log.Println("[seed]  Seed completo: 50 experimentos, 1000 modelos, 20000 métricas.")
}
