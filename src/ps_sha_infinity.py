"""Placeholder PS-SHA∞ identity chain implementation for tests."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List


class PS_SHA_Infinity:
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
