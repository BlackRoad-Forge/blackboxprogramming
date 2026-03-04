const { env } = process;

const config = {
  port: parseInt(env.PORT || '3000', 10),
  nodeEnv: env.NODE_ENV || 'development',

  stripe: {
    secretKey: env.STRIPE_SECRET_KEY || '',
    webhookSecret: env.STRIPE_WEBHOOK_SECRET || '',
    publishableKey: env.STRIPE_PUBLISHABLE_KEY || '',
  },

  apiKey: env.API_KEY || '',

  urls: {
    base: env.BASE_URL || 'http://localhost:3000',
    success: env.SUCCESS_URL || 'http://localhost:3000/success',
    cancel: env.CANCEL_URL || 'http://localhost:3000/cancel',
  },

  pi: {
    hosts: [env.PI_HOST_1, env.PI_HOST_2].filter(Boolean),
    user: env.PI_USER || 'pi',
    deployPath: env.PI_DEPLOY_PATH || '/opt/blackroad/stripe-service',
  },
};

function validateConfig() {
  const missing = [];
  if (!config.stripe.secretKey) missing.push('STRIPE_SECRET_KEY');
  if (!config.stripe.webhookSecret) missing.push('STRIPE_WEBHOOK_SECRET');
  return missing;
}

module.exports = { config, validateConfig };
