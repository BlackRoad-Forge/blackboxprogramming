const { config } = require('../config');

/**
 * Simple API-key auth for internal endpoints.
 * Skipped when API_KEY is not set (dev mode).
 */
function apiKeyAuth(req, res, next) {
  if (!config.apiKey) return next(); // no key configured → open
  const provided = req.headers['x-api-key'] || req.query.api_key;
  if (provided === config.apiKey) return next();
  return res.status(401).json({ error: 'Unauthorized' });
}

module.exports = { apiKeyAuth };
