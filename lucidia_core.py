from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
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
    """Minimal in-memory implementation of the Lucidia core used in tests."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url
        self.identity = PS_SHA_Infinity()
        self.facts: Dict[str, Dict[str, Any]] = {}
        self.contradictions: List[Dict[str, Any]] = []
        self._fact_counter = 0

    # Utility ---------------------------------------------------------
    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Knowledge management -------------------------------------------
    def learn(
        self,
        *,
        prop_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]],
        evidence: List[Evidence],
    ) -> Dict[str, Any]:
        """Store a fact and return identifiers."""
        if content is None:
            raise Exception("content required")
        self._fact_counter += 1
        fact_id = f"fact_{self._fact_counter}"
        content_hash = self._hash_content(content)
        fact = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "content_hash": content_hash,
            "confidence": confidence,
            "context": context or {},
            "evidence": [asdict(e) if isinstance(e, Evidence) else e for e in evidence],
        }
        self.facts[fact_id] = fact
        return {"content_hash": content_hash, "fact_id": fact_id}

    def query(self, *, content: str, confidence: Optional[Dict[str, float]], limit: int = 10) -> Dict[str, Any]:
        results = []
        for fact in self.facts.values():
            if content.lower() in fact["content"].lower():
                results.append(fact)
        return {"results": results[: limit]}

    def update_confidence(self, fact_id: str, new_confidence: float) -> None:
        if fact_id in self.facts:
            self.facts[fact_id]["confidence"] = new_confidence

    # Contradiction management ---------------------------------------
    def get_contradictions(self) -> List[Dict[str, Any]]:
        return list(self.contradictions)

    def quarantine_contradiction(
        self,
        *,
        proposition: Dict[str, Any],
        conflicting_facts: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

    # Statistics -----------------------------------------------------
    def get_fact_count(self) -> int:
        return len(self.facts)
