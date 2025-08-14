"""
Lucidia Testing Framework - Configuration and Fixtures

Provides comprehensive testing setup for:

- FastAPI endpoints testing
- Agent behavior testing
- Database layer testing
- Integration testing across components
- Mock external dependencies
"""

import pytest
import asyncio
import tempfile
import shutil
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import Lucidia components

from lucidia_core import Lucidia, Proposition, Evidence
from ps_sha_infinity import PS_SHA_Infinity
from lucidia_bridge import LucidiaBridge

# Test database setup

import sqlite3
import os

class TestConfig:
    """Test-specific configuration"""
    TESTING = True
    DATABASE_URL = "sqlite:///test_lucidia.db"
    BRIDGE_PORT = 5001  # Different from production
    LOG_LEVEL = "DEBUG"
    DISABLE_AUTH = True  # For testing
    MOCK_AI_RESPONSES = True

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for each test."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture(scope="function")
def mock_ps_sha_infinity():
    """Mock PS-SHA∞ identity for testing."""
    mock_identity = Mock(spec=PS_SHA_Infinity)
    mock_identity.current_hash = "test_hash_12345"
    mock_identity.chain = ["hash1", "hash2", "hash3"]
    mock_identity.get_continuity_events.return_value = []
    mock_identity.append_event.return_value = "new_hash"
    return mock_identity

@pytest.fixture(scope="function")
def lucidia_core(temp_db, mock_ps_sha_infinity):
    """Create a test Lucidia core instance."""
    with patch('lucidia_core.PS_SHA_Infinity', return_value=mock_ps_sha_infinity):
        core = Lucidia(database_url=f"sqlite:///{temp_db}")
        core.identity = mock_ps_sha_infinity
        yield core

@pytest.fixture(scope="function")
def lucidia_bridge(lucidia_core):
    """Create a test bridge instance."""
    bridge = LucidiaBridge(lucidia_core, port=TestConfig.BRIDGE_PORT)
    yield bridge

@pytest.fixture(scope="function")
def test_client(lucidia_bridge):
    """Create FastAPI test client."""
    client = TestClient(lucidia_bridge.app)
    yield client

@pytest.fixture(scope="function")
async def async_client(lucidia_bridge):
    """Create async test client."""
    async with AsyncClient(app=lucidia_bridge.app, base_url=f"http://localhost:{TestConfig.BRIDGE_PORT}") as ac:
        yield ac

@pytest.fixture(scope="function")
def sample_propositions():
    """Sample propositions for testing."""
    return [
        Proposition(
            type="assertion",
            content="The capital of France is Paris",
            confidence=0.95,
            context={"domain": "geography"},
            evidence=[
                Evidence(source="geography_textbook", weight=0.9, metadata={"page": 42})
            ],
        ),
        Proposition(
            type="assertion",
            content="Python is a programming language",
            confidence=0.99,
            context={"domain": "programming"},
            evidence=[
                Evidence(source="python_documentation", weight=0.95, metadata={"url": "https://python.org"})
            ],
        ),
        Proposition(
            type="assertion",
            content="Climate change affects global temperatures",
            confidence=0.88,
            context={"domain": "climate_science"},
            evidence=[
                Evidence(source="ipcc_report", weight=0.9, metadata={"year": 2023})
            ],
        ),
    ]

@pytest.fixture(scope="function")
def mock_agent_responses():
    """Mock responses from various agents."""
    return {
        "curator": {
            "status": "active",
            "metrics": {
                "facts_learned": 42,
                "contradictions_detected": 2,
                "sources_tracked": 8,
            },
        },
        "analyzer": {
            "status": "active",
            "metrics": {
                "analysis_runs": 15,
                "quality_score": 0.85,
                "gaps_identified": 3,
            },
        },
        "planner": {
            "status": "active",
            "metrics": {
                "reasoning_tasks": 7,
                "trees_generated": 12,
                "avg_confidence": 0.78,
            },
        },
    }

@pytest.fixture(scope="function")
def mock_ai_service():
    """Mock AI service responses."""
    mock_service = AsyncMock()
    # Standard responses for different types of queries
    mock_service.generate_response.return_value = {
        "response": "This is a test AI response",
        "confidence": 0.8,
        "sources": ["test_source_1", "test_source_2"],
    }
    mock_service.analyze_sentiment.return_value = {
        "sentiment": "neutral",
        "confidence": 0.7,
    }
    mock_service.extract_entities.return_value = [
        {"entity": "Paris", "type": "LOCATION", "confidence": 0.95},
        {"entity": "France", "type": "COUNTRY", "confidence": 0.98},
    ]
    return mock_service

# Test utilities

class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def create_test_fact(content: str, confidence: float = 0.8, domain: str = "test") -> dict:
        """Create a test fact object."""
        return {
            "type": "assertion",
            "content": content,
            "confidence": confidence,
            "context": {"domain": domain},
            "evidence": [
                {
                    "source": "test_source",
                    "weight": confidence,
                    "metadata": {"test": True},
                }
            ],
        }

    @staticmethod
    def create_test_query(content: str = None, confidence_min: float = None) -> dict:
        """Create a test query object."""
        query = {}
        if content:
            query["content"] = content
        if confidence_min:
            query["confidence"] = {"min": confidence_min}
        return query

    @staticmethod
    def assert_valid_response(response: dict, required_fields: list = None):
        """Assert that a response has valid structure."""
        assert isinstance(response, dict)
        assert "status" in response
        if required_fields:
            for field in required_fields:
                assert field in response, f"Missing required field: {field}"

    @staticmethod
    def assert_valid_fact(fact: dict):
        """Assert that a fact has valid structure."""
        required_fields = ["content", "confidence", "type"]
        for field in required_fields:
            assert field in fact, f"Missing required field: {field}"
        assert 0 <= fact["confidence"] <= 1, "Confidence must be between 0 and 1"
        assert isinstance(fact["content"], str), "Content must be string"

@pytest.fixture(scope="function")
def test_helpers():
    """Provide test helper methods."""
    return TestHelpers

# Database test utilities

@pytest.fixture(scope="function")
def db_with_sample_data(lucidia_core, sample_propositions):
    """Database populated with sample test data."""
    # Add sample propositions to the database
    for prop in sample_propositions:
        lucidia_core.learn(
            prop_type=prop.type,
            content=prop.content,
            confidence=prop.confidence,
            evidence=prop.evidence,
            context=prop.context,
        )
    yield lucidia_core

# Integration test fixtures

@pytest.fixture(scope="function")
async def running_bridge_server(lucidia_bridge):
    """Start bridge server for integration tests."""
    import threading
    import time
    # Start server in background thread
    server_thread = threading.Thread(target=lucidia_bridge.start_server, daemon=True)
    server_thread.start()
    # Wait for server to start
    time.sleep(0.5)
    yield lucidia_bridge
    # Server will stop when thread dies

# Mock external services

@pytest.fixture(scope="function")
def mock_external_apis():
    """Mock external API calls."""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        # Mock successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok", "data": []}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "created", "id": "test_id"}
        yield {"get": mock_get, "post": mock_post}

# Performance testing fixtures

@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing."""
    import time
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        def start(self):
            self.start_time = time.time()
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    return Timer()

# Error injection for testing error handling

@pytest.fixture(scope="function")
def error_injector():
    """Utility for injecting errors during tests."""
    class ErrorInjector:
        def __init__(self):
            self.active_errors = {}
        def inject_error(self, component: str, error_type: Exception, message: str = "Test error"):
            """Inject an error for a specific component."""
            self.active_errors[component] = (error_type, message)
        def should_raise_error(self, component: str):
            """Check if an error should be raised for a component."""
            if component in self.active_errors:
                error_type, message = self.active_errors[component]
                raise error_type(message)
        def clear_errors(self):
            """Clear all injected errors."""
            self.active_errors.clear()
    return ErrorInjector()

# Cleanup fixtures

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield
    # Clear any global state that might persist
    # Reset any singletons
    # Clear caches
    pass

# Test data generators

@pytest.fixture(scope="function")
def fact_generator():
    """Generate test facts on demand."""
    def _generate_facts(count: int = 1, domain: str = "test") -> list:
        facts = []
        for i in range(count):
            facts.append({
                "type": "assertion",
                "content": f"Test fact number {i} about {domain}",
                "confidence": 0.5 + (i % 5) * 0.1,  # Vary confidence
                "context": {"domain": domain, "test_id": i},
                "evidence": [{
                    "source": f"test_source_{i}",
                    "weight": 0.8,
                    "metadata": {"generated": True, "index": i},
                }],
            })
        return facts
    return _generate_facts

# Async test utilities

@pytest.fixture(scope="function")
def async_test_utils():
    """Utilities for async testing."""
    class AsyncTestUtils:
        @staticmethod
        async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
            """Wait for a condition to become true."""
            import asyncio
            start_time = asyncio.get_event_loop().time()
            while True:
                if condition_func():
                    return True
                if asyncio.get_event_loop().time() - start_time > timeout:
                    return False
                await asyncio.sleep(interval)
        @staticmethod
        async def collect_events(event_emitter, event_name: str, timeout: float = 1.0):
            """Collect events emitted during a time period."""
            events = []
            def handler(*args, **kwargs):
                events.append((args, kwargs))
            event_emitter.on(event_name, handler)
            import asyncio
            await asyncio.sleep(timeout)
            return events
    return AsyncTestUtils

if __name__ == "__main__":
    # Quick test to ensure fixtures work
    print("Lucidia Testing Framework - Configuration loaded successfully")
    print("Available fixtures:")
    print("- lucidia_core: Core Lucidia instance with test database")
    print("- lucidia_bridge: Bridge server for API testing")
    print("- test_client: FastAPI test client")
    print("- async_client: Async HTTP client")
    print("- sample_propositions: Test data")
    print("- mock_agent_responses: Mock agent data")
    print("- test_helpers: Utility methods")
    print("- And many more…")
