from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from lucidia_core import Lucidia


class LucidiaBridge:
    """Minimal FastAPI bridge exposing Lucidia operations for tests."""

    def __init__(self, lucidia: Lucidia, port: int = 8000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: list[Dict[str, Any]] = []
        self._setup_routes()

    # ------------------------------------------------------------------
    def _setup_routes(self) -> None:
        @self.app.get("/health")
        def health() -> Dict[str, Any]:
            return {
                "status": "healthy",
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
                "active_agents": len(self.active_agents),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @self.app.post("/agent/register")
        def register_agent(agent: Dict[str, Any]):
            agent_id = agent.get("agent_id")
            agent_type = agent.get("agent_type")
            if not agent_id or not agent_type:
                return JSONResponse({"error": "agent_id and agent_type required"}, status_code=400)
            self.active_agents[agent_id] = {
                "type": agent_type,
                "status": "active",
                "registered_at": datetime.utcnow().isoformat(),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, payload: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse({"error": "agent_not_registered"}, status_code=404)
            self.active_agents[agent_id]["last_heartbeat"] = datetime.utcnow().isoformat()
            metrics = payload.get("metrics")
            if metrics:
                self.agent_metrics.setdefault(agent_id, {}).update(metrics)
            return {"status": "heartbeat_received"}

        @self.app.post("/knowledge/learn")
        def learn(payload: Dict[str, Any]):
            if not payload.get("content"):
                return JSONResponse({"error": "content required"}, status_code=400)
            try:
                res = self.lucidia.learn(
                    prop_type=payload.get("type"),
                    content=payload.get("content"),
                    confidence=payload.get("confidence"),
                    context=(payload.get("metadata") or {}).get("context"),
                    evidence=(payload.get("metadata") or {}).get("evidence", []),
                )
            except Exception as exc:  # pragma: no cover - defensive
                return JSONResponse({"error": str(exc)}, status_code=500)

            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": payload.get("agent_id"),
                "content_hash": res["content_hash"],
                "confidence": payload.get("confidence"),
                "type": payload.get("type"),
            }
            self.learning_events.append(event)

            return {
                "status": "learned",
                "content_hash": res["content_hash"],
                "fact_id": res["fact_id"],
                "confidence": payload.get("confidence"),
            }

        @self.app.post("/knowledge/query")
        def query(payload: Dict[str, Any]) -> Dict[str, Any]:
            res = self.lucidia.query(
                content=payload.get("content"),
                confidence=payload.get("confidence"),
                limit=payload.get("limit", 10),
            )
            return {"results": res["results"], "count": len(res["results"]), "query": payload}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(payload: Dict[str, Any]):
            if not payload.get("fact_id") or payload.get("confidence") is None:
                return JSONResponse({"error": "fact_id and confidence required"}, status_code=400)
            self.lucidia.update_confidence(payload["fact_id"], payload["confidence"])
            return {
                "status": "updated",
                "fact_id": payload["fact_id"],
                "new_confidence": payload["confidence"],
            }

        @self.app.get("/knowledge/contradictions")
        def get_contradictions() -> Dict[str, Any]:
            contras = self.lucidia.get_contradictions()
            encoded = []
            for c in contras:
                if isinstance(c, dict):
                    encoded.append(c)
                else:
                    encoded.append(
                        {
                            "id": getattr(c, "id", None),
                            "facts": [getattr(f, "id", f) for f in getattr(c, "facts", [])],
                            "confidence": getattr(c, "confidence", None),
                            "status": getattr(c, "status", None),
                            "discovered_at": getattr(c, "discovered_at", None),
                            "metadata": getattr(c, "metadata", None),
                        }
                    )
            return {"contradictions": encoded, "count": len(encoded)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(payload: Dict[str, Any]):
            if not payload.get("proposition") or not payload.get("conflicting_facts"):
                return JSONResponse({"error": "proposition and conflicting_facts required"}, status_code=400)
            res = self.lucidia.quarantine_contradiction(
                proposition=payload["proposition"],
                conflicting_facts=payload["conflicting_facts"],
                metadata=payload.get("metadata"),
            )
            return {"status": "quarantined", **res}

        @self.app.get("/identity/current")
        def current_identity() -> Dict[str, Any]:
            ident = self.lucidia.identity
            return {
                "current_hash": ident.current_hash,
                "chain_length": len(ident.chain),
                "continuity_events": ident.get_continuity_events(),
            }

        @self.app.get("/telemetry/agents")
        def telemetry() -> Dict[str, Any]:
            stats = {
                "total_facts": self.lucidia.get_fact_count(),
                "active_contradictions": len(self.lucidia.get_contradictions()),
                "identity_chain_length": len(self.lucidia.identity.chain),
            }
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": self.learning_events,
                "system_stats": stats,
            }

    # ------------------------------------------------------------------
    def start_server(self) -> None:  # pragma: no cover - not used in tests
        import uvicorn

        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
