const { Router } = require('express');
const stripeService = require('../services/stripe');
const { apiKeyAuth } = require('../middleware/auth');

const router = Router();

// -------- Checkout --------

router.post('/checkout/subscription', apiKeyAuth, async (req, res) => {
  try {
    const { priceId, customerId, metadata } = req.body;
    if (!priceId) return res.status(400).json({ error: 'priceId is required' });

    const session = await stripeService.createCheckoutSession({
      priceId,
      customerId,
      metadata,
    });
    return res.json({ sessionId: session.id, url: session.url });
  } catch (err) {
    console.error('[stripe] checkout/subscription error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

router.post('/checkout/one-time', apiKeyAuth, async (req, res) => {
  try {
    const { priceId, quantity, metadata } = req.body;
    if (!priceId) return res.status(400).json({ error: 'priceId is required' });

    const session = await stripeService.createOneTimeCheckout({
      priceId,
      quantity,
      metadata,
    });
    return res.json({ sessionId: session.id, url: session.url });
  } catch (err) {
    console.error('[stripe] checkout/one-time error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

// -------- Customer portal --------

router.post('/portal', apiKeyAuth, async (req, res) => {
  try {
    const { customerId } = req.body;
    if (!customerId)
      return res.status(400).json({ error: 'customerId is required' });

    const session = await stripeService.createPortalSession(customerId);
    return res.json({ url: session.url });
  } catch (err) {
    console.error('[stripe] portal error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

// -------- Customers --------

router.post('/customers', apiKeyAuth, async (req, res) => {
  try {
    const { email, name, metadata } = req.body;
    if (!email) return res.status(400).json({ error: 'email is required' });

    const customer = await stripeService.createCustomer({
      email,
      name,
      metadata,
    });
    return res.status(201).json(customer);
  } catch (err) {
    console.error('[stripe] create customer error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

router.get('/customers/:id', apiKeyAuth, async (req, res) => {
  try {
    const customer = await stripeService.getCustomer(req.params.id);
    return res.json(customer);
  } catch (err) {
    console.error('[stripe] get customer error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

// -------- Subscriptions --------

router.get('/subscriptions/:id', apiKeyAuth, async (req, res) => {
  try {
    const sub = await stripeService.getSubscription(req.params.id);
    return res.json(sub);
  } catch (err) {
    console.error('[stripe] get subscription error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

router.delete('/subscriptions/:id', apiKeyAuth, async (req, res) => {
  try {
    const sub = await stripeService.cancelSubscription(req.params.id);
    return res.json(sub);
  } catch (err) {
    console.error('[stripe] cancel subscription error:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

// -------- Webhook --------

router.post('/webhook', async (req, res) => {
  const sig = req.headers['stripe-signature'];
  if (!sig) return res.status(400).json({ error: 'Missing stripe-signature' });

  let event;
  try {
    event = stripeService.constructWebhookEvent(req.rawBody, sig);
  } catch (err) {
    console.error('[stripe] webhook signature verification failed:', err.message);
    return res.status(400).json({ error: `Webhook Error: ${err.message}` });
  }

  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;
      console.log(`[stripe] checkout completed: ${session.id}`);
      // TODO: fulfil order / activate subscription in your DB
      break;
    }
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object;
      console.log(`[stripe] subscription ${event.type}: ${sub.id} → ${sub.status}`);
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object;
      console.log(`[stripe] subscription cancelled: ${sub.id}`);
      break;
    }
    case 'invoice.payment_succeeded': {
      const invoice = event.data.object;
      console.log(`[stripe] invoice paid: ${invoice.id}`);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object;
      console.error(`[stripe] invoice payment failed: ${invoice.id}`);
      break;
    }
    default:
      console.log(`[stripe] unhandled event: ${event.type}`);
  }

  return res.json({ received: true });
});

module.exports = router;
