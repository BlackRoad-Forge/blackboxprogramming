/*
 * Lucidia Planner Service
 *
 * This service wraps the EnhancedPlannerAgent in a simple Express server so
 * that the FastAPI backend can forward questions for reasoning. When a
 * question is posted to /plan, the planner decomposes the question,
 * executes reasoning, and returns the full reasoning result. Any errors
 * during reasoning are caught and returned with an appropriate HTTP status.
 */

const express = require('express');
const bodyParser = require('body-parser');

// Import the EnhancedPlannerAgent from the shared blackboxprogramming module.
const { EnhancedPlannerAgent } = require('../blackboxprogramming/EnhancedPlannerAgent.js');

// Instantiate the planner agent. You can pass configuration options here if needed.
const plannerAgent = new EnhancedPlannerAgent();

plannerAgent.on('planner-started', ({ agentId }) => {
  console.log(`🔧 Lucidia Planner service started with agent ID: ${agentId}`);
});

// Create the Express application and configure middleware
const app = express();
app.use(bodyParser.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Endpoint for processing reasoning requests. Expects a JSON body with a
// "question" property. Returns the full reasoning result from the agent.
app.post('/plan', async (req, res) => {
  const { question, context } = req.body || {};
  if (!question || typeof question !== 'string') {
    return res.status(400).json({ error: 'Invalid request', message: 'A "question" field is required.' });
  }
  try {
    // Call the agent's reason method and await the result
    const result = await plannerAgent.reason(question, context || {});
    res.json(result);
  } catch (error) {
    console.error('Planner reasoning error:', error);
    res.status(500).json({ error: 'Reasoning error', message: error.message });
  }
});

// Start listening on port 3000. This port is exposed internally within the
// Docker network and can be reached by other services via http://planner:3000.
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`📡 Planner service listening on port ${PORT}`);
});
