import hashlib
import json
import time
from typing import Any, Dict, List


class PS_SHA_Infinity:
    """Minimal PS-SHA∞ identity chain implementation for tests."""

    def __init__(self) -> None:
        self.chain: List[str] = []
        self._continuity_events: List[Dict[str, Any]] = []
        genesis = {"genesis": True, "timestamp": time.time()}
        genesis_hash = self._hash(genesis)
        self.chain.append(genesis_hash)
        self.current_hash = genesis_hash

    def _hash(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def append_event(self, event: Dict[str, Any]) -> str:
        event_record = {
            "event": event,
            "prev_hash": self.current_hash,
            "timestamp": time.time(),
        }
        new_hash = self._hash(event_record)
        self.chain.append(new_hash)
        self.current_hash = new_hash
        self._continuity_events.append(event)
        return new_hash

    def get_continuity_events(self) -> List[Dict[str, Any]]:
        return list(self._continuity_events)
