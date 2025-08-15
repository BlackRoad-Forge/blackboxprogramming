import os, time
from typing import Any, Dict, Optional
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from ps_sha_infinity_core import ps_sha_infinity, sign_message, verify_message
from fastapi.responses import FileResponse

API_TOKEN = os.getenv("PS_SHA_INFINITY_TOKEN", "change-me-dev")
SIGNING_SECRET = os.getenv("PS_SHA_INFINITY_SIGNING_SECRET", "dev-signing-secret")
DEFAULT_SALT = os.getenv("PS_SHA_INFINITY_SALT", "dev-salt")
RATE_LIMIT_QPS = float(os.getenv("PS_SHA_INFINITY_QPS", "10"))

last_ts = 0.0
def rate_gate():
    global last_ts
    now = time.time()
    min_dt = 1.0 / RATE_LIMIT_QPS
    if now - last_ts < min_dt:
        time.sleep(min_dt - (now - last_ts))
    last_ts = time.time()

class HashRequest(BaseModel):
    payload: Dict[str, Any]
    salt: Optional[str] = None
    breath: int = Field(default=0, description="trinary: 1,0,-1")
    stages: Optional[list[str]] = None
    meta: Optional[Dict[str, Any]] = None

class VerifyRequest(BaseModel):
    hash_hex: str
    signature_hex: str

class ChatBindRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}
    breath: int = 0
    meta: Optional[Dict[str, Any]] = None

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(title="PS-SHA∞ API", version="1.0.0", middleware=middleware)

def check_auth(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.middleware("http")
async def idempotency_mw(request: Request, call_next):
    rate_gate()
    req_id = request.headers.get("Idempotency-Key")
    response = await call_next(request)
    if req_id:
        response.headers["Idempotency-Key"] = req_id
    return response

@app.get("/health")
def health():
    return {"ok": True, "service": "ps-sha-infinity", "ts": int(time.time())}

@app.post("/hash")
def hash_endpoint(req: HashRequest, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    res = ps_sha_infinity(
        payload=req.payload,
        salt=req.salt or DEFAULT_SALT,
        breath=req.breath,
        stages=req.stages,
        meta=req.meta,
    )
    sig = sign_message(res["hash_hex"], SIGNING_SECRET)
    return {"hash": res, "signature_hex": sig}

@app.post("/verify")
def verify_endpoint(req: VerifyRequest, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    ok = verify_message(req.hash_hex, req.signature_hex, SIGNING_SECRET)
    return {"verified": ok}

@app.post("/breath")
def breath_endpoint(authorization: Optional[str] = Header(None), breath: int = 0):
    check_auth(authorization)
    # Pure trinary pulse; can be wired to hardware or logs
    if breath not in (1, 0, -1):
        raise HTTPException(400, "breath must be 1,0,-1")
    return {"breath": breath, "ack": True, "ts": int(time.time())}

@app.post("/chat-bind")
def chat_bind_endpoint(req: ChatBindRequest, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    # Bind every message + context to a PS-SHA∞ envelope for truth-state anchoring
    payload = {"message": req.message, "context": req.context}
    res = ps_sha_infinity(payload=payload, salt=DEFAULT_SALT, breath=req.breath, meta=req.meta)
    sig = sign_message(res["hash_hex"], SIGNING_SECRET)
    return {"hash": res, "signature_hex": sig, "echo": payload}


@app.get("/ui", include_in_schema=False)
def serve_ui():
    """Serve the static chat UI."""
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "ui", "index.html")
    return FileResponse(file_path, media_type="text/html")
