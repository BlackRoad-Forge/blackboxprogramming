from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ps_sha_infinity import PS_SHA_Infinity


@dataclass
class Evidence:
    source: str
    weight: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Proposition:
    type: str
    content: str
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)


class Lucidia:
    """In-memory knowledge store used for testing."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url
        self.identity = PS_SHA_Infinity()
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._fact_counter = 0
        self.contradictions: List[Dict[str, Any]] = []

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Evidence]] = None,
    ) -> Dict[str, Any]:
        if not content:
            raise ValueError("content is required")
        self._fact_counter += 1
        fact_id = f"fact_{self._fact_counter}"
        content_hash = self._hash_content(content)
        self._facts[fact_id] = {
            "id": fact_id,
            "content": content,
            "content_hash": content_hash,
            "confidence": confidence,
            "type": prop_type,
            "context": context or {},
            "evidence": [
                e.__dict__ if isinstance(e, Evidence) else e for e in (evidence or [])
            ],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(
        self, content: str, confidence: Optional[Dict[str, Any]] = None, limit: int = 10
    ) -> Dict[str, Any]:
        results = []
        for fact in self._facts.values():
            if content.lower() in fact["content"].lower():
                if confidence is None or fact["confidence"] >= confidence.get("min", 0):
                    results.append(fact)
        return {"results": results[:limit]}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id in self._facts:
            self._facts[fact_id]["confidence"] = new_confidence

    def get_contradictions(self):
        return list(self.contradictions)

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cid = f"contradiction_{len(self.contradictions) + 1}"
        self.contradictions.append(
            {
                "id": cid,
                "proposition": proposition,
                "conflicting_facts": conflicting_facts,
                "metadata": metadata,
            }
        )
        return {"contradiction_id": cid}

    def get_fact_count(self) -> int:
        return len(self._facts)
