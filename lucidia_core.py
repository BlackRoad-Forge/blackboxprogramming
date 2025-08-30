import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    """Simple representation of supporting evidence for a proposition."""
    source: str
    weight: float
    metadata: Dict[str, Any]


@dataclass
class Proposition:
    """Data model for a learned fact or assertion."""
    type: str
    content: str
    confidence: float
    context: Dict[str, Any]
    evidence: List[Evidence] = field(default_factory=list)


class PS_SHA_Infinity:  # pragma: no cover - patched in tests
    """Placeholder for identity component. Patched in tests."""
    pass


class Lucidia:
    """Minimal in-memory implementation of the Lucidia core used in tests."""

    def __init__(self, database_url: str = "sqlite:///:memory:") -> None:
        # The database URL is accepted for API compatibility but unused.
        self.database_url = database_url
        self._facts: List[Dict[str, Any]] = []
        self._next_id: int = 1

    def learn(
        self,
        prop_type: str,
        content: Optional[str],
        confidence: float,
        context: Dict[str, Any],
        evidence: List[Any],
    ) -> Dict[str, Any]:
        """Store a new fact and return identifiers."""
        if content is None:
            raise ValueError("content cannot be None")

        fact_id = self._next_id
        self._next_id += 1
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        fact = {
            "id": fact_id,
            "type": prop_type,
            "content": content,
            "confidence": confidence,
            "context": context,
            "evidence": evidence,
            "content_hash": content_hash,
        }
        self._facts.append(fact)
        return {"fact_id": fact_id, "content_hash": content_hash}

    def query(
        self,
        content: Optional[str] = None,
        confidence: Optional[Dict[str, float]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Query stored facts based on content substring and confidence."""
        results = list(self._facts)
        if content:
            results = [f for f in results if content.lower() in f["content"].lower()]
        if confidence and "min" in confidence:
            results = [f for f in results if f["confidence"] >= confidence["min"]]
        return {"results": results[:limit]}

    def update_confidence(self, fact_id: int, new_confidence: float) -> None:
        """Update the confidence score for a stored fact."""
        for fact in self._facts:
            if fact["id"] == fact_id:
                fact["confidence"] = new_confidence
                return
        raise KeyError(f"Fact id {fact_id} not found")

    def get_fact_count(self) -> int:
        """Return the total number of stored facts."""
        return len(self._facts)

    # The following methods are placeholders that satisfy the test suite.
    def get_contradictions(self):  # pragma: no cover - simple placeholder
        return []

    def quarantine_contradiction(
        self,
        proposition: Dict[str, Any],
        conflicting_facts: List[int],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:  # pragma: no cover - simple placeholder
        return {"contradiction_id": hashlib.md5(str(proposition).encode()).hexdigest()}
