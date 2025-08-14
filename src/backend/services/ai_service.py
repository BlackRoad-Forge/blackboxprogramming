"""
AI service layer for Lucidia.

This module defines an abstract AIService interface and provider-specific
implementations for various AI backends such as OpenAI, Anthropic, and local
models. It includes intelligent routing, caching, rate limiting, and error
handling to make AI usage robust and cost-effective.

Note: Actual API keys and model names should be configured in ai_config.py
and environment variables. Provider implementations contain placeholder
calls that should be replaced with real API integrations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AIService(ABC):
    """Abstract base class for AI service providers."""

    @abstractmethod
    async def extract_facts(self, text: str) -> List[Any]:
        """Extract factual statements from the given text."""
        raise NotImplementedError

    @abstractmethod
    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        """Compute a semantic similarity score between two strings."""
        raise NotImplementedError

    @abstractmethod
    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        """Generate a sequence of reasoning steps to achieve a goal given context."""
        raise NotImplementedError

    @abstractmethod
    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        """Detect contradictions among a list of facts."""
        raise NotImplementedError

    @abstractmethod
    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        """Produce a natural language explanation for a conclusion given evidence."""
        raise NotImplementedError


class BaseProvider(AIService):
    """
    Provides common functionality for concrete providers including rate limiting
    and simple in-memory caching. Each provider should inherit from this class.
    """

    def __init__(self, rate_limit_per_minute: int = 60) -> None:
        self.rate_limit_per_minute = max(rate_limit_per_minute, 1)
        self._lock = asyncio.Lock()
        self._last_call: float = 0.0
        self._cache: Dict[str, Any] = {}

    async def _rate_limited(self) -> None:
        """Enforce a minimum interval between successive API calls."""
        async with self._lock:
            interval = 60.0 / self.rate_limit_per_minute
            now = time.time()
            wait = self._last_call + interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.time()

    def _cache_key(self, method: str, *args: Any, **kwargs: Any) -> str:
        return f"{method}:{args}:{tuple(sorted(kwargs.items()))}"

    async def _cached(self, method: str, func, *args: Any, **kwargs: Any):
        key = self._cache_key(method, *args, **kwargs)
        if key in self._cache:
            return self._cache[key]
        await self._rate_limited()
        result = await func(*args, **kwargs)
        self._cache[key] = result
        return result

    async def extract_facts(self, text: str) -> List[Any]:
        raise NotImplementedError

    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        raise NotImplementedError

    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        raise NotImplementedError

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        raise NotImplementedError

    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    """AI provider using OpenAI's API."""

    def __init__(self, api_key: str, models: Dict[str, str], rate_limit_per_minute: int = 60) -> None:
        super().__init__(rate_limit_per_minute)
        self.api_key = api_key
        self.models = models
        try:
            import openai  # type: ignore
            openai.api_key = api_key
            self._client = openai
        except ImportError:
            self._client = None
            logger.warning("openai package is not installed; OpenAIProvider will not function.")

    async def _call_chat(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 512) -> Any:
        if not self._client:
            raise RuntimeError("OpenAI client is not available.")
        return await asyncio.to_thread(
            self._client.ChatCompletion.create,
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )

    async def extract_facts(self, text: str) -> List[Any]:
        async def call():
            response = await self._call_chat(
                self.models.get("extraction", "gpt-3.5-turbo"),
                [
                    {"role": "system", "content": "Extract factual statements from the user's input."},
                    {"role": "user", "content": text},
                ],
            )
            return [choice["message"]["content"] for choice in response["choices"]]
        return await self._cached("extract_facts", call)

    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        async def call():
            if not self._client:
                raise RuntimeError("OpenAI client is not available.")
            model = self.models.get("embeddings", "text-embedding-3-large")
            res1 = await asyncio.to_thread(self._client.Embedding.create, model=model, input=text1)
            res2 = await asyncio.to_thread(self._client.Embedding.create, model=model, input=text2)
            emb1 = res1["data"][0]["embedding"]
            emb2 = res2["data"][0]["embedding"]
            import numpy as np  # type: ignore
            return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        return await self._cached("analyze_semantic_similarity", call)

    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        async def call():
            response = await self._call_chat(
                self.models.get("reasoning", "gpt-4"),
                [
                    {"role": "system", "content": "You are a chain-of-thought reasoning assistant."},
                    {"role": "user", "content": f"Goal: {goal}\nContext: {context}"},
                ],
            )
            return [choice["message"]["content"] for choice in response["choices"]]
        return await self._cached("generate_reasoning_steps", call)

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        async def call():
            response = await self._call_chat(
                self.models.get("analysis", "gpt-4"),
                [
                    {"role": "system", "content": "Identify contradictions among the provided statements."},
                    {"role": "user", "content": "\n".join(str(f) for f in facts)},
                ],
            )
            return [choice["message"]["content"] for choice in response["choices"]]
        return await self._cached("detect_contradictions", call)

    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        async def call():
            response = await self._call_chat(
                self.models.get("reasoning", "gpt-4"),
                [
                    {"role": "system", "content": "Explain the reasoning behind the conclusion."},
                    {"role": "user", "content": f"Conclusion: {conclusion}\nEvidence: {evidence}"},
                ],
            )
            return response["choices"][0]["message"]["content"]
        return await self._cached("explain_reasoning", call)


class AnthropicProvider(BaseProvider):
    """AI provider using Anthropic's Claude models."""

    def __init__(self, api_key: str, models: Dict[str, str], rate_limit_per_minute: int = 60) -> None:
        super().__init__(rate_limit_per_minute)
        self.api_key = api_key
        self.models = models
        try:
            import anthropic  # type: ignore
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            self._client = None
            logger.warning("anthropic package is not installed; AnthropicProvider will not function.")

    async def _call(self, model: str, prompt: str) -> Any:
        if not self._client:
            raise RuntimeError("Anthropic client is not available.")
        return await asyncio.to_thread(
            self._client.completions.create,
            model=model,
            prompt=prompt,
            max_tokens=512
        )

    async def extract_facts(self, text: str) -> List[Any]:
        async def call():
            prompt = f"Extract factual statements from the following text:\n\n{text}\n\nFacts:"
            response = await self._call(self.models.get("extraction", "claude-3-haiku-20240307"), prompt)
            return [response.completion.strip()]
        return await self._cached("extract_facts", call)

    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        raise NotImplementedError("Anthropic embeddings are not supported in this stub.")

    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        async def call():
            prompt = f"Generate reasoning steps to accomplish the goal: {goal}. Context: {context}"
            response = await self._call(self.models.get("reasoning", "claude-3-sonnet-20240229"), prompt)
            return [response.completion.strip()]
        return await self._cached("generate_reasoning_steps", call)

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        async def call():
            prompt = "Identify contradictions among the following statements:\n" + "\n".join(str(f) for f in facts)
            response = await self._call(self.models.get("analysis", "claude-3-sonnet-20240229"), prompt)
            return [response.completion.strip()]
        return await self._cached("detect_contradictions", call)

    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        async def call():
            prompt = f"Explain why {conclusion} given the following evidence: {evidence}"
            response = await self._call(self.models.get("reasoning", "claude-3-sonnet-20240229"), prompt)
            return response.completion.strip()
        return await self._cached("explain_reasoning", call)


class LocalProvider(BaseProvider):
    """Local provider using a self-hosted model through a REST API."""

    def __init__(self, base_url: str, models: Dict[str, str], rate_limit_per_minute: int = 60) -> None:
        super().__init__(rate_limit_per_minute)
        self.base_url = base_url.rstrip("/")
        self.models = models
        try:
            import httpx  # type: ignore
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        except ImportError:
            self._client = None
            logger.warning("httpx package is not installed; LocalProvider will not function.")

    async def _post(self, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("httpx client is not available.")
        response = await self._client.post(endpoint, json=json)
        response.raise_for_status()
        return response.json()

    async def extract_facts(self, text: str) -> List[Any]:
        async def call():
            payload = {"model": self.models.get("extraction"), "prompt": text}
            data = await self._post("/v1/generate", payload)
            return data.get("choices", [])
        return await self._cached("extract_facts", call)

    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        raise NotImplementedError("Local embeddings are not supported in this stub.")

    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        async def call():
            payload = {
                "model": self.models.get("reasoning"),
                "prompt": f"Goal: {goal}\nContext: {context}\nReasoning steps:",
            }
            data = await self._post("/v1/generate", payload)
            return data.get("choices", [])
        return await self._cached("generate_reasoning_steps", call)

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        async def call():
            payload = {
                "model": self.models.get("analysis"),
                "prompt": "Detect contradictions:\n" + "\n".join(str(f) for f in facts)
            }
            data = await self._post("/v1/generate", payload)
            return data.get("choices", [])
        return await self._cached("detect_contradictions", call)

    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        async def call():
            payload = {
                "model": self.models.get("reasoning"),
                "prompt": f"Explain why {conclusion} given {evidence}"
            }
            data = await self._post("/v1/generate", payload)
            choices = data.get("choices", [])
            return choices[0] if choices else ""
        return await self._cached("explain_reasoning", call)


class AIServiceRouter:
    """
    Orchestrates multiple AI providers and selects the most appropriate one for
    each task. If a provider fails, subsequent providers in the fallback list
    will be tried.
    """

    def __init__(
        self,
        providers: Dict[str, AIService],
        default_provider: str,
        fallback_order: Optional[List[str]] = None,
    ) -> None:
        self.providers = providers
        self.default_provider = default_provider
        self.fallback_order = fallback_order or []

    async def _call(self, method_name: str, *args: Any, **kwargs: Any):
        ordered = [self.default_provider] + [p for p in self.fallback_order if p != self.default_provider]
        for name in ordered:
            provider = self.providers.get(name)
            if not provider:
                continue
            method = getattr(provider, method_name, None)
            if not method:
                continue
            try:
                return await method(*args, **kwargs)
            except Exception as exc:
                logger.warning("Provider '%s' failed for %s: %s", name, method_name, exc)
                continue
        raise RuntimeError(f"All providers failed for {method_name}")

    async def extract_facts(self, text: str) -> List[Any]:
        return await self._call("extract_facts", text)

    async def analyze_semantic_similarity(self, text1: str, text2: str) -> float:
        return await self._call("analyze_semantic_similarity", text1, text2)

    async def generate_reasoning_steps(self, goal: str, context: Dict[str, Any]) -> List[str]:
        return await self._call("generate_reasoning_steps", goal, context)

    async def detect_contradictions(self, facts: List[Any]) -> List[Any]:
        return await self._call("detect_contradictions", facts)

    async def explain_reasoning(self, conclusion: str, evidence: List[Any]) -> str:
        return await self._call("explain_reasoning", conclusion, evidence)
