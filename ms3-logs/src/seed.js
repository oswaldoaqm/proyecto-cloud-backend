const { faker } = require('@faker-js/faker')
const { v4: uuidv4 } = require('uuid')
const { PredictionLog, Feedback } = require('./models')

// Features de entrada simuladas para scoring crediticio
const generateFeatures = () => ({
  edad:             faker.number.int({ min: 18, max: 75 }),
  ingreso_mensual:  parseFloat(faker.finance.amount({ min: 500, max: 15000, dec: 2 })),
  score_historial:  parseFloat((Math.random() * 0.8 + 0.1).toFixed(3)),
  deuda_actual:     parseFloat(faker.finance.amount({ min: 0, max: 50000, dec: 2 })),
  años_empleo:      faker.number.int({ min: 0, max: 40 }),
  num_creditos:     faker.number.int({ min: 0, max: 10 }),
  tiene_propiedad:  faker.datatype.boolean()
})

const run = async () => {
  const existingCount = await PredictionLog.countDocuments()
  if (existingCount > 0) {
    console.log(`[seed] BD ya tiene ${existingCount} logs. Omitiendo seed.`)
    return
  }

  console.log('[seed] Generando 20,000 prediction logs...')

  const BATCH_SIZE = 500
  const TOTAL      = 20000
  const batches    = TOTAL / BATCH_SIZE

  // Fechas distribuidas en los últimos 90 días
  const now     = new Date()
  const past90d = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)

  for (let b = 0; b < batches; b++) {
    const batch = []

    for (let i = 0; i < BATCH_SIZE; i++) {
      const output = parseFloat((Math.random()).toFixed(4))
      const label  = output >= 0.5 ? 'aprobado' : 'rechazado'

      batch.push({
        log_id:            uuidv4(),
        modelo_id:         faker.number.int({ min: 1, max: 1000 }), // Referencia a MS2
        modelo_version:    `v${faker.number.int({min:1,max:3})}.${faker.number.int({min:0,max:9})}`,
        input_features:    generateFeatures(),
        prediccion_output: output,
        prediccion_label:  label,
        latencia_ms:       faker.number.int({ min: 10, max: 500 }),
        entorno:           'produccion',
        timestamp:         faker.date.between({ from: past90d, to: now })
      })
    }

    await PredictionLog.insertMany(batch)

    if ((b + 1) % 10 === 0) {
      console.log(`[seed] ${(b + 1) * BATCH_SIZE} logs insertados...`)
    }
  }

  // Generar 2,000 feedbacks (10% de los logs)
  console.log('[seed] Generando 2,000 feedbacks...')
  const logs = await PredictionLog.find({}).limit(2000).select('log_id prediccion_label')

  const feedbacks = logs.map(log => {
    const acerto      = Math.random() > 0.2 // 80% de acierto del modelo
    const realLabel   = acerto ? log.prediccion_label
                               : (log.prediccion_label === 'aprobado' ? 'rechazado' : 'aprobado')

    let feedbackTipo
    if (log.prediccion_label === 'aprobado' && realLabel === 'aprobado')   feedbackTipo = 'true_positive'
    if (log.prediccion_label === 'rechazado' && realLabel === 'rechazado') feedbackTipo = 'true_negative'
    if (log.prediccion_label === 'aprobado' && realLabel === 'rechazado')  feedbackTipo = 'false_positive'
    if (log.prediccion_label === 'rechazado' && realLabel === 'aprobado')  feedbackTipo = 'false_negative'

    const impacto = feedbackTipo === 'false_positive' ? -(Math.random() * 9000 + 1000)
                  : feedbackTipo === 'true_positive'  ?  (Math.random() * 5000 + 500)
                  : 0

    return {
      feedback_id:   uuidv4(),
      log_id:        log.log_id,
      analista_id:   `analista_${faker.number.int({ min: 1, max: 20 })}`,
      real_label:    realLabel,
      feedback_tipo: feedbackTipo,
      impacto_usd:   parseFloat(impacto.toFixed(2)),
      comentario:    faker.lorem.sentence(),
      timestamp:     new Date()
    }
  })

  await Feedback.insertMany(feedbacks)

  console.log('[seed]  Seed completo: 20,000 logs y 2,000 feedbacks.')
}

module.exports = { run }
