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
