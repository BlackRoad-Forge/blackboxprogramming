"""Lightweight LLM client for non-streaming text generation via Ollama's HTTP API."""

from __future__ import annotations

from typing import Any

import requests


class OllamaLLM:
    """Client for generating text using an Ollama server.

    Parameters
    ----------
    model:
        Name of the model loaded in the Ollama instance.
    base_url:
        Base URL of the Ollama server. Trailing slashes are stripped. Defaults to
        ``http://localhost:11434``.
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

    def generate(self, prompt: str, options: dict[str, Any] | None = None) -> str:
        """Generate a response from the model.

        Parameters
        ----------
        prompt:
            The prompt to send to the model.
        options:
            Optional generation parameters supported by Ollama. Defaults to ``None``.

        Returns
        -------
        str
            The generated text from the model.

        Raises
        ------
        RuntimeError
            If the request fails or the response cannot be decoded.
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
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError(f"Invalid response from Ollama: {exc}") from exc

        return data.get("response", "")
