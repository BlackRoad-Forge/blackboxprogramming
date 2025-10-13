"""Minimal FastAPI bridge exposing Lucidia core functionality."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse


class LucidiaBridge:
    """Small wrapper that exposes a Lucidia instance via FastAPI."""

    def __init__(self, lucidia, port: int = 8000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: List[Dict[str, Any]] = []

        self._add_routes()

    # ------------------------------------------------------------------
    # route definitions
    # ------------------------------------------------------------------
    def _add_routes(self) -> None:
        app = self.app

        @app.get("/health")
        def health() -> Dict[str, Any]:
            return {
                "status": "healthy",
                "lucidia_identity": self.lucidia.identity.current_hash,
                "active_agents": len(self.active_agents),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.post("/agent/register")
        def register_agent(data: Dict[str, Any]) -> Dict[str, Any]:
            agent_id = data.get("agent_id")
            agent_type = data.get("agent_type")
            if not agent_id or not agent_type:
                return JSONResponse(
                    status_code=400,
                    content={"error": "agent_id and agent_type required"},
                )
            self.active_agents[agent_id] = {
                "type": agent_type,
                "capabilities": data.get("capabilities", []),
                "registered_at": datetime.utcnow().isoformat(),
                "status": "active",
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": self.lucidia.identity.current_hash,
            }

        @app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
            if agent_id not in self.active_agents:
                return JSONResponse(
                    status_code=404, content={"error": "agent_not_registered"}
                )
            self.active_agents[agent_id][
                "last_heartbeat"
            ] = datetime.utcnow().isoformat()
            metrics = data.get("metrics", {})
            self.agent_metrics.setdefault(agent_id, {}).update(metrics)
            return {"status": "heartbeat_received"}

        @app.post("/knowledge/learn")
        def learn(data: Dict[str, Any]) -> Dict[str, Any]:
            if not data.get("content") or not data.get("type"):
                return JSONResponse(
                    status_code=400, content={"error": "content required"}
                )
            try:
                res = self.lucidia.learn(
                    prop_type=data["type"],
                    content=data["content"],
                    confidence=data.get("confidence", 0.0),
                    context=data.get("metadata", {}).get("context", {}),
                    evidence=[],
                )
            except Exception as exc:  # pragma: no cover - error path
                return JSONResponse(status_code=500, content={"error": str(exc)})

            self.learning_events.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": data.get("agent_id"),
                    "content_hash": res["content_hash"],
                    "confidence": data.get("confidence"),
                    "type": data["type"],
                }
            )
            return {"status": "learned", **res, "confidence": data.get("confidence")}

        @app.post("/knowledge/query")
        def query(data: Dict[str, Any]) -> Dict[str, Any]:
            results = self.lucidia.query(
                content=data.get("content", ""),
                confidence=data.get("confidence", {}),
                limit=data.get("limit", 10),
            )
            return {
                "results": results.get("results", []),
                "count": len(results.get("results", [])),
                "query": data,
            }

        @app.post("/knowledge/update_confidence")
        def update_confidence(data: Dict[str, Any]) -> Dict[str, Any]:
            if not data.get("fact_id") or data.get("confidence") is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "fact_id and confidence required"},
                )
            self.lucidia.update_confidence(data["fact_id"], data["confidence"])
            return {
                "status": "updated",
                "fact_id": data["fact_id"],
                "new_confidence": data["confidence"],
            }

        @app.get("/knowledge/contradictions")
        def get_contradictions() -> Dict[str, Any]:
            contradictions = self.lucidia.get_contradictions()
            processed = []
            for c in contradictions:
                if isinstance(c, dict):
                    processed.append(c)
                else:  # handle mocked objects
                    processed.append(
                        {
                            "id": getattr(c, "id", None),
                            "facts": [
                                {"id": getattr(f, "id", None)}
                                for f in getattr(c, "facts", [])
                            ],
                            "confidence": getattr(c, "confidence", None),
                            "status": getattr(c, "status", None),
                            "discovered_at": getattr(c, "discovered_at", None),
                            "metadata": getattr(c, "metadata", None),
                        }
                    )
            return {"contradictions": processed, "count": len(processed)}

        @app.post("/knowledge/quarantine_contradiction")
        def quarantine(data: Dict[str, Any]) -> Dict[str, Any]:
            if not data.get("proposition") or not data.get("conflicting_facts"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "proposition and conflicting_facts required"},
                )
            res = self.lucidia.quarantine_contradiction(
                proposition=data["proposition"],
                conflicting_facts=data["conflicting_facts"],
                metadata=data.get("metadata", {}),
            )
            return {"status": "quarantined", **res}

        @app.get("/identity/current")
        def identity_current() -> Dict[str, Any]:
            ident = self.lucidia.identity
            return {
                "current_hash": ident.current_hash,
                "chain_length": len(getattr(ident, "chain", [])),
                "continuity_events": ident.get_continuity_events(),
            }

        @app.get("/telemetry/agents")
        def telemetry_agents() -> Dict[str, Any]:
            recent = self.learning_events[-50:]
            stats = {
                "total_facts": self.lucidia.get_fact_count(),
                "active_contradictions": len(self.lucidia.get_contradictions()),
                "identity_chain_length": len(
                    getattr(self.lucidia.identity, "chain", [])
                ),
            }
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": recent,
                "system_stats": stats,
            }

    # ------------------------------------------------------------------
    def start_server(self) -> None:  # pragma: no cover - used in integration tests
        import uvicorn

        uvicorn.run(self.app, port=self.port)
