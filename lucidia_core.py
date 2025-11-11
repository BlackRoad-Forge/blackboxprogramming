"""Minimal in-memory implementation of the Lucidia core used in tests."""

from __future__ import annotations

import hashlib
import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ps_sha_infinity import PS_SHA_Infinity


@dataclass
class Evidence:
    """Simple representation of supporting evidence for a proposition."""

    source: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposition:
    """Data model for a learned fact or assertion."""

    type: str
    content: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)


class Lucidia:
    """A small in-memory knowledge store that powers the tests."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url
        self.identity = PS_SHA_Infinity()
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._contradictions: List[Dict[str, Any]] = []
        self._id_iter = itertools.count(1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _new_fact_id(self) -> str:
        return f"fact_{next(self._id_iter)}"

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalise_evidence(evidence: Optional[List[Any]]) -> List[Dict[str, Any]]:
        normalised: List[Dict[str, Any]] = []
        for item in evidence or []:
            if isinstance(item, Evidence):
                normalised.append(
                    {
                        "source": item.source,
                        "weight": item.weight,
                        "metadata": dict(item.metadata),
                    }
                )
            elif isinstance(item, dict):
                normalised.append(dict(item))
            else:
                normalised.append({"value": item})
        return normalised

    # ------------------------------------------------------------------
    # Public API mirrored in the tests
    # ------------------------------------------------------------------
    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Any]] = None,
    ) -> Dict[str, str]:
        """Store a proposition in memory and return identifiers."""

        if content is None:
            raise ValueError("content must not be None")

        fact_id = self._new_fact_id()
        content_hash = self._hash_content(content)
        stored_fact = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": dict(context or {}),
            "evidence": self._normalise_evidence(evidence),
            "content_hash": content_hash,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._facts[fact_id] = stored_fact
        return {"fact_id": fact_id, "content_hash": content_hash}

    def query(
        self,
        content: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        limit: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Return stored facts filtered by simple heuristics."""

        results = list(self._facts.values())

        if content:
            needle = content.lower()
            results = [fact for fact in results if needle in fact["content"].lower()]

        if confidence and "min" in confidence:
            threshold = confidence["min"]
            results = [fact for fact in results if fact["confidence"] >= threshold]

        if context:
            for key, value in context.items():
                results = [fact for fact in results if fact["context"].get(key) == value]

        if limit is not None:
            results = results[:limit]

        return {"results": results}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        """Update the stored confidence value for a fact."""

        try:
            self._facts[fact_id]["confidence"] = new_confidence
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"unknown fact_id: {fact_id}") from exc

    def get_contradictions(self) -> List[Dict[str, Any]]:
        """Return any contradictions recorded so far."""

        return list(self._contradictions)

    def get_fact_count(self) -> int:
        """Return the number of stored facts."""

        return len(self._facts)

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Record a contradiction and return its identifier."""

        contradiction_id = f"contradiction_{len(self._contradictions) + 1}"
        record = {
            "contradiction_id": contradiction_id,
            "proposition": dict(proposition),
            "conflicting_facts": list(conflicting_facts),
            "metadata": dict(metadata or {}),
        }
        self._contradictions.append(record)
        return {"contradiction_id": contradiction_id}


__all__ = ["Evidence", "Proposition", "Lucidia"]
