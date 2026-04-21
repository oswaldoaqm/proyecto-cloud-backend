package main

import (
    "fmt"
    "log"
    "ms2-models/database"
    "ms2-models/models"
    "ms2-models/routes"
    "ms2-models/seed"
    "os"

    "github.com/gin-contrib/cors"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
)

func main() {
    // Cargar variables de entorno
    if err := godotenv.Load(); err != nil {
        log.Println("[main] No se encontró .env, usando variables del sistema")
    }

    // Conectar a MySQL
    database.Connect()

    // Crear tablas automáticamente
    database.DB.AutoMigrate(
        &models.Experiment{},
        &models.Modelo{},
        &models.ModelArtifact{},
        &models.Metrica{},
    )
    log.Println("[main] Tablas creadas/verificadas en MySQL")

    // Ejecutar seed si la BD está vacía
    seed.Run(database.DB)

    // Configurar el servidor Gin
    r := gin.Default()

    // CORS para que el frontend pueda consumir la API
    r.Use(cors.New(cors.Config{
        AllowOrigins: []string{"*"},
        AllowMethods: []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
        AllowHeaders: []string{"*"},
    }))

    // Registrar rutas
    routes.Register(r)

    port := os.Getenv("PORT")
    if port == "" {
        port = "8002"
    }

    fmt.Printf("[main] MS2 corriendo en puerto %s\n", port)
    r.Run(":" + port)
}
