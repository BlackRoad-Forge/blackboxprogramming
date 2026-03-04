const { config } = require('../config');

let stripe;

function getStripe() {
  if (!stripe) {
    const Stripe = require('stripe');
    stripe = new Stripe(config.stripe.secretKey, {
      apiVersion: '2024-04-10',
      appInfo: {
        name: 'blackroad-stripe-service',
        version: '1.0.0',
      },
    });
  }
  return stripe;
}

/** Override the stripe instance (for testing). */
function setStripe(instance) {
  stripe = instance;
}

// --------------- Checkout ---------------

async function createCheckoutSession({ priceId, customerId, metadata }) {
  const s = getStripe();
  const params = {
    mode: 'subscription',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${config.urls.success}?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: config.urls.cancel,
    metadata: metadata || {},
  };
  if (customerId) params.customer = customerId;
  return s.checkout.sessions.create(params);
}

async function createOneTimeCheckout({ priceId, quantity, metadata }) {
  const s = getStripe();
  return s.checkout.sessions.create({
    mode: 'payment',
    line_items: [{ price: priceId, quantity: quantity || 1 }],
    success_url: `${config.urls.success}?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: config.urls.cancel,
    metadata: metadata || {},
  });
}

// --------------- Customer portal ---------------

async function createPortalSession(customerId) {
  const s = getStripe();
  return s.billingPortal.sessions.create({
    customer: customerId,
    return_url: config.urls.base,
  });
}

// --------------- Subscriptions ---------------

async function getSubscription(subscriptionId) {
  return getStripe().subscriptions.retrieve(subscriptionId);
}

async function cancelSubscription(subscriptionId) {
  return getStripe().subscriptions.cancel(subscriptionId);
}

// --------------- Customers ---------------

async function createCustomer({ email, name, metadata }) {
  return getStripe().customers.create({ email, name, metadata });
}

async function getCustomer(customerId) {
  return getStripe().customers.retrieve(customerId);
}

// --------------- Webhooks ---------------

function constructWebhookEvent(body, signature) {
  return getStripe().webhooks.constructEvent(
    body,
    signature,
    config.stripe.webhookSecret
  );
}

module.exports = {
  getStripe,
  setStripe,
  createCheckoutSession,
  createOneTimeCheckout,
  createPortalSession,
  getSubscription,
  cancelSubscription,
  createCustomer,
  getCustomer,
  constructWebhookEvent,
};
