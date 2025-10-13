import hashlib
import json
from typing import Any, List


class PS_SHA_Infinity:
    """Simplified identity chain using hash continuity."""

    def __init__(self) -> None:
        genesis = hashlib.sha256(b"genesis").hexdigest()
        self.chain: List[str] = [genesis]
        self.current_hash: str = genesis
        self._events: List[Any] = []

    def append_event(self, event: Any) -> str:
        """Append an event and update the chain hash."""
        payload = json.dumps(event, sort_keys=True).encode()
        new_hash = hashlib.sha256(self.current_hash.encode() + payload).hexdigest()
        self.chain.append(new_hash)
        self.current_hash = new_hash
        self._events.append(event)
        return new_hash

    def get_continuity_events(self) -> List[Any]:
        """Return a list of recorded continuity events."""
        return list(self._events)
"""Simple PS-SHA∞ identity placeholder used for testing.

The real project uses a cryptographic identity chain.  For the unit tests we
only need minimal functionality: a current hash value, a history of hashes
("chain") and helper methods to return continuity events and append new
entries.  This lightweight implementation keeps everything in memory and uses
UUIDs to generate pseudo hashes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PS_SHA_Infinity:
    """Minimal identity chain used by the tests."""

    current_hash: str = field(default_factory=lambda: uuid.uuid4().hex)
    chain: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        if not self.chain:
            self.chain.append(self.current_hash)

    def get_continuity_events(self) -> List[Dict[str, Any]]:
        """Return recorded identity events."""
        return [{"hash": h} for h in self.chain]

    def append_event(self, event: Dict[str, Any]) -> str:
        """Append a new event to the chain and return the new hash."""
        new_hash = uuid.uuid4().hex
        self.chain.append(new_hash)
        self.current_hash = new_hash
        return new_hash
    """Simple PS-SHA∞ identity chain for testing.

    Maintains a chain of hashes representing events. Each event is
    hashed and appended to the chain. The current hash is always the
    latest element in the chain. Continuity events are stored for
    inspection by tests.
    """

    def __init__(self) -> None:
        self.chain: List[str] = []
        self._events: List[Any] = []
        genesis = self._hash_event({"event": "genesis"})
        self.chain.append(genesis)
        self.current_hash: str = genesis

    def _hash_event(self, event: Any) -> str:
        data = json.dumps(event, sort_keys=True).encode()
        return hashlib.sha256(data).hexdigest()

    def append_event(self, event: Any) -> str:
        """Append an event to the chain and update current_hash."""
        self._events.append(event)
        new_hash = self._hash_event(event)
        self.chain.append(new_hash)
        self.current_hash = new_hash
        return new_hash

    def get_continuity_events(self) -> List[Any]:
        """Return list of recorded events."""
        return list(self._events)
