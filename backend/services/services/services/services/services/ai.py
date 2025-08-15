"""
AI service utilities for Lucidia.

This module encapsulates calls to large language models (LLMs), embeddings
generation, simple fact extraction, contradiction detection and
explanation generation. The functions in this module attempt to call
OpenAI's REST APIs directly via HTTP when an API key is provided via
environment variable (``OPENAI_API_KEY``). If the API call fails for any
reason (e.g., missing key, network issues), sensible fallbacks are used
to ensure the rest of the system continues functioning.

These utilities are designed to be imported by the FastAPI backend and
other modules. They do not maintain any global state.
"""

from __future__ import annotations

import os
import hashlib
import json
from typing import Dict, Any, List, Optional

import requests

# ---------------------------------------------------------------------------
# Core LLM calls

def call_openai(prompt: str, *, model: Optional[str] = None, max_tokens: int = 256, temperature: float = 0.7) -> str:
    """Call the OpenAI chat/completions API with a given prompt.

    Args:
        prompt: The prompt to send to the model.
        model: Which OpenAI model to use (defaults to ``gpt-3.5-turbo``).
        max_tokens: The maximum number of tokens to generate in the response.
        temperature: Sampling temperature for the generation.

    Returns:
        The model's response as a string. If the API call cannot be made
        (due to missing API key, lack of network connectivity, or any
        exception), a fallback response is returned prefixed with an
        explanatory tag.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # No API key provided – fall back to a deterministic stub.
        return f"[AI unavailable] {prompt}"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices")
            if choices:
                return choices[0]["message"]["content"].strip()
            return "[AI: no choices returned]"
        else:
            return f"[AI error {resp.status_code}] {prompt}"
    except Exception:
        return f"[AI call failed] {prompt}"


def call_openai_embeddings(text: str, *, model: Optional[str] = None) -> List[float]:
    """Generate an embedding for the given text using OpenAI's embeddings API.

    Args:
        text: Input string to embed.
        model: Which embeddings model to use (defaults to ``text-embedding-ada-002``).

    Returns:
        A list of floats representing the embedding. If the API call cannot
        be made, a fallback embedding based on a simple hash of the text is
        returned.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: derive a pseudo-embedding from the MD5 hash of the text
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        # Convert the hex digest into a list of floats between 0 and 1
        return [(int(digest[i:i+2], 16) / 255.0) for i in range(0, min(len(digest), 32), 2)]
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "text-embedding-ada-002",
        "input": text,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            embed_list = data.get("data")
            if embed_list:
                return embed_list[0].get("embedding", [])
            return []
        else:
            # Unexpected status – fall back to hash-based embedding
            digest = hashlib.md5(text.encode("utf-8")).hexdigest()
            return [(int(digest[i:i+2], 16) / 255.0) for i in range(0, min(len(digest), 32), 2)]
    except Exception:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        return [(int(digest[i:i+2], 16) / 255.0) for i in range(0, min(len(digest), 32), 2)]


# ---------------------------------------------------------------------------
# Fact extraction and contradiction detection

def extract_facts(text: str) -> List[Dict[str, Any]]:
    """Extract simple facts from a text.

    This function tokenizes the text into sentences and wraps each
    sentence in a dictionary structure. A more sophisticated NLP pipeline
    could be substituted here when additional libraries and models are
    available.

    Args:
        text: The raw text from which to extract facts.

    Returns:
        A list of dictionaries, each representing a fact with its text and
        a default confidence.
    """
    # Split on periods, question marks, and exclamation marks
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    facts: List[Dict[str, Any]] = []
    for s in sentences:
        facts.append({
            "content": s,
            "confidence": 1.0,
        })
    return facts


def detect_contradictions(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect potential contradictions among a list of facts.

    A simple heuristic flags a pair of facts as contradictory if they
    contain the exact same subject (first word) and one contains a
    negation ("not", "no", "never") while the other does not. This
    implementation is deliberately rudimentary; in production a more
    sophisticated semantic analysis would be required.

    Args:
        facts: A list of fact dictionaries containing at least the
            ``content`` key.

    Returns:
        A list of dictionaries describing contradictions. Each entry
        contains the indices of the contradicting facts and a description.
    """
    contradictions: List[Dict[str, Any]] = []
    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            a = facts[i]["content"].lower()
            b = facts[j]["content"].lower()
            # Extract the first word as a proxy for the subject
            subj_a = a.split()[0] if a.split() else ""
            subj_b = b.split()[0] if b.split() else ""
            if subj_a and subj_a == subj_b:
                neg_a = any(w in a for w in [" not ", " no ", " never "])
                neg_b = any(w in b for w in [" not ", " no ", " never "])
                if neg_a != neg_b:
                    contradictions.append({
                        "facts": (i, j),
                        "description": f"Potential contradiction between fact {i} and {j} about '{subj_a}'",
                    })
    return contradictions


# ---------------------------------------------------------------------------
# Explanation generation

def generate_explanation(reasoning_tree: Dict[str, Any]) -> str:
    """Generate a natural language explanation from a reasoning tree.

    The explanation attempts to summarize the steps of reasoning and the
    final conclusion. If an LLM is available, this function will call
    ``call_openai`` with a prompt that instructs the model to produce
    a human-friendly explanation. Otherwise, it falls back to a simple
    concatenation of the answer and the strategy name.

    Args:
        reasoning_tree: A dictionary representing the reasoning tree as
            returned by the planner.

    Returns:
        A string explanation.
    """
    # Build a textual summary of the tree structure
    summary_parts = []
    strategy = reasoning_tree.get("strategy", "unknown strategy")
    conclusion = reasoning_tree.get("answer") or reasoning_tree.get("conclusion", {}).get("answer")
    if conclusion:
        summary_parts.append(f"The system concluded: {conclusion}.")
    nodes = reasoning_tree.get("nodes")
    if nodes:
        summary_parts.append(f"It used {len(nodes)} intermediate sub-questions to arrive at this conclusion.")
    summary_parts.append(f"Strategy employed: {strategy}.")
    base_summary = " ".join(summary_parts)
    # If an API key is configured, ask the model to rewrite the summary
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        prompt = ("Explain the following reasoning process in clear, plain language "
                  "suitable for a non-expert audience. Include the main conclusion "
                  "and how the sub-questions contributed to the answer:\n\n"
                  f"Reasoning summary: {base_summary}")
        explanation = call_openai(prompt, model="gpt-3.5-turbo", max_tokens=200, temperature=0.5)
        return explanation
    else:
        return base_summary
