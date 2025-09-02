"""
Lucidia Backend API Skeleton

This module defines the FastAPI application for the Lucidia backend service.
It provides basic endpoints for submitting questions, adding facts, querying
the knowledge base, and monitoring agent status. This skeleton is intended
as a starting point for incremental development of the full Lucidia system.
"""

# isort: skip_file
import hashlib
import os
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Generator, List, Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# isort: off
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)

# isort: on
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lucidia:lucidiapassword@postgres:5432/lucidia",  # pragma: allowlist secret
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FactORM(Base):
    """SQLAlchemy model representing a fact."""

    __tablename__ = "facts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_hash = Column(String(64), unique=True)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    fact_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    evidence = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)


class ReasoningTreeORM(Base):
    """SQLAlchemy model representing a reasoning tree."""

    __tablename__ = "reasoning_trees"
    id = Column(String, primary_key=True)
    goal = Column(Text, nullable=False)
    strategy = Column(String(100))
    nodes = Column(JSON)
    conclusion = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AgentMetricORM(Base):
    """SQLAlchemy model representing agent metrics."""

    __tablename__ = "agent_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False)
    metrics_data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# Create tables if they do not exist
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def compute_hash(content: str) -> str:
    """Compute an MD5 hash of the content for deduplication."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts messages to them.
    """

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                # If sending fails, drop the connection silently
                self.disconnect(connection)


manager = ConnectionManager()


class FactCreate(BaseModel):
    """Model for creating a new fact."""

    content: str = Field(..., description="The textual content of the fact.")
    confidence: Optional[float] = Field(
        1.0, description="Confidence score between 0 and 1."
    )
    evidence: Optional[Dict[str, Any]] = Field(
        None, description="Optional evidence metadata for the fact."
    )


class Fact(BaseModel):
    """Representation of a fact stored in the knowledge base."""

    id: uuid.UUID
    content: str
    confidence: float
    evidence: Optional[Dict[str, Any]] = None
    created_at: datetime


class AskRequest(BaseModel):
    """Request model for submitting a question for reasoning."""

    question: str = Field(..., description="The question to ask the system.")


class AskResponse(BaseModel):
    """Response model for a question submission."""

    question: str
    answer: str
    reasoning_tree: Optional[Dict[str, Any]] = None
    timestamp: datetime


class AgentStatus(BaseModel):
    """Represents the status of a single agent."""

    name: str
    active: bool
    tasks_processed: int
    last_active: Optional[datetime] = None


class AgentsStatusResponse(BaseModel):
    """Response model for agent status monitoring."""

    agents: List[AgentStatus]
    timestamp: datetime


app = FastAPI(title="Lucidia Backend API", version="0.1.0")

# Allow all origins for simplicity; adjust in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend dashboard as static files. This allows users to navigate
# directly to the root URL and access the dashboard. The directory is
# calculated relative to this file to ensure correct resolution whether the
# app is run via Docker or locally.
frontend_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend"
)
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

# Agent metrics are kept in memory and can be extended to persist in the database
AGENT_METRICS: Dict[str, Dict[str, Any]] = {
    "curator": {"tasks_processed": 0},
    "analyzer": {"tasks_processed": 0},
    "planner": {"tasks_processed": 0},
    "bridge": {"tasks_processed": 0},
    "identity_keeper": {"tasks_processed": 0},
    "explainer": {"tasks_processed": 0},
}


@app.post("/api/v1/learn", response_model=Fact)
def add_fact(fact_in: FactCreate, db: Session = Depends(get_db)) -> Fact:
    """Add a new fact to the knowledge base.

    Stores the fact in the PostgreSQL database. If a fact with the same
    content hash already exists, the existing record is returned.
    """
    content_hash = compute_hash(fact_in.content)
    # Check for duplicate fact
    existing = db.query(FactORM).filter(FactORM.content_hash == content_hash).first()
    if existing:
        return Fact(
            id=uuid.UUID(existing.id),
            content=existing.content,
            confidence=existing.confidence,
            evidence=existing.evidence,
            created_at=existing.created_at,
        )
    # Create and persist new fact
    new_fact_id = str(uuid.uuid4())
    fact_record = FactORM(
        id=new_fact_id,
        content_hash=content_hash,
        content=fact_in.content,
        confidence=fact_in.confidence if fact_in.confidence is not None else 1.0,
        evidence=fact_in.evidence,
        context=None,
    )
    db.add(fact_record)
    db.commit()
    db.refresh(fact_record)
    # Record curator metric
    AGENT_METRICS["curator"]["tasks_processed"] += 1
    return Fact(
        id=uuid.UUID(fact_record.id),
        content=fact_record.content,
        confidence=fact_record.confidence,
        evidence=fact_record.evidence,
        created_at=fact_record.created_at,
    )


@app.get("/api/v1/knowledge", response_model=List[Fact])
def get_knowledge(
    limit: Optional[int] = 100, db: Session = Depends(get_db)
) -> List[Fact]:
    """Retrieve facts from the knowledge base.

    Queries the PostgreSQL database for facts and returns up to `limit` results.
    """
    records = db.query(FactORM).order_by(FactORM.created_at.desc()).limit(limit).all()
    return [
        Fact(
            id=uuid.UUID(rec.id),
            content=rec.content,
            confidence=rec.confidence,
            evidence=rec.evidence,
            created_at=rec.created_at,
        )
        for rec in records
    ]


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask_question(req: AskRequest, db: Session = Depends(get_db)) -> AskResponse:
    """Submit a question for reasoning.

    Forwards the question to the planner service via HTTP, stores the
    resulting reasoning tree in the database, updates metrics, and
    broadcasts the result to connected WebSocket clients.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")
    # Forward the question to the planner service
    planner_url = os.getenv("PLANNER_URL", "http://planner:3000/plan")
    try:
        planner_resp = requests.post(
            planner_url, json={"question": question, "context": {}}
        )
        planner_resp.raise_for_status()
        planner_result = planner_resp.json()
    except Exception as ex:
        raise HTTPException(
            status_code=502, detail=f"Planner service unavailable: {ex}"
        )
    # Persist the reasoning tree
    tree_id = planner_result.get("id", str(uuid.uuid4()))
    reasoning_record = ReasoningTreeORM(
        id=tree_id,
        goal=question,
        strategy=planner_result.get("strategy"),
        nodes=planner_result.get("nodes"),
        conclusion=planner_result,
        confidence=planner_result.get("confidence"),
    )
    db.add(reasoning_record)
    db.commit()
    # Update planner metrics
    AGENT_METRICS["planner"]["tasks_processed"] += 1
    # Build response for the API caller
    answer_text = (
        planner_result.get("answer")
        or planner_result.get("conclusion", {}).get("answer")
        or "No answer returned."
    )
    response = AskResponse(
        question=question,
        answer=answer_text,
        reasoning_tree=planner_result,
        timestamp=datetime.now(UTC),
    )
    # Broadcast the reasoning result via WebSocket
    await manager.broadcast(
        {
            "type": "reasoning_complete",
            "data": response.dict(),
        }
    )
    return response


@app.get("/api/v1/agents/status", response_model=AgentsStatusResponse)
def get_agent_status() -> AgentsStatusResponse:
    """Get status information for all agents.

    This endpoint returns basic metrics for each agent. In a more advanced
    implementation, this data could come from a monitoring subsystem.
    """
    agents_status = []
    for name, metrics in AGENT_METRICS.items():
        agents_status.append(
            AgentStatus(
                name=name,
                active=True if metrics.get("tasks_processed", 0) >= 0 else False,
                tasks_processed=metrics.get("tasks_processed", 0),
                last_active=datetime.now(UTC),
            )
        )
    return AgentsStatusResponse(agents=agents_status, timestamp=datetime.now(UTC))


@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket) -> None:
    """WebSocket endpoint to push real-time updates to clients.

    Clients connecting to this endpoint will receive JSON messages whenever
    reasoning completes or other events are triggered. The server does not
    currently process incoming messages from the client, but could be
    extended to support ping/pong or specific client commands.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message from the client; ignore its contents.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
