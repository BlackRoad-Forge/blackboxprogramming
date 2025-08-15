<!-- FILE: webstr/server.py -->
import os
import pathlib
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import httpx

ROOT = pathlib.Path(__file__).resolve().parent
WEB = ROOT / "web"

app = FastAPI(title="Lucidia Webstr", version="1.0")

# CORS: allow browser use from anywhere (tighten later if you want)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# serve static UI
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")

class IngestRequest(BaseModel):
    repo: str  # e.g. "blackboxprogramming/blackboxprogramming"
    title: str
    body: str
    labels: List[str] = ["ingest", "auto"]

    @field_validator("repo")
    @classmethod
    def repo_must_be_slug(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("repo must look like owner/name")
        return v

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/")
async def index():
    index_path = WEB / "index.html"
    if not index_path.exists():
        return JSONResponse({"error": "index.html missing"}, status_code=500)
    return FileResponse(index_path)

@app.post("/api/ingest")
async def api_ingest(payload: IngestRequest):
    token = os.getenv("GH_TOKEN")
    if not token:
        raise HTTPException(500, detail="GH_TOKEN not set on server")

    url = f"https://api.github.com/repos/{payload.repo}/issues"
    data = {"title": payload.title, "body": payload.body, "labels": payload.labels}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "lucidia-webstr/1.0",
            },
            json=data,
        )
    if r.status_code >= 300:
        raise HTTPException(r.status_code, detail=r.text)

    js = r.json()
    return {"number": js.get("number"), "url": js.get("html_url")}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)