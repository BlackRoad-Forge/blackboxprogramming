from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import hashlib
import uuid

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
    evidence: List[Evidence]


class Lucidia:
    """Minimal in-memory implementation of the Lucidia knowledge core."""

    def __init__(self, database_url: str = "sqlite:///:memory:"):
        self.database_url = database_url
        self.facts: List[Dict[str, Any]] = []
        self._next_id = 1
        self.identity = PS_SHA_Infinity()
        self.contradictions: List[Dict[str, Any]] = []

    def learn(
        self,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Evidence]] = None,
    ) -> Dict[str, Any]:
        if content is None:
            raise ValueError("content must not be None")
        fact_id = str(self._next_id)
        self._next_id += 1
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        fact = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": context or {},
            "evidence": evidence or [],
            "content_hash": content_hash,
        }
        self.facts.append(fact)
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(
        self,
        content: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        confidence = confidence or {}
        min_conf = confidence.get("min", float("-inf"))
        max_conf = confidence.get("max", float("inf"))
        results = [
            f
            for f in self.facts
            if (content is None or content.lower() in f["content"].lower())
            and min_conf <= f["confidence"] <= max_conf
        ]
        if limit is not None:
            results = results[:limit]
        return {"results": results}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        for f in self.facts:
            if f["id"] == fact_id:
                f["confidence"] = new_confidence
                return
        raise ValueError("fact not found")

    def get_contradictions(self) -> List[Dict[str, Any]]:
        return list(self.contradictions)

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        contradiction_id = str(uuid.uuid4())
        record = {
            "id": contradiction_id,
            "proposition": proposition,
            "conflicting_facts": conflicting_facts,
            "metadata": metadata or {},
        }
        self.contradictions.append(record)
        return {"contradiction_id": contradiction_id}

    def get_fact_count(self) -> int:
        return len(self.facts)
