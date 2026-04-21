require('dotenv').config()
const express = require('express')
const cors    = require('cors')
const { connect } = require('./database')
const { run: runSeed } = require('./seed')
const routes  = require('./routes')

const app  = express()
const PORT = process.env.PORT || 8003

app.use(cors())
app.use(express.json({ limit: '10mb' }))

// Documentación manual (Swagger no es nativo en Express)
app.get('/', (req, res) => {
  res.json({
    service:   'MS3 — Prediction Logs & Feedback',
    version:   '1.0.0',
    endpoints: {
      'GET  /api/v1/health':          'Estado del servicio',
      'GET  /api/v1/logs':            'Lista logs (query: modelo_id, label, limit, skip)',
      'POST /api/v1/logs':            'Crea un log de predicción',
      'GET  /api/v1/logs/recent':     'Logs recientes (query: days)',
      'GET  /api/v1/logs/stats':      'Estadísticas generales',
      'POST /api/v1/feedback':        'Registra feedback de analista',
      'GET  /api/v1/feedback/stats':  'Métricas de calidad (query: modelo_id)'
    }
  })
})

app.use('/api/v1', routes)

const start = async () => {
  await connect()
  await runSeed()
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[main] MS3 corriendo en puerto ${PORT}`)
  })
}

start()
