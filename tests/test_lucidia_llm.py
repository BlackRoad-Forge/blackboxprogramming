import pytest
from unittest.mock import patch

from lucidia_llm import OllamaLLM


def test_generate_calls_ollama_correctly():
    client = OllamaLLM(model="test-model", base_url="http://example.com")
    mock_response = {"response": "Hello"}

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        result = client.generate("Hi")

        mock_post.assert_called_once_with(
            "http://example.com/api/generate",
            json={"model": "test-model", "prompt": "Hi", "stream": False},
            timeout=30,
        )
        assert result == "Hello"


def test_generate_includes_options_when_provided():
    client = OllamaLLM(model="test-model", base_url="http://example.com")
    mock_response = {"response": "Hi there"}

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        opts = {"temperature": 0.7}
        result = client.generate("Hi", options=opts)

        mock_post.assert_called_once_with(
            "http://example.com/api/generate",
            json={"model": "test-model", "prompt": "Hi", "stream": False, "options": opts},
            timeout=30,
        )
        assert result == "Hi there"


def test_generate_handles_request_errors():
    client = OllamaLLM()
    import requests

    with patch("requests.post", side_effect=requests.RequestException("boom")):
        with pytest.raises(RuntimeError):
            client.generate("Hi")
