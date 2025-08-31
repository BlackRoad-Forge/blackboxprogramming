from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse


class LucidiaBridge:
    """FastAPI bridge providing access to the Lucidia core."""

    def __init__(self, lucidia, port: int = 8000):
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()

        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events = []

        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/health")
        def health():
            return {
                "status": "healthy",
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
                "active_agents": len(self.active_agents),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @self.app.post("/agent/register")
        def register_agent(data: Dict[str, Any]):
            agent_id = data.get("agent_id")
            agent_type = data.get("agent_type")
            if not agent_id or not agent_type:
                return JSONResponse(status_code=400, content={"error": "agent_id and agent_type required"})
            self.active_agents[agent_id] = {
                "type": agent_type,
                "capabilities": data.get("capabilities", []),
                "status": "active",
                "registered_at": datetime.utcnow().isoformat(),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def agent_heartbeat(agent_id: str, payload: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse(status_code=404, content={"error": "agent_not_registered"})
            self.agent_metrics[agent_id] = payload.get("metrics", {})
            self.active_agents[agent_id]["last_heartbeat"] = datetime.utcnow().isoformat()
            return {"status": "heartbeat_received"}

        @self.app.post("/knowledge/learn")
        def learn(body: Dict[str, Any]):
            content = body.get("content")
            prop_type = body.get("type")
            confidence = body.get("confidence")
            if not content:
                return JSONResponse(status_code=400, content={"error": "content required"})
            try:
                result = self.lucidia.learn(
                    prop_type=prop_type,
                    content=content,
                    confidence=confidence,
                    context=body.get("metadata", {}).get("context", {}),
                    evidence=[],
                )
            except Exception as exc:  # noqa: BLE001 - we want consistent JSON errors
                return JSONResponse(status_code=500, content={"error": str(exc)})
            if body.get("agent_id"):
                self.learning_events.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": body["agent_id"],
                    "content_hash": result.get("content_hash"),
                    "confidence": confidence,
                    "type": prop_type,
                })
            return {
                "status": "learned",
                "content_hash": result.get("content_hash"),
                "fact_id": result.get("fact_id"),
                "confidence": confidence,
            }

        @self.app.post("/knowledge/query")
        def query(body: Dict[str, Any]):
            result = self.lucidia.query(
                content=body.get("content"),
                confidence=body.get("confidence"),
                limit=body.get("limit"),
            )
            results = result.get("results", [])
            return {"results": results, "count": len(results), "query": body}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(body: Dict[str, Any]):
            fact_id = body.get("fact_id")
            confidence = body.get("confidence")
            if fact_id is None or confidence is None:
                return JSONResponse(status_code=400, content={"error": "fact_id and confidence required"})
            self.lucidia.update_confidence(fact_id, confidence)
            return {"status": "updated", "fact_id": fact_id, "new_confidence": confidence}

        @self.app.get("/knowledge/contradictions")
        def get_contradictions():
            contras = self.lucidia.get_contradictions()

            def _serialize_fact(fact):
                if isinstance(fact, dict):
                    return fact
                return {"id": getattr(fact, "id", None)}

            def _serialize_contra(c):
                if isinstance(c, dict):
                    return c
                return {
                    "id": getattr(c, "id", None),
                    "facts": [_serialize_fact(f) for f in getattr(c, "facts", [])],
                    "confidence": getattr(c, "confidence", None),
                    "status": getattr(c, "status", None),
                    "discovered_at": getattr(c, "discovered_at", None),
                    "metadata": getattr(c, "metadata", {}),
                }

            serialized = [_serialize_contra(c) for c in contras]
            return {"contradictions": serialized, "count": len(serialized)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(body: Dict[str, Any]):
            proposition = body.get("proposition")
            conflicting = body.get("conflicting_facts")
            if not proposition or not conflicting:
                return JSONResponse(status_code=400, content={"error": "proposition and conflicting_facts required"})
            result = self.lucidia.quarantine_contradiction(
                proposition=proposition,
                conflicting_facts=conflicting,
                metadata=body.get("metadata", {}),
            )
            return {"status": "quarantined", **result}

        @self.app.get("/identity/current")
        def identity_current():
            identity = self.lucidia.identity
            return {
                "current_hash": getattr(identity, "current_hash", ""),
                "chain_length": len(getattr(identity, "chain", [])),
                "continuity_events": identity.get_continuity_events(),
            }

        @self.app.get("/telemetry/agents")
        def telemetry_agents():
            stats = {
                "total_facts": self.lucidia.get_fact_count(),
                "active_contradictions": len(self.lucidia.get_contradictions()),
                "identity_chain_length": len(getattr(self.lucidia.identity, "chain", [])),
            }
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": self.learning_events[-10:],
                "system_stats": stats,
            }

    def start_server(self):
        import uvicorn

        uvicorn.run(self.app, port=self.port)
