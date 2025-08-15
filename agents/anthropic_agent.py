"""
Client for interacting with Anthropic's Claude API.

This module provides a simple wrapper around the Anthropic API. It reads the
API key from the environment variable ``CLAUDE_API_KEY`` and exposes a
``claude_chat`` function that submits a prompt to the service and returns
the generated completion. In a production deployment you should update the
endpoint URL, payload structure, and response parsing to match the latest
Anthropic API specification.

Example usage::

    from agents.anthropic_agent import claude_chat
    response = claude_chat("Tell me a joke about penguins.")
    print(response)

"""
import os
import requests
from typing import Optional

# Retrieve the API key from the environment. If this is not set, the client
# will raise a runtime error when used.
CLAUDE_API_KEY: Optional[str] = os.getenv("CLAUDE_API_KEY")


def claude_chat(prompt: str, model: str = "claude-3-opus-20240229", max_tokens: int = 1024) -> str:
    """Send a prompt to Claude and return the generated completion.

    :param prompt: The prompt text to send to the model.
    :param model: The model identifier to use; defaults to Claude 3 Opus.
    :param max_tokens: The maximum number of tokens to generate.
    :returns: The completion text from the model response.
    :raises RuntimeError: If the API key is not configured.
    :raises requests.HTTPError: If the HTTP request fails.
    """
    if not CLAUDE_API_KEY:
        raise RuntimeError(
            "CLAUDE_API_KEY environment variable is not set. "
            "Please configure your API key in the .env file or environment."
        )

    # Assemble the request payload. Adjust this according to the official API specification.
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {CLAUDE_API_KEY}",
        "Content-Type": "application/json",
    }

    # NOTE: Replace this URL with the official Anthropic API endpoint when deploying.
    endpoint = "https://api.anthropic.com/v1/complete"

    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Anthropic's API typically returns a field like ``completion`` or ``text``. Adjust accordingly.
    return data.get("completion") or data.get("text", "")
