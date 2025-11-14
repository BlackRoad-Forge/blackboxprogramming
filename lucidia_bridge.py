"""FastAPI bridge exposing a Lucidia core instance for the unit tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from lucidia_core import Lucidia


class LucidiaBridge:
    """Minimal FastAPI bridge exposing Lucidia core operations."""

    def __init__(self, lucidia: Lucidia, port: int = 8000) -> None:
        self.lucidia = lucidia
        self.port = port
        self.app = FastAPI()

        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.learning_events: List[Dict[str, Any]] = []

        self._setup_routes()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _context_from_metadata(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(metadata, dict):
            return dict(metadata.get("context", {}))
        return {}

    def _evidence_from_metadata(self, metadata: Optional[Dict[str, Any]]) -> List[Any]:
        if isinstance(metadata, dict):
            evidence = metadata.get("evidence", [])
            return list(evidence) if isinstance(evidence, list) else []
        return []

    @staticmethod
    def _serialise_fact(fact: Any) -> Dict[str, Any]:
        if isinstance(fact, dict):
            return dict(fact)
        return {"id": getattr(fact, "id", getattr(fact, "fact_id", None))}

    @classmethod
    def _serialise_contradiction(cls, item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            data = dict(item)
            facts_source = data.get("facts")
            if facts_source is None:
                facts_source = data.get("conflicting_facts", [])
            if isinstance(facts_source, (list, tuple)):
                data["facts"] = [cls._serialise_fact(fact) for fact in facts_source]
            else:
                data["facts"] = []
            data["id"] = data.get("id", data.get("contradiction_id"))
            metadata = data.get("metadata", {})
            data["metadata"] = dict(metadata) if isinstance(metadata, dict) else {}
            return data
        facts = [cls._serialise_fact(f) for f in getattr(item, "facts", [])]
        metadata = getattr(item, "metadata", {})
        metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
        return {
            "id": getattr(item, "id", None),
            "facts": facts,
            "confidence": getattr(item, "confidence", None),
            "status": getattr(item, "status", None),
            "discovered_at": getattr(item, "discovered_at", None),
            "metadata": metadata_dict,
        }

    def _setup_routes(self) -> None:
        @self.app.get("/health")
        def health() -> Dict[str, Any]:
            identity = getattr(self.lucidia, "identity", None)
            current_hash = getattr(identity, "current_hash", "")
            return {
                "status": "healthy",
                "lucidia_identity": current_hash,
                "active_agents": len(self.active_agents),
                "timestamp": self._timestamp(),
            }

        @self.app.post("/agent/register")
        def register_agent(agent: Dict[str, Any]):
            agent_id = agent.get("agent_id")
            agent_type = agent.get("agent_type")
            if not agent_id or not agent_type:
                return JSONResponse(
                    status_code=400, content={"error": "agent_id and agent_type required"}
                )
            self.active_agents[agent_id] = {
                "type": agent_type,
                "capabilities": agent.get("capabilities", []),
                "status": "active",
                "registered_at": self._timestamp(),
            }
            return {
                "status": "registered",
                "agent_id": agent_id,
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
            }

        @self.app.post("/agent/{agent_id}/heartbeat")
        def heartbeat(agent_id: str, payload: Dict[str, Any]):
            if agent_id not in self.active_agents:
                return JSONResponse(
                    status_code=404, content={"error": "agent_not_registered"}
                )
            timestamp = self._timestamp()
            self.active_agents[agent_id]["last_heartbeat"] = timestamp
            metrics = payload.get("metrics", {})
            if isinstance(metrics, dict):
                stored_metrics = deepcopy(metrics)
            else:
                stored_metrics = {}
            self.agent_metrics[agent_id] = stored_metrics
            response_metrics = deepcopy(stored_metrics)
            return {
                "status": "heartbeat_received",
                "agent_id": agent_id,
                "lucidia_identity": getattr(self.lucidia.identity, "current_hash", ""),
                "metrics": response_metrics,
                "timestamp": timestamp,
            }

        @self.app.post("/knowledge/learn")
        def learn(payload: Dict[str, Any]):
            content = payload.get("content")
            if content is None:
                return JSONResponse(status_code=400, content={"error": "content required"})
            metadata = payload.get("metadata")
            try:
                result = self.lucidia.learn(
                    prop_type=payload.get("type"),
                    content=content,
                    confidence=payload.get("confidence", 0.0),
                    context=self._context_from_metadata(metadata),
                    evidence=self._evidence_from_metadata(metadata),
                )
            except Exception as exc:  # pragma: no cover - defensive wrapper
                return JSONResponse(status_code=500, content={"error": str(exc)})

            event = {
                "timestamp": self._timestamp(),
                "agent_id": payload.get("agent_id"),
                "content_hash": result.get("content_hash"),
                "confidence": payload.get("confidence", 0.0),
                "type": payload.get("type"),
            }
            self.learning_events.append(event)
            return {"status": "learned", **result, "confidence": payload.get("confidence", 0.0)}

        @self.app.post("/knowledge/query")
        def query(payload: Dict[str, Any]):
            results = self.lucidia.query(**payload)
            count = len(results.get("results", []))
            return {**results, "count": count, "query": payload}

        @self.app.post("/knowledge/update_confidence")
        def update_confidence(payload: Dict[str, Any]):
            fact_id = payload.get("fact_id")
            new_confidence = payload.get("confidence")
            if fact_id is None or new_confidence is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "fact_id and confidence required"},
                )
            try:
                self.lucidia.update_confidence(fact_id, new_confidence)
            except KeyError as exc:
                return JSONResponse(status_code=404, content={"error": str(exc)})
            return {
                "status": "updated",
                "fact_id": fact_id,
                "new_confidence": new_confidence,
            }

        @self.app.get("/knowledge/contradictions")
        def get_contradictions():
            raw = self.lucidia.get_contradictions()
            serialised = [self._serialise_contradiction(item) for item in raw]
            return {"contradictions": serialised, "count": len(serialised)}

        @self.app.post("/knowledge/quarantine_contradiction")
        def quarantine(payload: Dict[str, Any]):
            proposition = payload.get("proposition")
            conflicting = payload.get("conflicting_facts")
            metadata = payload.get("metadata")
            if not proposition or not conflicting:
                return JSONResponse(
                    status_code=400,
                    content={"error": "proposition and conflicting_facts required"},
                )
            result = self.lucidia.quarantine_contradiction(
                proposition=proposition,
                conflicting_facts=list(conflicting),
                metadata=metadata,
            )
            return {"status": "quarantined", **result}

        @self.app.get("/identity/current")
        def current_identity() -> Dict[str, Any]:
            identity = getattr(self.lucidia, "identity", None)
            if identity is None:
                return JSONResponse(
                    status_code=404, content={"error": "identity_unavailable"}
                )
            chain = getattr(identity, "chain", [])
            events = []
            if hasattr(identity, "get_continuity_events"):
                events = deepcopy(identity.get_continuity_events())
            return {
                "current_hash": getattr(identity, "current_hash", ""),
                "chain_length": len(chain),
                "continuity_events": events,
            }

        @self.app.get("/telemetry/agents")
        def agent_telemetry() -> Dict[str, Any]:
            identity = getattr(self.lucidia, "identity", None)
            chain_length = len(getattr(identity, "chain", [])) if identity else 0
            total_facts = 0
            if hasattr(self.lucidia, "get_fact_count"):
                total_facts = self.lucidia.get_fact_count()
            contradictions = self.lucidia.get_contradictions()
            payload = {
                "active_agents": deepcopy(self.active_agents),
                "agent_metrics": deepcopy(self.agent_metrics),
                "recent_learning_events": deepcopy(self.learning_events),
                "system_stats": {
                    "total_facts": total_facts,
                    "active_contradictions": len(contradictions),
                    "identity_chain_length": chain_length,
                },
            }
            return payload


__all__ = ["LucidiaBridge"]
