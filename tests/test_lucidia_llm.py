"""Tests for the lightweight Ollama client."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import requests

from lucidia_llm import OllamaLLM


def test_generate_calls_ollama_correctly():
    client = OllamaLLM(model="test-model", base_url="http://example.com")
    mock_response = {"response": "Hello"}

    with patch("lucidia_llm.ollama.requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        result = client.generate("Hi")

        mock_post.assert_called_once_with(
            "http://example.com/api/generate",
            json={"model": "test-model", "prompt": "Hi", "stream": False},
            timeout=30.0,
        )
        assert result == "Hello"


def test_generate_includes_options_when_provided():
    client = OllamaLLM(model="test-model", base_url="http://example.com")
    mock_response = {"response": "Hi there"}

    with patch("lucidia_llm.ollama.requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        opts = {"temperature": 0.7}
        result = client.generate("Hi", options=opts)

        mock_post.assert_called_once_with(
            "http://example.com/api/generate",
            json={
                "model": "test-model",
                "prompt": "Hi",
                "stream": False,
                "options": opts,
            },
            timeout=30.0,
        )
        assert result == "Hi there"


def test_generate_handles_request_errors():
    client = OllamaLLM()

    with patch(
        "lucidia_llm.ollama.requests.post",
        side_effect=requests.RequestException("boom"),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            client.generate("Hi")
        assert "Ollama request failed" in str(exc_info.value)


def test_generate_handles_invalid_json():
    client = OllamaLLM()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.side_effect = ValueError("bad json")
    mock_resp.text = "bad json"

    with patch("lucidia_llm.ollama.requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            client.generate("Hello")
        message = str(exc_info.value)
        assert "could not be decoded" in message
        assert "bad json" in message


def test_generate_requires_response_field():
    client = OllamaLLM()
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {}

    with patch("lucidia_llm.ollama.requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            client.generate("Hello")
        assert "missing 'response'" in str(exc_info.value)


def test_generate_trims_trailing_slash_from_base_url():
    client = OllamaLLM(base_url="http://example.com/")
    mock_response = {"response": "Hello"}

    with patch("lucidia_llm.ollama.requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None

        result = client.generate("Hi")

        mock_post.assert_called_once_with(
            "http://example.com/api/generate",
            json={"model": "llama3", "prompt": "Hi", "stream": False},
            timeout=30.0,
        )
        assert result == "Hello"


def test_generate_truncates_long_invalid_json_response():
    client = OllamaLLM()

    long_text = "a" * 250

    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.side_effect = ValueError("bad json")
    mock_resp.text = long_text

    with patch("lucidia_llm.ollama.requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            client.generate("Hello")
        message = str(exc_info.value)
        assert long_text[:197] in message
        assert long_text not in message
        assert "..." in message


def test_base_url_assignment_normalizes_trailing_slash():
    client = OllamaLLM()

    client.base_url = "http://example.com/"

    assert client.base_url == "http://example.com"
