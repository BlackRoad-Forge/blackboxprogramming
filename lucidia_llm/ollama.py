"""Lightweight interface for interacting with LLM backends.

Currently supports [Ollama](https://ollama.ai) through its HTTP API.
The interface is intentionally small to provide a simple entry point for
experimentation within the Lucidia project.
"""

from __future__ import annotations

import requests
from typing import Any, Dict, Optional


class OllamaLLM:
    """Client for generating text using an Ollama server.

    Parameters
    ----------
    model:
        Name of the model loaded in the Ollama instance.
    base_url:
        Base URL of the Ollama server. Defaults to ``http://localhost:11434``.
    timeout:
        Request timeout in seconds. Defaults to ``30`` seconds.
    """

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 30,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response from the model.

        Parameters
        ----------
        prompt:
            The prompt to send to the model.
        options:
            Optional generation parameters supported by Ollama.

        Returns
        -------
        str
            The generated text from the model.
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if options is not None:
            payload["options"] = options
        url = f"{self.base_url}/api/generate"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        return data.get("response", "")
