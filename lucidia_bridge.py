"""FastAPI bridge exposing Lucidia core functionality.

The implementation here is intentionally lightweight; it only provides the
endpoints and behaviour required by the unit tests.  The bridge keeps simple
in-memory structures describing registered agents, their metrics and learning
events.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse


class LucidiaBridge:
    """Lightweight FastAPI bridge exposing Lucidia core operations."""

    def __init__(self, lucidia, port: int = 8000) -> None:
from lucidia_core import Lucidia


class LucidiaBridge:
    """Expose a :class:`Lucidia` instance through a REST API."""

    def __init__(self, lucidia: Lucidia, port: int = 8000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: List[Dict[str, Any]] = []

        @self.app.get("/health")
        def health() -> Dict[str, Any]:
            identity = getattr(self.lucidia, "identity", None)
            return {
                "status": "healthy",
                "lucidia_identity": getattr(identity, "current_hash", ""),
                "active_agents": len(self.active_agents),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        @self.app.post("/agent/register")
        def register(agent: Dict[str, Any]) -> Dict[str, Any]:
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
                "registered_at": datetime.now(UTC).isoformat(),
            }
            identity = getattr(self.lucidia, "identity", None)
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": getattr(identity, "current_hash", ""),
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            if agent_id not in self.active_agents:
                return JSONResponse(
                    status_code=404,
                    content={"error": "agent_not_registered"},
                )
            self.active_agents[agent_id][
                "last_heartbeat"
            ] = datetime.now(UTC).isoformat()
            metrics = payload.get("metrics", {})
            self.agent_metrics.setdefault(agent_id, {}).update(metrics)
            return {"status": "heartbeat_received"}

        @self.app.post("/knowledge/learn")
        def learn(data: Dict[str, Any]) -> Dict[str, Any]:
            content = data.get("content")
            if content is None:
                return JSONResponse(
                    status_code=400, content={"error": "content required"}
                )
            try:
                result = self.lucidia.learn(
                    prop_type=data.get("type"),
                    content=content,
                    confidence=data.get("confidence", 0.0),
                    context=data.get("metadata", {}).get("context", {}),
                    evidence=(
                        data.get("metadata", {}).get("evidence", [])
                        if isinstance(data.get("metadata"), dict)
                        else []
                    ),
                )
            except Exception as exc:  # pragma: no cover - simple error pass-through
                return JSONResponse(status_code=500, content={"error": str(exc)})

            event = {
                "timestamp": datetime.now(UTC).isoformat(),
                "agent_id": data.get("agent_id"),
                "content_hash": result.get("content_hash"),
                "confidence": data.get("confidence", 0.0),
                "type": data.get("type"),
            }
            self.learning_events.append(event)

            return {
                "status": "learned",
                **result,
                "confidence": data.get("confidence", 0.0),
            }

        @self.app.post("/knowledge/query")
        def query(data: Dict[str, Any]) -> Dict[str, Any]:
            result = self.lucidia.query(**data)
            return {
                "results": result.get("results", []),
                "count": len(result.get("results", [])),
                "query": data,
            }

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(data: Dict[str, Any]) -> Dict[str, Any]:
            fact_id = data.get("fact_id")
            new_conf = data.get("confidence")
            if fact_id is None or new_conf is None:
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
        def get_contradictions() -> Dict[str, Any]:
            raw = self.lucidia.get_contradictions()
            serialized: List[Dict[str, Any]] = []
            for c in raw:
                if isinstance(c, dict):
                    serialized.append(c)
                else:
                    serialized.append(
                        {
                            "id": getattr(c, "id", None),
                            "facts": [
                                getattr(f, "id", None) for f in getattr(c, "facts", [])
                            ],
                            "confidence": getattr(c, "confidence", None),
                            "status": getattr(c, "status", None),
                            "discovered_at": getattr(c, "discovered_at", None),
                            "metadata": getattr(c, "metadata", {}),
                        }
                    )
            return {"contradictions": serialized, "count": len(serialized)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(data: Dict[str, Any]) -> Dict[str, Any]:
            proposition = data.get("proposition")
            conflicting = data.get("conflicting_facts")
            if not proposition or not conflicting:
                return JSONResponse(
                    status_code=400,
                    content={"error": "proposition and conflicting_facts required"},
                )
            result = self.lucidia.quarantine_contradiction(
                proposition, conflicting, data.get("metadata", {})
            )
            return {"status": "quarantined", **result}

        @self.app.get("/identity/current")
        def identity_current() -> Dict[str, Any]:
            identity = getattr(self.lucidia, "identity", None)
            return {
                "current_hash": getattr(identity, "current_hash", ""),
                "chain_length": len(getattr(identity, "chain", [])),
                "continuity_events": (
                    identity.get_continuity_events()
                    if hasattr(identity, "get_continuity_events")
                    else []
                ),
            }

        @self.app.get("/telemetry/agents")
        def agent_telemetry() -> Dict[str, Any]:
            total_facts = (
                self.lucidia.get_fact_count()
                if hasattr(self.lucidia, "get_fact_count")
                else 0
            )
            contradictions = self.lucidia.get_contradictions()
            identity = getattr(self.lucidia, "identity", None)
            return {
                "active_agents": self.active_agents,
                "agent_metrics": self.agent_metrics,
                "recent_learning_events": self.learning_events,
                "system_stats": {
                    "total_facts": total_facts,
                    "active_contradictions": len(contradictions),
                    "identity_chain_length": len(getattr(identity, "chain", [])),
        self._setup_routes()

    # ------------------------------------------------------------------ routes
    def _setup_routes(self) -> None:
        app = self.app

        @app.get("/health")
        def health() -> Dict[str, Any]:
            return {
                "status": "healthy",
                "lucidia_identity": self.lucidia.identity.current_hash,
                "active_agents": len(self.active_agents),
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }

        @app.post("/agent/register")
        def register_agent(agent: Dict[str, Any]):
            if "agent_id" not in agent or "agent_type" not in agent:
                return JSONResponse(
                    {"error": "agent_id and agent_type required"}, status_code=400
                )
            agent_id = agent["agent_id"]
            self.active_agents[agent_id] = {
                "type": agent["agent_type"],
                "capabilities": agent.get("capabilities", []),
                "status": "active",
                "registered_at": datetime.now(tz=UTC).isoformat(),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": self.lucidia.identity.current_hash,
            }

        @app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, data: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse({"error": "agent_not_registered"}, status_code=404)
            metrics = data.get("metrics") or {}
            stored_metrics = deepcopy(metrics)
            self.agent_metrics[agent_id] = stored_metrics
            heartbeat_ts = datetime.now(tz=UTC).isoformat()
            self.active_agents[agent_id]["last_heartbeat"] = heartbeat_ts
            return {
                "status": "heartbeat_received",
                "agent_id": agent_id,
                "lucidia_identity": self.lucidia.identity.current_hash,
                "metrics": deepcopy(stored_metrics),
                "timestamp": heartbeat_ts,
            }

        @app.post("/knowledge/learn")
        def learn(data: Dict[str, Any]):
            if "content" not in data:
                return JSONResponse({"error": "content required"}, status_code=400)
            try:
                res = self.lucidia.learn(
                    prop_type=data.get("type"),
                    content=data["content"],
                    confidence=data.get("confidence", 0.0),
                    context=data.get("metadata", {}).get("context", {}),
                    evidence=data.get("metadata", {}).get("evidence", []),
                )
            except Exception as exc:  # pragma: no cover - exercised in tests
                return JSONResponse({"error": str(exc)}, status_code=500)
            event = {
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "agent_id": data.get("agent_id", ""),
                "content_hash": res["content_hash"],
                "confidence": data.get("confidence"),
                "type": data.get("type"),
            }
            self.learning_events.append(event)
            return {
                "status": "learned",
                "content_hash": res["content_hash"],
                "fact_id": res["fact_id"],
                "confidence": data.get("confidence"),
            }

        @app.post("/knowledge/query")
        def query(data: Dict[str, Any]):
            res = self.lucidia.query(
                content=data.get("content", ""),
                confidence=data.get("confidence"),
                limit=data.get("limit", 10),
            )
            results = res.get("results", [])
            return {"results": results, "count": len(results), "query": data}

        @app.post("/knowledge/update_confidence")
        def update_confidence(data: Dict[str, Any]):
            if "fact_id" not in data or "confidence" not in data:
                return JSONResponse(
                    {"error": "fact_id and confidence required"}, status_code=400
                )
            self.lucidia.update_confidence(data["fact_id"], data["confidence"])
            return {
                "status": "updated",
                "fact_id": data["fact_id"],
                "new_confidence": data["confidence"],
            }

        @app.get("/knowledge/contradictions")
        def get_contradictions():
            raw = self.lucidia.get_contradictions()
            contradictions = []
            for c in raw:
                if isinstance(c, dict):
                    contradictions.append(c)
                else:  # convert mock objects
                    facts = []
                    for f in getattr(c, "facts", []):
                        fid = getattr(f, "id", f)
                        facts.append({"id": fid})
                    contradictions.append(
                        {
                            "id": getattr(c, "id", None),
                            "facts": facts,
                            "confidence": getattr(c, "confidence", None),
                            "status": getattr(c, "status", None),
                            "discovered_at": getattr(c, "discovered_at", None),
                            "metadata": getattr(c, "metadata", None),
                        }
                    )
            return {"contradictions": contradictions, "count": len(contradictions)}

        @app.post("/knowledge/quarantine_contradiction")
        def quarantine(data: Dict[str, Any]):
            if "proposition" not in data or "conflicting_facts" not in data:
                return JSONResponse(
                    {"error": "proposition and conflicting_facts required"},
                    status_code=400,
                )
            res = self.lucidia.quarantine_contradiction(
                proposition=data["proposition"],
                conflicting_facts=data["conflicting_facts"],
                metadata=data.get("metadata"),
            )
            return {"status": "quarantined", **res}

        @app.get("/identity/current")
        def identity_current():
            ident = self.lucidia.identity
            return {
                "current_hash": ident.current_hash,
                "chain_length": len(ident.chain),
                "continuity_events": ident.get_continuity_events(),
            }

        @app.get("/telemetry/agents")
        def telemetry_agents():
            return {
                "active_agents": deepcopy(self.active_agents),
                "agent_metrics": deepcopy(self.agent_metrics),
                "recent_learning_events": deepcopy(self.learning_events),
                "system_stats": {
                    "total_facts": self.lucidia.get_fact_count(),
                    "active_contradictions": len(self.lucidia.get_contradictions()),
                    "identity_chain_length": len(self.lucidia.identity.chain),
                },
            }
