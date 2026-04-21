const mongoose = require('mongoose')

const connect = async () => {
  const host     = process.env.MONGO_HOST
  const port     = process.env.MONGO_PORT || '27017'
  const user     = process.env.MONGO_USER
  const password = process.env.MONGO_PASSWORD
  const db       = process.env.MONGO_DB

  const uri = `mongodb://${user}:${password}@${host}:${port}/${db}?authSource=admin`

  try {
    await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 10000,
      maxPoolSize: 10
    })
    console.log('[database] Conexión a MongoDB establecida')
  } catch (error) {
    console.error('[database] Error conectando a MongoDB:', error.message)
    process.exit(1)
  }
}

module.exports = { connect }
