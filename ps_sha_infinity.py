import hashlib
import json
from typing import Any, List


class PS_SHA_Infinity:
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
