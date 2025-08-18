import hashlib
import json
from typing import Any, Dict, List


class PS_SHA_Infinity:
    """A minimal identity chain implementation for testing.

    The chain is a simple list of SHA256 hashes. Each new event extends the
    chain by hashing the previous hash together with a JSON representation of
    the event. Continuity events are stored for inspection by the tests.
    """

    def __init__(self) -> None:
        genesis = hashlib.sha256(b"genesis").hexdigest()
        self.chain: List[str] = [genesis]
        self.current_hash: str = genesis
        self._continuity_events: List[Dict[str, Any]] = []

    def append_event(self, event: Dict[str, Any]) -> str:
        """Append an event to the chain and return the new hash."""
        payload = json.dumps(event, sort_keys=True)
        new_hash = hashlib.sha256(
            (self.current_hash + payload).encode("utf-8")
        ).hexdigest()
        self.chain.append(new_hash)
        self.current_hash = new_hash
        self._continuity_events.append(event)
        return new_hash

    def get_continuity_events(self) -> List[Dict[str, Any]]:
        """Return a copy of continuity events tracked so far."""
        return list(self._continuity_events)
