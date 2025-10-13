"""Minimal Lucidia core implementation used by tests.

This module provides a very small in-memory knowledge base that exposes the
interfaces required by the unit tests.  It is *not* a full featured Lucidia
implementation.
"""
"""Simplified Lucidia core for unit testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    """Evidence supporting a proposition."""

    source: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)
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
    """A proposition stored by Lucidia."""

    type: str
    content: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)


class PS_SHA_Infinity:
    """Placeholder for the PS-SHA∞ identity chain.

    The real project contains a sophisticated implementation; however, the tests
    only require a minimal interface which this class provides.
    """

    def __init__(self) -> None:
        self.current_hash = "initial_hash"
        self.chain: List[str] = [self.current_hash]

    def get_continuity_events(
        self,
    ) -> List[Dict[str, Any]]:  # pragma: no cover - simple
        return []

    def append_event(self, event: Dict[str, Any]) -> str:  # pragma: no cover - simple
        new_hash = sha256(str(event).encode()).hexdigest()
        self.chain.append(new_hash)
        self.current_hash = new_hash
        return new_hash


class Lucidia:
    """Very small in-memory knowledge base used for testing."""

    def __init__(self, database_url: str | None = None) -> None:  # pragma: no cover
        self.database_url = database_url
        self.facts: Dict[str, Dict[str, Any]] = {}
        self._next_id = 1
        self.contradictions: List[Dict[str, Any]] = []
        self.identity = PS_SHA_Infinity()

    # ------------------------------------------------------------------
    # basic fact operations
    # ------------------------------------------------------------------
    def learn(
        self,
        *,
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
    ) -> Dict[str, Any]:
        """Store a new fact and return identifiers.

        Raises an ``Exception`` if ``content`` is missing so tests can verify
        error handling.
        """

        if content is None:
            raise Exception("content required")

        fact_id = f"fact_{self._next_id}"
        self._next_id += 1
        content_hash = sha256(content.encode()).hexdigest()
        self.facts[fact_id] = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": context or {},
            "evidence": evidence or [],
            "content_hash": content_hash,
        }
        return {"fact_id": fact_id, "content_hash": content_hash}

    def query(
        self, *, content: str, confidence: Dict[str, float], limit: int = 10
    ) -> Dict[str, Any]:
        """Return facts matching ``content`` substring and confidence filter."""

        min_conf = confidence.get("min", 0.0)
        results = [
            fact
            for fact in self.facts.values()
            if content.lower() in fact["content"].lower()
            and fact["confidence"] >= min_conf
        ][:limit]
        return {"results": results}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id in self.facts:
            self.facts[fact_id]["confidence"] = new_confidence

    # ------------------------------------------------------------------
    # contradiction handling (minimal stubs)
    # ------------------------------------------------------------------
    def get_contradictions(self) -> List[Any]:  # pragma: no cover - simple
        return self.contradictions

    def quarantine_contradiction(
        self,
        *,
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
        """Record a contradiction and return its ID."""

        contradiction_id = f"contradiction_{len(self.contradictions) + 1}"
        self.contradictions.append(
            {
                "id": contradiction_id,
                "proposition": proposition,
                "conflicting_facts": conflicting_facts,
                "metadata": metadata or {},
            }
        )
        return {"contradiction_id": contradiction_id}

    # ------------------------------------------------------------------
    # telemetry helpers
    # ------------------------------------------------------------------
    def get_fact_count(self) -> int:  # pragma: no cover - simple
        return len(self.facts)
        contradiction_id = sha256(
            (proposition.get("content", "") + str(conflicting_facts)).encode("utf-8")
        ).hexdigest()
        return {"contradiction_id": contradiction_id}

    def get_fact_count(self) -> int:
        return len(self._facts)
