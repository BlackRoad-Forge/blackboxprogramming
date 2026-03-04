require('dotenv').config();

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const { config, validateConfig } = require('./config');
const { rawBodyCapture } = require('./middleware/webhook');
const routes = require('./routes');

const app = express();

// Security
app.use(helmet());
app.use(cors());

// Body parsing — raw body capture must come first for webhook verification
app.use(express.json({ verify: rawBodyCapture }));

// Routes
app.use('/api', routes);

// Root redirect
app.get('/', (_req, res) => {
  res.json({
    service: 'blackroad-stripe-service',
    docs: '/api/health',
    endpoints: [
      'POST /api/stripe/checkout/subscription',
      'POST /api/stripe/checkout/one-time',
      'POST /api/stripe/portal',
      'POST /api/stripe/customers',
      'GET  /api/stripe/customers/:id',
      'GET  /api/stripe/subscriptions/:id',
      'DELETE /api/stripe/subscriptions/:id',
      'POST /api/stripe/webhook',
      'GET  /api/health',
    ],
  });
});

// Only listen when not imported for testing
if (require.main === module) {
  const missing = validateConfig();
  if (missing.length > 0) {
    console.warn(`[warn] Missing env vars: ${missing.join(', ')} — running in degraded mode`);
  }
  app.listen(config.port, '0.0.0.0', () => {
    console.log(`[blackroad-stripe] listening on :${config.port} (${config.nodeEnv})`);
  });
}

module.exports = app;
