const express   = require('express')
const { v4: uuidv4 } = require('uuid')
const { PredictionLog, Feedback } = require('./models')

const router = express.Router()

// ── Health ─────────────────────────────────────────────────────────────────

router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'ms3-logs' })
})

// ── Prediction Logs ────────────────────────────────────────────────────────

// GET /logs — lista logs con filtros opcionales
router.get('/logs', async (req, res) => {
  try {
    const { modelo_id, label, limit = 50, skip = 0 } = req.query
    const filter = {}
    if (modelo_id) filter.modelo_id = parseInt(modelo_id)
    if (label)     filter.prediccion_label = label

    const logs = await PredictionLog
      .find(filter)
      .sort({ timestamp: -1 })
      .skip(parseInt(skip))
      .limit(parseInt(limit))

    const total = await PredictionLog.countDocuments(filter)
    res.json({ total, logs })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// POST /logs — crea un nuevo log (lo llama MS4)
router.post('/logs', async (req, res) => {
  try {
    const {
      modelo_id, modelo_version, input_features,
      prediccion_output, prediccion_label, latencia_ms
    } = req.body

    if (!modelo_id || prediccion_output === undefined || !prediccion_label) {
      return res.status(400).json({ error: 'Faltan campos requeridos: modelo_id, prediccion_output, prediccion_label' })
    }

    const log = new PredictionLog({
      log_id:            uuidv4(),
      modelo_id,
      modelo_version:    modelo_version || 'v1.0',
      input_features:    input_features || {},
      prediccion_output,
      prediccion_label,
      latencia_ms:       latencia_ms || 0,
      entorno:           'produccion'
    })

    await log.save()
    res.status(201).json(log)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// GET /logs/recent — logs de los últimos N días
router.get('/logs/recent', async (req, res) => {
  try {
    const days  = parseInt(req.query.days) || 7
    const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000)

    const logs = await PredictionLog
      .find({ timestamp: { $gte: since } })
      .sort({ timestamp: -1 })
      .limit(200)

    res.json({ days, total: logs.length, logs })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// GET /logs/stats — estadísticas generales
router.get('/logs/stats', async (req, res) => {
  try {
    const total      = await PredictionLog.countDocuments()
    const aprobados  = await PredictionLog.countDocuments({ prediccion_label: 'aprobado' })
    const rechazados = await PredictionLog.countDocuments({ prediccion_label: 'rechazado' })

    const avgOutput = await PredictionLog.aggregate([
      { $group: { _id: null, avg: { $avg: '$prediccion_output' }, avgLatencia: { $avg: '$latencia_ms' } } }
    ])

    const porModelo = await PredictionLog.aggregate([
      { $group: { _id: '$modelo_id', total: { $sum: 1 } } },
      { $sort: { total: -1 } },
      { $limit: 10 }
    ])

    res.json({
      total_logs:       total,
      aprobados,
      rechazados,
      tasa_aprobacion:  total > 0 ? (aprobados / total).toFixed(4) : 0,
      avg_prediccion:   avgOutput[0]?.avg?.toFixed(4) || 0,
      avg_latencia_ms:  avgOutput[0]?.avgLatencia?.toFixed(2) || 0,
      top_10_modelos:   porModelo
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Feedback ───────────────────────────────────────────────────────────────

// POST /feedback — el analista registra si el modelo acertó
router.post('/feedback', async (req, res) => {
  try {
    const { log_id, analista_id, real_label, feedback_tipo, impacto_usd, comentario } = req.body

    if (!log_id || !analista_id || !real_label || !feedback_tipo) {
      return res.status(400).json({ error: 'Faltan campos: log_id, analista_id, real_label, feedback_tipo' })
    }

    const logExiste = await PredictionLog.findOne({ log_id })
    if (!logExiste) {
      return res.status(404).json({ error: `Log ${log_id} no encontrado` })
    }

    const feedback = new Feedback({
      feedback_id:   uuidv4(),
      log_id,
      analista_id,
      real_label,
      feedback_tipo,
      impacto_usd:   impacto_usd || 0,
      comentario:    comentario || ''
    })

    await feedback.save()
    res.status(201).json(feedback)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// GET /feedback/stats — métricas de calidad del modelo
router.get('/feedback/stats', async (req, res) => {
  try {
    const { modelo_id } = req.query

    // Si filtramos por modelo, necesitamos cruzar con logs
    const matchLogs = modelo_id
      ? await PredictionLog.find({ modelo_id: parseInt(modelo_id) }).select('log_id')
      : null

    const filter = matchLogs
      ? { log_id: { $in: matchLogs.map(l => l.log_id) } }
      : {}

    const total = await Feedback.countDocuments(filter)

    const porTipo = await Feedback.aggregate([
      { $match: filter },
      { $group: { _id: '$feedback_tipo', count: { $sum: 1 }, impacto_total: { $sum: '$impacto_usd' } } }
    ])

    const impactoTotal = await Feedback.aggregate([
      { $match: filter },
      { $group: { _id: null, total: { $sum: '$impacto_usd' } } }
    ])

    res.json({
      total_feedbacks: total,
      por_tipo:        porTipo,
      impacto_total_usd: impactoTotal[0]?.total?.toFixed(2) || 0
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

module.exports = router
