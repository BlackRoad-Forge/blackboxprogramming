from __future__ import annotations
import os, requests
from typing import Dict, Any, Optional

class PSSHAInfinityClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token or os.getenv("PS_SHA_INFINITY_TOKEN")

    def _h(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def health(self) -> Dict[str, Any]:
        return requests.get(f"{self.base_url}/health").json()

    def hash(self, payload: Dict[str, Any], breath: int = 0, stages=None, meta=None, salt: str | None=None):
        body = {"payload": payload, "breath": breath, "stages": stages, "meta": meta, "salt": salt}
        r = requests.post(f"{self.base_url}/hash", headers=self._h(), json=body)
        r.raise_for_status()
        return r.json()

    def verify(self, hash_hex: str, signature_hex: str):
        r = requests.post(f"{self.base_url}/verify", headers=self._h(), json={"hash_hex": hash_hex, "signature_hex": signature_hex})
        r.raise_for_status()
        return r.json()

    def chat_bind(self, message: str, context: Dict[str, Any], breath: int = 0, meta=None, idem_key: str=""):
        headers = self._h()
        if idem_key:
            headers["Idempotency-Key"] = idem_key
        r = requests.post(
            f"{self.base_url}/chat-bind",
            headers=headers,
            json={"message": message, "context": context, "breath": breath, "meta": meta},
        )
        r.raise_for_status()
        return r.json()
