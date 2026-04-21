package database

import (
    "fmt"
    "log"
    "os"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

var DB *gorm.DB

func Connect() {
    host     := os.Getenv("DB_HOST")
    port     := os.Getenv("DB_PORT")
    name     := os.Getenv("DB_NAME")
    user     := os.Getenv("DB_USER")
    password := os.Getenv("DB_PASSWORD")

    dsn := fmt.Sprintf(
        "%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=True&loc=UTC",
        user, password, host, port, name,
    )

    var err error
    DB, err = gorm.Open(mysql.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Warn),
    })
    if err != nil {
        log.Fatalf("[database] Error conectando a MySQL: %v", err)
    }

    sqlDB, _ := DB.DB()
    sqlDB.SetMaxOpenConns(20)
    sqlDB.SetMaxIdleConns(5)

    log.Println("[database] Conexión a MySQL establecida")
}
