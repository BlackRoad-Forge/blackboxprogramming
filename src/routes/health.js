const { Router } = require('express');
const { config, validateConfig } = require('../config');

const router = Router();

router.get('/health', (_req, res) => {
  const missingEnv = validateConfig();
  const status = missingEnv.length === 0 ? 'healthy' : 'degraded';
  res.json({
    status,
    service: 'blackroad-stripe-service',
    version: '1.0.0',
    env: config.nodeEnv,
    timestamp: new Date().toISOString(),
    checks: {
      stripe: missingEnv.length === 0 ? 'configured' : 'missing keys',
    },
    ...(missingEnv.length > 0 && { missingEnv }),
  });
});

module.exports = router;
