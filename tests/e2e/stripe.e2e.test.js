const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const {
  installStripeMock,
  startServer,
  stopServer,
  request,
} = require('./setup');

describe('Stripe API E2E', () => {
  let server, http;

  before(async () => {
    installStripeMock();
    const app = require('../../src/server');
    const ctx = await startServer(app);
    server = ctx.server;
    http = request(ctx.baseUrl);
  });

  after(async () => {
    await stopServer(server);
  });

  // -------- Checkout --------

  describe('POST /api/stripe/checkout/subscription', () => {
    it('creates a checkout session and returns url', async () => {
      const res = await http.post('/api/stripe/checkout/subscription', {
        body: { priceId: 'price_test_123' },
      });
      assert.equal(res.status, 200);
      assert.ok(res.body.sessionId);
      assert.ok(res.body.url);
    });

    it('returns 400 when priceId is missing', async () => {
      const res = await http.post('/api/stripe/checkout/subscription', {
        body: {},
      });
      assert.equal(res.status, 400);
      assert.equal(res.body.error, 'priceId is required');
    });
  });

  describe('POST /api/stripe/checkout/one-time', () => {
    it('creates a one-time checkout session', async () => {
      const res = await http.post('/api/stripe/checkout/one-time', {
        body: { priceId: 'price_onetime_456', quantity: 2 },
      });
      assert.equal(res.status, 200);
      assert.ok(res.body.sessionId);
      assert.ok(res.body.url);
    });

    it('returns 400 when priceId is missing', async () => {
      const res = await http.post('/api/stripe/checkout/one-time', {
        body: {},
      });
      assert.equal(res.status, 400);
    });
  });

  // -------- Customer portal --------

  describe('POST /api/stripe/portal', () => {
    it('creates a billing portal session', async () => {
      const res = await http.post('/api/stripe/portal', {
        body: { customerId: 'cus_test_abc' },
      });
      assert.equal(res.status, 200);
      assert.ok(res.body.url);
    });

    it('returns 400 when customerId is missing', async () => {
      const res = await http.post('/api/stripe/portal', { body: {} });
      assert.equal(res.status, 400);
      assert.equal(res.body.error, 'customerId is required');
    });
  });

  // -------- Customers --------

  describe('POST /api/stripe/customers', () => {
    it('creates a customer', async () => {
      const res = await http.post('/api/stripe/customers', {
        body: { email: 'test@blackroad.systems', name: 'Test' },
      });
      assert.equal(res.status, 201);
      assert.ok(res.body.id);
      assert.equal(res.body.email, 'test@blackroad.systems');
    });

    it('returns 400 when email is missing', async () => {
      const res = await http.post('/api/stripe/customers', {
        body: { name: 'No Email' },
      });
      assert.equal(res.status, 400);
    });
  });

  describe('GET /api/stripe/customers/:id', () => {
    it('retrieves a customer', async () => {
      const res = await http.get('/api/stripe/customers/cus_test_abc');
      assert.equal(res.status, 200);
      assert.equal(res.body.id, 'cus_test_abc');
    });
  });

  // -------- Subscriptions --------

  describe('GET /api/stripe/subscriptions/:id', () => {
    it('retrieves a subscription', async () => {
      const res = await http.get('/api/stripe/subscriptions/sub_test_123');
      assert.equal(res.status, 200);
      assert.equal(res.body.id, 'sub_test_123');
      assert.equal(res.body.status, 'active');
    });
  });

  describe('DELETE /api/stripe/subscriptions/:id', () => {
    it('cancels a subscription', async () => {
      const res = await http.del('/api/stripe/subscriptions/sub_test_123');
      assert.equal(res.status, 200);
      assert.equal(res.body.status, 'canceled');
    });
  });

  // -------- Webhook --------

  describe('POST /api/stripe/webhook', () => {
    it('processes a valid webhook event', async () => {
      const event = {
        type: 'checkout.session.completed',
        data: { object: { id: 'cs_test_webhook' } },
      };
      const res = await http.post('/api/stripe/webhook', {
        body: event,
        headers: { 'stripe-signature': 'valid_sig' },
      });
      assert.equal(res.status, 200);
      assert.equal(res.body.received, true);
    });

    it('rejects webhook with missing signature', async () => {
      const res = await http.post('/api/stripe/webhook', {
        body: { type: 'test' },
      });
      assert.equal(res.status, 400);
    });

    it('rejects webhook with invalid signature', async () => {
      const res = await http.post('/api/stripe/webhook', {
        body: { type: 'test' },
        headers: { 'stripe-signature': 'invalid' },
      });
      assert.equal(res.status, 400);
    });
  });
});
