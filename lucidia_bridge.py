from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class LucidiaBridge:
    """Minimal FastAPI bridge exposing Lucidia core operations."""

    def __init__(self, lucidia, port: int = 8000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: List[Dict[str, Any]] = []
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
        def register_agent(data: Dict[str, Any]):
            if not data.get("agent_id") or not data.get("agent_type"):
                return JSONResponse(status_code=400, content={"error": "agent_id and agent_type required"})
            agent_id = data["agent_id"]
            self.active_agents[agent_id] = {
                "type": data["agent_type"],
                "capabilities": data.get("capabilities", []),
                "registered_at": datetime.utcnow().isoformat(),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def agent_heartbeat(agent_id: str, data: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse(status_code=404, content={"error": "agent_not_registered"})
            self.active_agents[agent_id]["last_heartbeat"] = datetime.utcnow().isoformat()
            metrics = data.get("metrics", {})
            self.agent_metrics.setdefault(agent_id, {}).update(metrics)
            return {"status": "heartbeat_received"}

        @self.app.post("/knowledge/learn")
        def learn(data: Dict[str, Any]):
            if not data.get("content"):
                return JSONResponse(status_code=400, content={"error": "content required"})
            try:
                res = self.lucidia.learn(
                    prop_type=data.get("type"),
                    content=data.get("content"),
                    confidence=data.get("confidence", 0.0),
                    context=data.get("metadata", {}).get("context", {}),
                    evidence=[],
                )
            except Exception as exc:
                return JSONResponse(status_code=500, content={"error": str(exc)})
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": data.get("agent_id"),
                "content_hash": res.get("content_hash"),
                "confidence": data.get("confidence", 0.0),
                "type": data.get("type"),
            }
            self.learning_events.append(event)
            return {"status": "learned", **res, "confidence": data.get("confidence", 0.0)}

        @self.app.post("/knowledge/query")
        def query(data: Dict[str, Any]) -> Dict[str, Any]:
            res = self.lucidia.query(
                content=data.get("content", ""),
                confidence=data.get("confidence"),
                limit=data.get("limit", 10),
            )
            return {"results": res.get("results", []), "count": len(res.get("results", [])), "query": data}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(data: Dict[str, Any]):
            if not data.get("fact_id") or data.get("confidence") is None:
                return JSONResponse(status_code=400, content={"error": "fact_id and confidence required"})
            self.lucidia.update_confidence(data["fact_id"], data["confidence"])
            return {"status": "updated", "fact_id": data["fact_id"], "new_confidence": data["confidence"]}

        @self.app.get("/knowledge/contradictions")
        def get_contradictions() -> Dict[str, Any]:
            raw = self.lucidia.get_contradictions()
            processed: List[Dict[str, Any]] = []
            for item in raw:
                if isinstance(item, dict):
                    processed.append(item)
                else:
                    facts = [
                        {"id": getattr(f, "id", None)} if not isinstance(f, dict) else f
                        for f in getattr(item, "facts", [])
                    ]
                    processed.append(
                        {
                            "id": getattr(item, "id", None),
                            "facts": facts,
                            "confidence": getattr(item, "confidence", None),
                            "status": getattr(item, "status", None),
                            "discovered_at": getattr(item, "discovered_at", None),
                            "metadata": getattr(item, "metadata", {}),
                        }
                    )
            return {"contradictions": processed, "count": len(processed)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(data: Dict[str, Any]):
            if not data.get("proposition") or not data.get("conflicting_facts"):
                return JSONResponse(status_code=400, content={"error": "proposition and conflicting_facts required"})
            res = self.lucidia.quarantine_contradiction(
                proposition=data["proposition"],
                conflicting_facts=data["conflicting_facts"],
                metadata=data.get("metadata", {}),
            )
            return {"status": "quarantined", **res}

        @self.app.get("/identity/current")
        def identity_current() -> Dict[str, Any]:
            identity = self.lucidia.identity
            return {
                "current_hash": getattr(identity, "current_hash", ""),
                "chain_length": len(getattr(identity, "chain", [])),
                "continuity_events": identity.get_continuity_events() if hasattr(identity, "get_continuity_events") else [],
            }

        @self.app.get("/telemetry/agents")
        def telemetry_agents() -> Dict[str, Any]:
            stats = {
                "total_facts": getattr(self.lucidia, "get_fact_count", lambda: len(self.lucidia.facts))(),
                "active_contradictions": len(self.lucidia.get_contradictions()),
                "identity_chain_length": len(getattr(self.lucidia.identity, "chain", [])),
            }
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": self.learning_events[-10:],
                "system_stats": stats,
            }
