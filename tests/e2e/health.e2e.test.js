const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { startServer, stopServer, request } = require('./setup');

describe('Health endpoint E2E', () => {
  let server, http;

  before(async () => {
    const app = require('../../src/server');
    const ctx = await startServer(app);
    server = ctx.server;
    http = request(ctx.baseUrl);
  });

  after(async () => {
    await stopServer(server);
  });

  it('GET /api/health returns 200 with status field', async () => {
    const res = await http.get('/api/health');
    assert.equal(res.status, 200);
    assert.ok(res.body.status);
    assert.equal(res.body.service, 'blackroad-stripe-service');
    assert.ok(res.body.timestamp);
  });

  it('GET / returns service info with endpoint list', async () => {
    const res = await http.get('/');
    assert.equal(res.status, 200);
    assert.equal(res.body.service, 'blackroad-stripe-service');
    assert.ok(Array.isArray(res.body.endpoints));
    assert.ok(res.body.endpoints.length > 0);
  });
});
