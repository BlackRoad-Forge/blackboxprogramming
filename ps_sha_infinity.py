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
