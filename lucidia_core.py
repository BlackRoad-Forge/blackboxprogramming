from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
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
    context: Dict[str, Any]
    evidence: List[Evidence] = field(default_factory=list)


class Lucidia:
    """A very small in-memory knowledge store used for testing."""

    def __init__(self, database_url: str = "sqlite:///:memory:") -> None:
        self.database_url = database_url
        self.identity = PS_SHA_Infinity()
        self._facts: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Knowledge operations
    # ------------------------------------------------------------------
    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Evidence]] = None,
    ) -> Dict[str, str]:
        """Store a proposition in memory and return identifiers."""
        if not content:
            raise Exception("content required")

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        fact_id = str(uuid.uuid4())
        self._facts[fact_id] = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": context or {},
            "evidence": [
                e.__dict__ if isinstance(e, Evidence) else e
                for e in (evidence or [])
            ],
            "content_hash": content_hash,
        }
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(
        self,
        content: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        results = list(self._facts.values())
        if content:
            results = [
                f for f in results if content.lower() in f["content"].lower()
            ]
        if confidence and "min" in confidence:
            results = [f for f in results if f["confidence"] >= confidence["min"]]
        return {"results": results[:limit]}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id in self._facts:
            self._facts[fact_id]["confidence"] = new_confidence

    # ------------------------------------------------------------------
    # Contradiction handling (stub implementations)
    # ------------------------------------------------------------------
    def get_contradictions(self) -> List[Any]:
        return []

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        return {"contradiction_id": str(uuid.uuid4())}

    # ------------------------------------------------------------------
    def get_fact_count(self) -> int:
        return len(self._facts)
