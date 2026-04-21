package routes

import (
    "ms2-models/database"
    "ms2-models/models"
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"
)

func Register(r *gin.Engine) {
    v1 := r.Group("/api/v1")

    v1.GET("/health", health)

    v1.GET("/experiments",          listExperiments)
    v1.POST("/experiments",         createExperiment)
    v1.GET("/experiments/:id",      getExperiment)
    v1.GET("/experiments/:id/leaderboard", leaderboard)

    v1.GET("/models",               listModels)
    v1.POST("/models",              createModel)
    v1.GET("/models/:id",           getModel)
    v1.PATCH("/models/:id/stage",   stageModel)

    v1.GET("/models/:id/metrics",   listMetrics)
    v1.POST("/models/:id/metrics",  addMetric)

    v1.GET("/stats",                getStats)
}

func health(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"status": "ok", "service": "ms2-models"})
}

// ── EXPERIMENTS ────────────────────────────────────────────────────────────

func listExperiments(c *gin.Context) {
    var exps []models.Experiment
    database.DB.Find(&exps)
    c.JSON(http.StatusOK, exps)
}

func createExperiment(c *gin.Context) {
    var input struct {
        Nombre   string `json:"nombre"   binding:"required"`
        Objetivo string `json:"objetivo"`
    }
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    exp := models.Experiment{Nombre: input.Nombre, Objetivo: input.Objetivo, Status: "activo"}
    database.DB.Create(&exp)
    c.JSON(http.StatusCreated, exp)
}

func getExperiment(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))
    var exp models.Experiment
    if err := database.DB.Preload("Modelos").First(&exp, id).Error; err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Experimento no encontrado"})
        return
    }
    c.JSON(http.StatusOK, exp)
}

func leaderboard(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))
    var results []struct {
        ModeloID  uint    `json:"modelo_id"`
        Nombre    string  `json:"nombre"`
        Version   string  `json:"version"`
        Framework string  `json:"framework"`
        Estado    string  `json:"estado"`
        AvgAcc    float64 `json:"avg_accuracy"`
    }
    database.DB.Raw(`
        SELECT m.id as modelo_id, m.nombre, m.version, m.framework, m.estado,
               AVG(CASE WHEN mt.tipo_metrica = 'accuracy' THEN mt.valor ELSE NULL END) as avg_acc
        FROM modelos m
        LEFT JOIN metricas mt ON mt.modelo_id = m.id
        WHERE m.experiment_id = ?
        GROUP BY m.id, m.nombre, m.version, m.framework, m.estado
        ORDER BY avg_acc DESC
    `, id).Scan(&results)
    c.JSON(http.StatusOK, results)
}

// ── MODELS ─────────────────────────────────────────────────────────────────

func listModels(c *gin.Context) {
    estado    := c.Query("estado")
    framework := c.Query("framework")

    query := database.DB.Model(&models.Modelo{})
    if estado    != "" { query = query.Where("estado = ?", estado) }
    if framework != "" { query = query.Where("framework = ?", framework) }

    var mods []models.Modelo
    query.Find(&mods)
    c.JSON(http.StatusOK, mods)
}

func createModel(c *gin.Context) {
    var input struct {
        ExperimentID uint   `json:"experiment_id" binding:"required"`
        Nombre       string `json:"nombre"        binding:"required"`
        Version      string `json:"version"       binding:"required"`
        Framework    string `json:"framework"     binding:"required"`
        DatasetID    uint   `json:"dataset_id"    binding:"required"`
    }
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    mod := models.Modelo{
        ExperimentID: input.ExperimentID,
        Nombre:       input.Nombre,
        Version:      input.Version,
        Framework:    input.Framework,
        Estado:       "en_prueba",
        DatasetID:    input.DatasetID,
    }
    database.DB.Create(&mod)
    c.JSON(http.StatusCreated, mod)
}

func getModel(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))
    var mod models.Modelo
    if err := database.DB.First(&mod, id).Error; err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Modelo no encontrado"})
        return
    }
    c.JSON(http.StatusOK, mod)
}

func stageModel(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))
    var input struct {
        Estado string `json:"estado" binding:"required"`
    }
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    allowed := map[string]bool{"en_prueba": true, "staging": true, "production": true, "deprecado": true}
    if !allowed[input.Estado] {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Estado inválido"})
        return
    }
    result := database.DB.Model(&models.Modelo{}).Where("id = ?", id).Update("estado", input.Estado)
    if result.RowsAffected == 0 {
        c.JSON(http.StatusNotFound, gin.H{"error": "Modelo no encontrado"})
        return
    }
    var mod models.Modelo
    database.DB.First(&mod, id)
    c.JSON(http.StatusOK, mod)
}

// ── METRICS ────────────────────────────────────────────────────────────────

func listMetrics(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))
    var metricas []models.Metrica
    database.DB.Where("modelo_id = ?", id).Find(&metricas)
    c.JSON(http.StatusOK, metricas)
}

func addMetric(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))

    var mod models.Modelo
    if err := database.DB.First(&mod, id).Error; err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Modelo no encontrado"})
        return
    }

    var input struct {
        TipoMetrica string  `json:"tipo_metrica" binding:"required"`
        Valor       float64 `json:"valor"        binding:"required"`
        Epoch       int     `json:"epoch"`
    }
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    met := models.Metrica{
        ModeloID:    uint(id),
        TipoMetrica: input.TipoMetrica,
        Valor:       input.Valor,
        Epoch:       input.Epoch,
    }
    database.DB.Create(&met)
    c.JSON(http.StatusCreated, met)
}

// ── STATS ──────────────────────────────────────────────────────────────────

func getStats(c *gin.Context) {
    var totalModelos, totalMetricas, totalExps int64
    database.DB.Model(&models.Modelo{}).Count(&totalModelos)
    database.DB.Model(&models.Metrica{}).Count(&totalMetricas)
    database.DB.Model(&models.Experiment{}).Count(&totalExps)

    var byFramework []struct {
        Framework string  `json:"framework"`
        Total     int64   `json:"total"`
        AvgAcc    float64 `json:"avg_accuracy"`
    }
    database.DB.Raw(`
        SELECT m.framework,
               COUNT(DISTINCT m.id) as total,
               AVG(CASE WHEN mt.tipo_metrica='accuracy' THEN mt.valor ELSE NULL END) as avg_acc
        FROM modelos m
        LEFT JOIN metricas mt ON mt.modelo_id = m.id
        GROUP BY m.framework
    `).Scan(&byFramework)

    c.JSON(http.StatusOK, gin.H{
        "total_experimentos": totalExps,
        "total_modelos":      totalModelos,
        "total_metricas":     totalMetricas,
        "por_framework":      byFramework,
    })
}
