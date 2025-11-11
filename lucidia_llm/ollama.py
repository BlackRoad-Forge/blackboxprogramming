"""Lightweight client for Ollama's non-streaming text-generation endpoint."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import requests


class OllamaLLM:
    """Small helper class around the ``/api/generate`` Ollama endpoint."""

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

    # ------------------------------------------------------------------
    # Base URL normalisation
    # ------------------------------------------------------------------
    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._base_url = value.rstrip("/") if value else value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, prompt: str, options: Optional[Mapping[str, Any]] = None) -> str:
        """Generate text for *prompt* using the configured Ollama server."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = dict(options)

        url = f"{self.base_url}/api/generate"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - thin wrapper
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            body = getattr(response, "text", "")
            preview = body if len(body) <= 200 else f"{body[:197]}..."
            preview = preview or "<empty response>"
            raise RuntimeError(
                "Ollama response could not be decoded as JSON. "
                f"Raw response: {preview}"
            ) from exc

        if "response" not in data:
            raise RuntimeError("Invalid response from Ollama: missing 'response' field")

        return data["response"]


__all__ = ["OllamaLLM"]
