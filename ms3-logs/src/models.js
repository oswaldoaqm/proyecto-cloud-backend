const mongoose = require('mongoose')
const { Schema } = mongoose

// ── Colección 1: prediction_logs ──────────────────────────────────────────
// Guarda cada predicción que hace el modelo en producción

const PredictionLogSchema = new Schema({
  log_id:             { type: String, required: true, unique: true, index: true },
  modelo_id:          { type: Number, required: true, index: true },
  modelo_version:     { type: String, required: true },
  input_features:     { type: Schema.Types.Mixed, required: true },
  prediccion_output:  { type: Number, required: true, min: 0, max: 1 },
  prediccion_label:   { type: String, enum: ['aprobado', 'rechazado'], required: true },
  latencia_ms:        { type: Number, default: 0 },
  entorno:            { type: String, default: 'produccion' },
  timestamp:          { type: Date, default: Date.now, index: true }
})

// ── Colección 2: feedback_loop ────────────────────────────────────────────
// El analista humano corrige si el modelo acertó o no

const FeedbackSchema = new Schema({
  feedback_id:   { type: String, required: true, unique: true },
  log_id:        { type: String, required: true, index: true },
  analista_id:   { type: String, required: true },
  real_label:    { type: String, enum: ['aprobado', 'rechazado'], required: true },
  feedback_tipo: {
    type: String,
    enum: ['true_positive', 'true_negative', 'false_positive', 'false_negative'],
    required: true
  },
  impacto_usd:   { type: Number, default: 0 },
  comentario:    { type: String },
  timestamp:     { type: Date, default: Date.now }
})

const PredictionLog = mongoose.model('PredictionLog', PredictionLogSchema)
const Feedback      = mongoose.model('Feedback', FeedbackSchema)

module.exports = { PredictionLog, Feedback }
