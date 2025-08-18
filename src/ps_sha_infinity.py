"""Simplified PS-SHA∞ identity chain implementation for testing."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, List


def _hash_data(data: str) -> str:
    return sha256(data.encode("utf-8")).hexdigest()


@dataclass
class PS_SHA_Infinity:
    """Tiny implementation of a PS-SHA∞ style identity chain.

    This implementation is intentionally minimal and only supports the
    features required by the unit tests. It tracks an append-only chain of
    hashes and a list of continuity events that describe when new events are
    added to the chain.
    """

    chain: List[str] = field(default_factory=list)
    _continuity_events: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        genesis = _hash_data("genesis")
        self.chain.append(genesis)

    @property
    def current_hash(self) -> str:
        return self.chain[-1]

    def append_event(self, event: Dict[str, Any]) -> str:
        """Append an event to the chain and return the new hash."""
        event_repr = f"{self.current_hash}{event}"
        new_hash = _hash_data(event_repr)
        self.chain.append(new_hash)
        # Store a copy so tests cannot mutate internal state.
        self._continuity_events.append(dict(event))
        return new_hash

    def get_continuity_events(self) -> List[Dict[str, Any]]:
        """Return a list of recorded continuity events."""
        return list(self._continuity_events)
