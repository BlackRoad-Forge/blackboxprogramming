"""Minimal PS-SHA∞ identity chain implementation for unit tests."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


class PS_SHA_Infinity:
    """A lightweight, in-memory identity chain."""

    def __init__(self) -> None:
        genesis = hashlib.sha256(b"genesis").hexdigest()
        self.chain: List[str] = [genesis]
        self.current_hash: str = genesis
        self._events: List[Dict[str, Any]] = []

    def append_event(self, event: Dict[str, Any]) -> str:
        """Append an event and update the continuity hash."""

        payload = json.dumps(event, sort_keys=True).encode("utf-8")
        new_hash = hashlib.sha256(self.current_hash.encode("utf-8") + payload).hexdigest()
        self.chain.append(new_hash)
        self.current_hash = new_hash
        self._events.append(dict(event))
        return new_hash

    def get_continuity_events(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of recorded events."""

        return [dict(event) for event in self._events]


__all__ = ["PS_SHA_Infinity"]
