"""Simplified Lucidia core for unit testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from threading import Lock
from typing import Any, Dict, List, Optional

from ps_sha_infinity import PS_SHA_Infinity


@dataclass
class Evidence:
    source: str
    weight: float
    metadata: Dict[str, Any]


@dataclass
class Proposition:
    type: str
    content: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)


class Lucidia:
    """In-memory knowledge store used for tests.

    It provides a minimal interface that mimics the expected behaviour of the
    real Lucidia core used in production. Facts are stored in an in-memory
    dictionary and indexed by a generated identifier.
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._next_id = 1
        self._lock = Lock()
        self.identity = PS_SHA_Infinity()

    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Evidence]] = None,
    ) -> Dict[str, str]:
        if not content:
            raise Exception("content required")
        context = context or {}
        evidence = evidence or []
        content_hash = sha256(content.encode("utf-8")).hexdigest()
        with self._lock:
            fact_id = f"fact_{self._next_id}"
            self._next_id += 1
            self._facts[fact_id] = {
                "id": fact_id,
                "type": prop_type,
                "content": content,
                "content_hash": content_hash,
                "confidence": confidence,
                "context": context,
                "evidence": [
                    e.__dict__ if isinstance(e, Evidence) else e for e in evidence
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(
        self,
        content: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        results = list(self._facts.values())
        if content:
            content_lower = content.lower()
            results = [f for f in results if content_lower in f["content"].lower()]
        if confidence and "min" in confidence:
            results = [f for f in results if f["confidence"] >= confidence["min"]]
        if limit is not None:
            results = results[:limit]
        return {"results": results}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id in self._facts:
            self._facts[fact_id]["confidence"] = new_confidence

    def get_contradictions(self) -> List[Dict[str, Any]]:
        """Return a list of contradictions.

        This simplified implementation does not perform real contradiction
        detection; it merely returns an empty list which is sufficient for the
        tests that exercise this method.
        """
        return []

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        contradiction_id = sha256(
            (proposition.get("content", "") + str(conflicting_facts)).encode("utf-8")
        ).hexdigest()
        return {"contradiction_id": contradiction_id}

    def get_fact_count(self) -> int:
        return len(self._facts)
