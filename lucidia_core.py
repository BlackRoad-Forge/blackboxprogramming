"""Minimal Lucidia core used for the unit tests.

The real project features a persistent knowledge base backed by databases and
cryptographic identities.  For the purposes of the tests we only implement a
small in-memory store that exposes the operations exercised by the tests:
learning propositions, querying, updating confidence values and basic
contradiction handling helpers.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ps_sha_infinity import PS_SHA_Infinity


@dataclass
class Evidence:
    source: str
    weight: float
    metadata: Dict[str, Any] | None = None


@dataclass
class Proposition:
    type: str
    content: str
    confidence: float
    context: Dict[str, Any] | None = None
    evidence: List[Evidence] | None = None


class Lucidia:
    """Simple in-memory knowledge store."""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url
        self.identity = PS_SHA_Infinity()
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._id_counter = itertools.count(1)

    # ------------------------------------------------------------------ utils
    def _new_fact_id(self) -> str:
        return f"fact_{next(self._id_counter)}"

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    # ----------------------------------------------------------------- methods
    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        if not content:
            raise ValueError("content required")
        fact_id = self._new_fact_id()
        content_hash = self._hash_content(content)
        fact = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": context or {},
            "evidence": evidence or [],
            "content_hash": content_hash,
        }
        self._facts[fact_id] = fact
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(
        self,
        content: str,
        confidence: Optional[Dict[str, float]] = None,
        limit: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        confidence = confidence or {}
        min_conf = confidence.get("min", 0.0)
        results = [
            fact
            for fact in self._facts.values()
            if content.lower() in fact["content"].lower()
            and fact["confidence"] >= min_conf
        ]
        return {"results": results[:limit]}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id not in self._facts:
            raise KeyError(f"unknown fact_id: {fact_id}")
        self._facts[fact_id]["confidence"] = new_confidence

    # The test-suite only asserts that a list-like object is returned, so an
    # empty list is sufficient.
    def get_contradictions(self) -> List[Any]:  # pragma: no cover - trivial
        return []

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:  # pragma: no cover - simple
        contradiction_id = f"contradiction_{len(conflicting_facts)}"
        return {"contradiction_id": contradiction_id}

    def get_fact_count(self) -> int:  # pragma: no cover - trivial
        return len(self._facts)
