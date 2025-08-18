from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse


class LucidiaBridge:
    """Simple FastAPI bridge exposing Lucidia operations."""

    def __init__(self, lucidia, port: int = 5001) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: list = []
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.get("/health")
        def health():
            return {
                "status": "healthy",
                "lucidia_identity": self.lucidia.identity.current_hash,
                "active_agents": len(self.active_agents),
                "timestamp": datetime.utcnow().isoformat(),
            }

        @self.app.post("/agent/register")
        def register(agent: Dict[str, Any]):
            agent_id = agent.get("agent_id")
            agent_type = agent.get("agent_type")
            if not agent_id or not agent_type:
                return JSONResponse(
                    status_code=400,
                    content={"error": "agent_id and agent_type required"},
                )
            self.active_agents[agent_id] = {
                "type": agent_type,
                "status": "active",
                "registered_at": datetime.utcnow().isoformat(),
                "capabilities": agent.get("capabilities", []),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": self.lucidia.identity.current_hash,
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, payload: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse(
                    status_code=404, content={"error": "agent_not_registered"}
                )
            self.active_agents[agent_id][
                "last_heartbeat"
            ] = datetime.utcnow().isoformat()
            metrics = payload.get("metrics", {})
            self.agent_metrics.setdefault(agent_id, {}).update(metrics)
            return {"status": "heartbeat_received"}

        @self.app.post("/knowledge/learn")
        def learn(payload: Dict[str, Any]):
            try:
                content = payload.get("content")
                if not content:
                    return JSONResponse(
                        status_code=400, content={"error": "content required"}
                    )
                result = self.lucidia.learn(
                    prop_type=payload.get("type"),
                    content=content,
                    confidence=payload.get("confidence"),
                    context=payload.get("metadata", {}).get("context"),
                    evidence=[],
                )
                self.learning_events.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent_id": payload.get("agent_id"),
                        "content_hash": result.get("content_hash"),
                        "confidence": payload.get("confidence"),
                        "type": payload.get("type"),
                    }
                )
                return {
                    "status": "learned",
                    **result,
                    "confidence": payload.get("confidence"),
                }
            except Exception as exc:  # pragma: no cover - defensive
                return JSONResponse(status_code=500, content={"error": str(exc)})

        @self.app.post("/knowledge/query")
        def query(payload: Dict[str, Any]):
            results = self.lucidia.query(**payload)
            return {**results, "count": len(results["results"]), "query": payload}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(payload: Dict[str, Any]):
            fact_id = payload.get("fact_id")
            conf = payload.get("confidence")
            if not fact_id or conf is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "fact_id and confidence required"},
                )
            self.lucidia.update_confidence(fact_id, conf)
            return {"status": "updated", "fact_id": fact_id, "new_confidence": conf}

        @self.app.get("/knowledge/contradictions")
        def get_contradictions():
            items = []
            for c in self.lucidia.get_contradictions():
                if isinstance(c, dict):
                    items.append(c)
                else:
                    items.append(
                        {
                            "id": getattr(c, "id", None),
                            "facts": [
                                getattr(f, "id", f) for f in getattr(c, "facts", [])
                            ],
                            "confidence": getattr(c, "confidence", None),
                            "status": getattr(c, "status", None),
                            "discovered_at": getattr(c, "discovered_at", None),
                            "metadata": getattr(c, "metadata", None),
                        }
                    )
            return {"contradictions": items, "count": len(items)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(payload: Dict[str, Any]):
            proposition = payload.get("proposition")
            conflicting = payload.get("conflicting_facts")
            if not proposition or not conflicting:
                return JSONResponse(
                    status_code=400,
                    content={"error": "proposition and conflicting_facts required"},
                )
            result = self.lucidia.quarantine_contradiction(
                proposition=proposition,
                conflicting_facts=conflicting,
                metadata=payload.get("metadata"),
            )
            return {"status": "quarantined", **result}

        @self.app.get("/identity/current")
        def identity_current():
            identity = self.lucidia.identity
            return {
                "current_hash": identity.current_hash,
                "chain_length": len(identity.chain),
                "continuity_events": identity.get_continuity_events(),
            }

        @self.app.get("/telemetry/agents")
        def telemetry_agents():
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
