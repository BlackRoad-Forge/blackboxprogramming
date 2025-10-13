"""Lightweight helper for Ollama's non-streaming text generation HTTP API."""
"""Helpers for Ollama's non-streaming text-generation HTTP endpoint.

The module exposes :class:`OllamaLLM`, a tiny façade over the
``POST /api/generate`` route that Lucidia hits for synchronous completions.
It keeps the public surface tight while still surfacing the configuration
callers routinely need to control, such as model selection, server URL,
request timeout and optional generation tweaks passed through ``options``.
"""
"""Lightweight client for non-streaming text generation via Ollama's HTTP API."""
"""Lightweight LLM client for non-streaming text generation via Ollama's HTTP API."""

from __future__ import annotations

from typing import Any, Mapping

import requests
from json import JSONDecodeError
from typing import Any, Dict, Optional

import requests


class OllamaLLM:
    """Small helper for text generation against an Ollama server.

    Parameters
    ----------
    model:
        Name of the model loaded in the Ollama instance.
    base_url:
        Base URL of the Ollama server. Trailing slashes are stripped on
        assignment to ensure consistent endpoint construction. Defaults to
        ``http://localhost:11434``.
    timeout:
        Request timeout in seconds. Defaults to ``30.0`` seconds.
    """

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: float = 30.0,
    ) -> None:
        self.model = model
        self._base_url = ""
        self.base_url = base_url
        self.timeout = timeout

    def generate(
        self, prompt: str, options: Mapping[str, Any] | None = None
    ) -> str:
    @property
    def base_url(self) -> str:
        """Return the normalized Ollama base URL."""

        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        """Normalize and store the Ollama base URL."""

        self._base_url = value.rstrip("/")

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
            If the request fails or the response cannot be decoded. When JSON
            decoding fails, the error message includes a truncated preview of
            the raw response body to aid debugging.
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if options is not None:
            payload["options"] = dict(options)
        url = f"{self.base_url}/api/generate"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except ValueError as exc:
            body = getattr(response, "text", "<unavailable>")
            raise RuntimeError(
                f"Invalid response from Ollama: {exc}. Response body: {body}"
            ) from exc

        try:
            return data["response"]
        except KeyError as exc:
            raise RuntimeError(
                "Invalid response from Ollama: missing 'response' field"
            ) from exc
            data = response.json()
        except (ValueError, JSONDecodeError) as exc:
            response_preview = getattr(response, "text", "")
            if len(response_preview) > 200:
                response_preview = f"{response_preview[:197]}..."
            raise RuntimeError(
                "Ollama response could not be decoded as JSON. "
                f"Raw response: {response_preview or '<empty response>'}"
            ) from exc

        try:
            data = response.json()
        except (ValueError, JSONDecodeError) as exc:
            raise RuntimeError("Ollama response could not be decoded as JSON") from exc

        return data.get("response", "")
