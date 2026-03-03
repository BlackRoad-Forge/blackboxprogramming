/**
 * Tests for the Ollama Extension server.
 *
 * Run with:  node --test src/tests/index.test.js
 */

'use strict';

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');

// ---- Minimal HTTP helpers (no external test runner needed) ----------------

const http = require('node:http');

function request(options, body) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// ---- Start the server on an ephemeral port --------------------------------

let server;
let port;

before(async () => {
  // Point at a non-existent Ollama so we can test error paths without a real instance
  process.env.OLLAMA_BASE_URL = 'http://127.0.0.1:1'; // guaranteed to refuse connection
  process.env.OLLAMA_MODEL = 'test-model';
  process.env.PORT = '0'; // OS picks a free port

  // Import after env vars are set
  server = require('../index.js');

  await new Promise((resolve) => {
    server.on('listening', () => {
      port = server.address().port;
      resolve();
    });
    // app.listen returns the http.Server; if it's already listening resolve immediately
    if (server.listening) {
      port = server.address().port;
      resolve();
    }
  });
});

after(() => {
  server.close();
});

// ---- Tests ----------------------------------------------------------------

describe('GET /api/health', () => {
  it('returns 200 with provider=ollama', async () => {
    const res = await request({ host: '127.0.0.1', port, path: '/api/health', method: 'GET' });
    assert.equal(res.status, 200);
    const body = JSON.parse(res.body);
    assert.equal(body.status, 'ok');
    assert.equal(body.provider, 'ollama');
    assert.equal(body.model, 'test-model');
  });
});

describe('POST /', () => {
  it('returns SSE content-type and [DONE] sentinel even when Ollama is unreachable', async () => {
    const res = await request(
      {
        host: '127.0.0.1',
        port,
        path: '/',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      },
      { messages: [{ role: 'user', content: 'Hello from the test' }] }
    );

    assert.equal(res.status, 200);
    assert.match(res.headers['content-type'], /text\/event-stream/);
    assert.ok(res.body.includes('data: [DONE]'), 'SSE stream must end with [DONE]');
    // Error message should mention Ollama
    assert.ok(
      res.body.toLowerCase().includes('ollama'),
      'Error message should reference Ollama'
    );
  });

  it('handles missing messages gracefully', async () => {
    const res = await request(
      {
        host: '127.0.0.1',
        port,
        path: '/',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      },
      {} // no messages key
    );

    assert.equal(res.status, 200);
    assert.ok(res.body.includes('data: [DONE]'));
  });
});
