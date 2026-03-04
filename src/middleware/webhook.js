/**
 * Express middleware that captures the raw body for Stripe webhook
 * signature verification. Must be applied BEFORE express.json().
 */
function rawBodyCapture(req, res, buf) {
  if (req.originalUrl === '/api/stripe/webhook') {
    req.rawBody = buf;
  }
}

module.exports = { rawBodyCapture };
