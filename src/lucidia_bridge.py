"""FastAPI bridge for the simplified Lucidia core."""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse


class LucidiaBridge:
    """Expose the Lucidia core through a FastAPI application."""

    def __init__(self, lucidia, port: int = 5000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: List[Dict[str, Any]] = []
        self._register_routes()

    def _register_routes(self) -> None:
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
                "status": "active",
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
                return JSONResponse(
                    status_code=404, content={"error": "agent_not_registered"}
                )
            metrics = data.get("metrics", {})
            current = self.agent_metrics.get(agent_id, {})
            current.update(metrics)
            self.agent_metrics[agent_id] = current
            self.active_agents[agent_id][
                "last_heartbeat"
            ] = datetime.utcnow().isoformat()
            return {"status": "heartbeat_received", "agent_id": agent_id}

        @self.app.post("/knowledge/learn")
        def learn(data: Dict[str, Any]):
            if not data.get("content"):
                return JSONResponse(
                    status_code=400, content={"error": "content required"}
                )
            try:
                result = self.lucidia.learn(
                    prop_type=data.get("type"),
                    content=data.get("content"),
                    confidence=data.get("confidence"),
                    context=(data.get("metadata") or {}).get("context", {}),
                    evidence=(data.get("metadata") or {}).get("evidence", []),
                )
            except Exception as exc:  # pragma: no cover - defensive programming
                return JSONResponse(status_code=500, content={"error": str(exc)})
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": data.get("agent_id"),
                "content_hash": result.get("content_hash"),
                "confidence": data.get("confidence"),
                "type": data.get("type"),
            }
            self.learning_events.append(event)
            return {
                "status": "learned",
                "content_hash": result.get("content_hash"),
                "fact_id": result.get("fact_id"),
                "confidence": data.get("confidence"),
            }

        @self.app.post("/knowledge/query")
        def query(data: Dict[str, Any]):
            result = self.lucidia.query(
                content=data.get("content"),
                confidence=data.get("confidence"),
                limit=data.get("limit"),
            )
            facts = result.get("results", [])
            return {"results": facts, "count": len(facts), "query": data}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(data: Dict[str, Any]):
            fact_id = data.get("fact_id")
            new_conf = data.get("confidence")
            if not fact_id or new_conf is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "fact_id and confidence required"},
                )
            self.lucidia.update_confidence(fact_id, new_conf)
            return {
                "status": "updated",
                "fact_id": fact_id,
                "new_confidence": new_conf,
            }

        @self.app.get("/knowledge/contradictions")
        def get_contradictions():
            contradictions = self.lucidia.get_contradictions()
            serialised = []
            for c in contradictions:
                if isinstance(c, dict):
                    item = c
                else:
                    item = {}
                    for attr in [
                        "id",
                        "facts",
                        "confidence",
                        "status",
                        "discovered_at",
                        "metadata",
                    ]:
                        if hasattr(c, attr):
                            val = getattr(c, attr)
                            if attr == "facts":
                                val = [f.id if hasattr(f, "id") else f for f in val]
                            item[attr] = val
                serialised.append(item)
            return {"contradictions": serialised, "count": len(serialised)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(data: Dict[str, Any]):
            if not data.get("proposition") or not data.get("conflicting_facts"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "proposition and conflicting_facts required"},
                )
            result = self.lucidia.quarantine_contradiction(
                proposition=data["proposition"],
                conflicting_facts=data["conflicting_facts"],
                metadata=data.get("metadata"),
            )
            return {
                "status": "quarantined",
                "contradiction_id": result.get("contradiction_id"),
            }

        @self.app.get("/identity/current")
        def current_identity():
            identity = self.lucidia.identity
            return {
                "current_hash": getattr(identity, "current_hash", ""),
                "chain_length": len(getattr(identity, "chain", [])),
                "continuity_events": identity.get_continuity_events(),
            }

        @self.app.get("/telemetry/agents")
        def agent_telemetry():
            total_facts = self.lucidia.get_fact_count()
            contradictions = self.lucidia.get_contradictions()
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": self.learning_events[-10:],
                "system_stats": {
                    "total_facts": total_facts,
                    "active_contradictions": len(contradictions),
                    "identity_chain_length": len(
                        getattr(self.lucidia.identity, "chain", [])
                    ),
                },
            }
