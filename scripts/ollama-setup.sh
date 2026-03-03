#!/usr/bin/env bash
# scripts/ollama-setup.sh
# Install Ollama locally (no Docker needed) and pull a default model.
# Usage: bash scripts/ollama-setup.sh [model]
# Example: bash scripts/ollama-setup.sh llama3.2

set -euo pipefail

MODEL="${1:-${OLLAMA_DEFAULT_MODEL:-llama3.2}}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

# ── Install ────────────────────────────────────────────────────────────────────
if command -v ollama &>/dev/null; then
  echo "✅ Ollama already installed: $(ollama --version)"
else
  echo "📦 Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
  echo "✅ Ollama installed."
fi

# ── Start daemon (if not running) ─────────────────────────────────────────────
if curl -sf "${OLLAMA_HOST}/api/tags" &>/dev/null; then
  echo "✅ Ollama daemon already running at ${OLLAMA_HOST}"
else
  echo "🚀 Starting Ollama daemon..."
  ollama serve &
  OLLAMA_READY=0
  for attempt in $(seq 1 15); do
    if curl -sf "${OLLAMA_HOST}/api/tags" &>/dev/null; then
      echo "✅ Ollama daemon ready."
      OLLAMA_READY=1
      break
    fi
    sleep 2
  done
  if [ "${OLLAMA_READY}" -eq 0 ]; then
    echo "❌ Ollama daemon did not start within 30 seconds." >&2
    exit 1
  fi
fi

# ── Pull model ─────────────────────────────────────────────────────────────────
echo "⬇️  Pulling model: ${MODEL}"
ollama pull "${MODEL}"
echo ""
echo "✅ Done! Ollama is running locally at ${OLLAMA_HOST}"
echo ""
echo "Try it:"
echo "  ollama run ${MODEL}"
echo "  curl ${OLLAMA_HOST}/api/generate -d '{\"model\":\"${MODEL}\",\"prompt\":\"Hello!\",\"stream\":false}'"
