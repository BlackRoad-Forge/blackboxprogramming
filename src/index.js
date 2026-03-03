/**
 * Blackboxprogramming Ollama Extension
 *
 * GitHub Copilot Extension Agent that routes ALL requests for
 * @copilot, @lucidia, and @blackboxprogramming directly to a
 * local Ollama instance — no cloud AI providers involved.
 *
 * GitHub Copilot Extension Agent API reference:
 * https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension
 */

'use strict';

const express = require('express');

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// Configuration (set via environment variables; see .env.example)
// ---------------------------------------------------------------------------
const PORT = process.env.PORT || 3000;
const OLLAMA_BASE_URL = (process.env.OLLAMA_BASE_URL || 'http://localhost:11434').replace(/\/$/, '');
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'llama3';

// ---------------------------------------------------------------------------
// Health endpoint — used by the existing auto-deploy / self-healing workflows
// ---------------------------------------------------------------------------
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', provider: 'ollama', model: OLLAMA_MODEL, base_url: OLLAMA_BASE_URL });
});

// ---------------------------------------------------------------------------
// GitHub Copilot Extension Agent endpoint
//
// GitHub sends a POST to the root path "/" with the conversation payload.
// We forward the messages to Ollama and stream the response back in the
// Server-Sent Events (SSE) format expected by GitHub Copilot.
// ---------------------------------------------------------------------------
app.post('/', async (req, res) => {
  // GitHub sends a token we can optionally verify.  We accept the request
  // regardless so the extension works even in self-hosted / air-gapped setups.
  const messages = Array.isArray(req.body?.messages) ? req.body.messages : [];

  // Strip any GitHub-injected system messages that reference cloud providers
  // and build a clean messages array for Ollama.
  const ollamaMessages = messages
    .filter((m) => m && m.role && m.content)
    .map((m) => ({ role: m.role, content: m.content }));

  // Set up SSE response headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  try {
    const ollamaRes = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: OLLAMA_MODEL, messages: ollamaMessages, stream: true }),
    });

    if (!ollamaRes.ok) {
      const errText = await ollamaRes.text();
      sendSSEError(res, `Ollama error ${ollamaRes.status}: ${errText}`);
      return;
    }

    // Stream Ollama response chunks → GitHub Copilot SSE format
    const reader = ollamaRes.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      // Ollama streams newline-delimited JSON objects
      for (const line of chunk.split('\n')) {
        if (!line.trim()) continue;
        try {
          const parsed = JSON.parse(line);
          const content = parsed?.message?.content ?? '';
          const finishReason = parsed?.done ? 'stop' : null;

          // GitHub Copilot SSE format (OpenAI-compatible delta)
          const ssePayload = JSON.stringify({
            choices: [
              {
                delta: { role: 'assistant', content },
                finish_reason: finishReason,
              },
            ],
          });
          res.write(`data: ${ssePayload}\n\n`);
        } catch {
          // Ignore non-JSON lines from Ollama
        }
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();
  } catch (err) {
    sendSSEError(res, `Failed to reach Ollama at ${OLLAMA_BASE_URL}: ${err.message}`);
  }
});

// ---------------------------------------------------------------------------
// Helper: send an error as an SSE message so Copilot Chat displays it
// ---------------------------------------------------------------------------
function sendSSEError(res, message) {
  const payload = JSON.stringify({
    choices: [
      {
        delta: { role: 'assistant', content: `⚠️ ${message}` },
        finish_reason: 'stop',
      },
    ],
  });
  res.write(`data: ${payload}\n\n`);
  res.write('data: [DONE]\n\n');
  res.end();
}

// ---------------------------------------------------------------------------
// Start server
// ---------------------------------------------------------------------------
const server = app.listen(PORT, () => {
  console.log(`🦙 Ollama Extension listening on port ${PORT}`);
  console.log(`   Model  : ${OLLAMA_MODEL}`);
  console.log(`   Ollama : ${OLLAMA_BASE_URL}`);
  console.log(`   Handles: @copilot  @lucidia  @blackboxprogramming`);
});

module.exports = server; // exported for testing
