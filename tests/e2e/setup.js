/**
 * E2E test helpers — shared setup for the test suite.
 *
 * Provides a lightweight supertest wrapper around the Express app,
 * and stubs the Stripe SDK so tests run without real API keys.
 */

const http = require('http');
const { setStripe } = require('../../src/services/stripe');

// ---- Stripe mock ----

function makeFakeSession(overrides = {}) {
  return {
    id: 'cs_test_' + Math.random().toString(36).slice(2, 10),
    url: 'https://checkout.stripe.com/fake',
    ...overrides,
  };
}

function createStripeMock() {
  return {
    checkout: {
      sessions: {
        create: async (params) => makeFakeSession({ params }),
      },
    },
    billingPortal: {
      sessions: {
        create: async (params) => ({
          url: 'https://billing.stripe.com/fake-portal',
          ...params,
        }),
      },
    },
    customers: {
      create: async (params) => ({
        id: 'cus_test_' + Math.random().toString(36).slice(2, 10),
        ...params,
      }),
      retrieve: async (id) => ({
        id,
        email: 'test@blackroad.systems',
        name: 'Test Customer',
      }),
    },
    subscriptions: {
      retrieve: async (id) => ({
        id,
        status: 'active',
        current_period_end: Math.floor(Date.now() / 1000) + 86400 * 30,
      }),
      cancel: async (id) => ({
        id,
        status: 'canceled',
      }),
    },
    webhooks: {
      constructEvent: (body, sig, secret) => {
        if (sig === 'invalid') throw new Error('Invalid signature');
        const parsed = typeof body === 'string' ? JSON.parse(body) : JSON.parse(body.toString());
        return parsed;
      },
    },
  };
}

// ---- Server helpers ----

function startServer(app) {
  return new Promise((resolve) => {
    const server = http.createServer(app);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, port, baseUrl: `http://127.0.0.1:${port}` });
    });
  });
}

function stopServer(server) {
  return new Promise((resolve) => server.close(resolve));
}

// Simple HTTP helper (no external deps)
function request(baseUrl) {
  // Auto-attach API key from env so authenticated endpoints pass in tests
  const apiKey = process.env.API_KEY || '';

  async function send(method, path, { body, headers = {} } = {}) {
    const url = new URL(path, baseUrl);
    const payload = body ? JSON.stringify(body) : undefined;
    const opts = {
      method,
      headers: {
        'content-type': 'application/json',
        ...(apiKey && { 'x-api-key': apiKey }),
        ...headers,
      },
    };

    return new Promise((resolve, reject) => {
      const req = http.request(url, opts, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(data), headers: res.headers });
          } catch {
            resolve({ status: res.statusCode, body: data, headers: res.headers });
          }
        });
      });
      req.on('error', reject);
      if (payload) req.write(payload);
      req.end();
    });
  }

  return {
    get: (path, opts) => send('GET', path, opts),
    post: (path, opts) => send('POST', path, opts),
    del: (path, opts) => send('DELETE', path, opts),
  };
}

function installStripeMock() {
  const mock = createStripeMock();
  setStripe(mock);
  return mock;
}

module.exports = {
  createStripeMock,
  installStripeMock,
  startServer,
  stopServer,
  request,
};
