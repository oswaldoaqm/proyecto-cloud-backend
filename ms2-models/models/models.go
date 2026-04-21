package models

import "time"

// Experiment agrupa varios modelos bajo un mismo objetivo
type Experiment struct {
    ID        uint      `gorm:"primaryKey;autoIncrement" json:"id"`
    Nombre    string    `gorm:"size:200;not null"        json:"nombre"`
    Objetivo  string    `gorm:"size:500"                 json:"objetivo"`
    Status    string    `gorm:"size:50;default:'activo'" json:"status"`
    CreatedAt time.Time `gorm:"autoCreateTime"           json:"created_at"`
    Modelos   []Modelo  `gorm:"foreignKey:ExperimentID"  json:"modelos,omitempty"`
}

// Modelo representa un modelo de ML entrenado
type Modelo struct {
    ID           uint            `gorm:"primaryKey;autoIncrement" json:"id"`
    ExperimentID uint            `gorm:"not null;index"           json:"experiment_id"`
    Nombre       string          `gorm:"size:200;not null"        json:"nombre"`
    Version      string          `gorm:"size:50;not null"         json:"version"`
    Framework    string          `gorm:"size:100;not null"        json:"framework"`
    Estado       string          `gorm:"size:50;default:'en_prueba'" json:"estado"`
    DatasetID    uint            `gorm:"not null"                 json:"dataset_id"`
    CreatedAt    time.Time       `gorm:"autoCreateTime"           json:"created_at"`
    Metricas     []Metrica       `gorm:"foreignKey:ModeloID"      json:"metricas,omitempty"`
    Artifacts    []ModelArtifact `gorm:"foreignKey:ModeloID"      json:"artifacts,omitempty"`
}

// ModelArtifact guarda la ruta al archivo del modelo en S3
type ModelArtifact struct {
    ID          uint      `gorm:"primaryKey;autoIncrement" json:"id"`
    ModeloID    uint      `gorm:"not null;index"           json:"modelo_id"`
    ArtifactURL string    `gorm:"size:500"                 json:"artifact_url"`
    Checksum    string    `gorm:"size:64"                  json:"checksum"`
    TamanioMB   float64   `gorm:"default:0"                json:"tamanio_mb"`
    CreatedAt   time.Time `gorm:"autoCreateTime"           json:"created_at"`
}

// Metrica almacena resultados de evaluación de un modelo
type Metrica struct {
    ID          uint      `gorm:"primaryKey;autoIncrement" json:"id"`
    ModeloID    uint      `gorm:"not null;index"           json:"modelo_id"`
    TipoMetrica string    `gorm:"size:100;not null"        json:"tipo_metrica"`
    Valor       float64   `gorm:"not null"                 json:"valor"`
    Epoch       int       `gorm:"default:0"                json:"epoch"`
    CreatedAt   time.Time `gorm:"autoCreateTime"           json:"created_at"`
}
