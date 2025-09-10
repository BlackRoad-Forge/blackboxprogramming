"""Comprehensive tests for Lucidia Bridge API endpoints."""

from unittest.mock import Mock, patch


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, test_client, lucidia_core):
        """Test successful health check."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "lucidia_identity" in data
        assert "active_agents" in data
        assert "timestamp" in data
        assert isinstance(data["active_agents"], int)

    def test_health_check_format(self, test_client):
        """Test health check response format."""
        response = test_client.get("/health")
        data = response.json()

        # Verify timestamp format
        from datetime import datetime

        timestamp = datetime.fromisoformat(data["timestamp"])
        assert timestamp is not None

        # Verify identity is string
        assert isinstance(data["lucidia_identity"], str)


class TestAgentManagement:
    """Test agent registration and management endpoints."""

    def test_agent_registration_success(self, test_client):
        """Test successful agent registration."""
        agent_data = {
            "agent_id": "test-curator-123",
            "agent_type": "Curator",
            "capabilities": ["learning", "deduplication", "evidence-merging"],
        }

        response = test_client.post("/agent/register", json=agent_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "registered"
        assert data["agent_id"] == agent_data["agent_id"]
        assert "lucidia_identity" in data

    def test_agent_registration_missing_fields(self, test_client):
        """Test agent registration with missing required fields."""
        # Missing agent_type
        response = test_client.post("/agent/register", json={"agent_id": "test-agent"})

        assert response.status_code == 400
        assert "agent_id and agent_type required" in response.json()["error"]

        # Missing agent_id
        response = test_client.post("/agent/register", json={"agent_type": "Curator"})

        assert response.status_code == 400

    def test_agent_heartbeat_success(self, test_client, lucidia_bridge):
        """Test successful agent heartbeat."""
        # First register agent
        agent_data = {
            "agent_id": "test-agent-heartbeat",
            "agent_type": "Analyzer",
            "capabilities": ["analysis"],
        }
        test_client.post("/agent/register", json=agent_data)

        # Send heartbeat
        heartbeat_data = {
            "metrics": {
                "analysis_runs": 5,
                "quality_score": 0.85,
                "nested": {"inner": 1},
            }
        }

        response = test_client.post(
            f"/agent/{agent_data['agent_id']}/heartbeat",
            json=heartbeat_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "heartbeat_received"
        assert data["agent_id"] == agent_data["agent_id"]
        assert data["lucidia_identity"] == lucidia_bridge.lucidia.identity.current_hash
        assert data["metrics"] == heartbeat_data["metrics"]
        assert (
            lucidia_bridge.agent_metrics[agent_data["agent_id"]]
            == heartbeat_data["metrics"]
        )
        assert (
            lucidia_bridge.agent_metrics[agent_data["agent_id"]]
            is not heartbeat_data["metrics"]
        )
        assert (
            lucidia_bridge.agent_metrics[agent_data["agent_id"]]["nested"]
            is not heartbeat_data["metrics"]["nested"]
        )
        heartbeat_data["metrics"]["analysis_runs"] = 10
        heartbeat_data["metrics"]["nested"]["inner"] = 2
        assert (
            lucidia_bridge.agent_metrics[agent_data["agent_id"]]["analysis_runs"] == 5
        )
        assert (
            lucidia_bridge.agent_metrics[agent_data["agent_id"]]["nested"]["inner"] == 1
        )
        assert "timestamp" in data
        assert (
            lucidia_bridge.active_agents[agent_data["agent_id"]]["last_heartbeat"]
            == data["timestamp"]
        )
        from datetime import datetime, timezone

        ts = datetime.fromisoformat(data["timestamp"])
        assert ts.tzinfo == timezone.utc

    def test_agent_heartbeat_unregistered(self, test_client):
        """Test heartbeat from unregistered agent."""
        response = test_client.post(
            "/agent/nonexistent-agent/heartbeat", json={"metrics": {}}
        )

        assert response.status_code == 404
        assert response.json()["error"] == "agent_not_registered"


class TestKnowledgeOperations:
    """Test knowledge learning, querying, and updating."""

    def test_learn_proposition_success(self, test_client, lucidia_core):
        """Test successful proposition learning."""
        proposition_data = {
            "type": "assertion",
            "content": "The capital of France is Paris",
            "confidence": 0.95,
            "metadata": {
                "source": "geography_textbook",
                "context": {"domain": "geography"},
            },
            "agent_id": "test-curator",
        }

        with patch.object(lucidia_core, "learn") as mock_learn:
            mock_learn.return_value = {"content_hash": "abc123", "fact_id": "fact_456"}

            response = test_client.post("/knowledge/learn", json=proposition_data)

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "learned"
            assert data["content_hash"] == "abc123"
            assert data["fact_id"] == "fact_456"
            assert data["confidence"] == 0.95

            # Verify learn was called correctly
            mock_learn.assert_called_once()
            call_args = mock_learn.call_args
            assert call_args[1]["prop_type"] == "assertion"
            assert call_args[1]["content"] == proposition_data["content"]
            assert call_args[1]["confidence"] == 0.95

    def test_learn_proposition_missing_content(self, test_client):
        """Test learning with missing content."""
        response = test_client.post(
            "/knowledge/learn", json={"type": "assertion", "confidence": 0.8}
        )

        assert response.status_code == 400
        assert "content required" in response.json()["error"]

    def test_query_knowledge_success(self, test_client, lucidia_core):
        """Test successful knowledge querying."""
        query_data = {"content": "France", "confidence": {"min": 0.5}, "limit": 10}

        mock_results = {
            "results": [
                {
                    "id": "fact_123",
                    "content": "France is a country in Europe",
                    "content_hash": "hash_123",
                    "confidence": 0.9,
                    "type": "assertion",
                    "timestamp": "2024-01-01T12:00:00",
                    "context": {"domain": "geography"},
                    "evidence": [
                        {
                            "source": "atlas",
                            "weight": 0.95,
                            "timestamp": "2024-01-01T12:00:00",
                            "metadata": {"page": 42},
                        }
                    ],
                }
            ]
        }

        with patch.object(lucidia_core, "query") as mock_query:
            mock_query.return_value = mock_results

            response = test_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            assert "count" in data
            assert "query" in data
            assert len(data["results"]) == 1
            assert data["count"] == 1
            assert data["query"] == query_data

            # Verify query structure
            result = data["results"][0]
            assert result["id"] == "fact_123"
            assert result["confidence"] == 0.9
            assert len(result["evidence"]) == 1

    def test_update_confidence_success(self, test_client, lucidia_core):
        """Test successful confidence update."""
        update_data = {
            "fact_id": "fact_123",
            "confidence": 0.85,
            "agent_id": "test-analyzer",
        }

        with patch.object(lucidia_core, "update_confidence") as mock_update:
            response = test_client.post(
                "/knowledge/update_confidence", json=update_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "updated"
            assert data["fact_id"] == "fact_123"
            assert data["new_confidence"] == 0.85

            mock_update.assert_called_once_with("fact_123", 0.85)

    def test_update_confidence_missing_fields(self, test_client):
        """Test confidence update with missing fields."""
        response = test_client.post(
            "/knowledge/update_confidence", json={"fact_id": "fact_123"}
        )

        assert response.status_code == 400
        assert "fact_id and confidence required" in response.json()["error"]


class TestContradictionManagement:
    """Test contradiction detection and management."""

    def test_get_contradictions_success(self, test_client, lucidia_core):
        """Test successful contradiction retrieval."""
        mock_contradictions = [
            Mock(
                id="contradiction_1",
                facts=[Mock(id="fact_1"), Mock(id="fact_2")],
                confidence=0.8,
                status="active",
                discovered_at="2024-01-01T12:00:00",
                metadata={"analysis_method": "semantic_similarity"},
            )
        ]

        # Convert Mock to dict for JSON serialization
        mock_contradictions[0].discovered_at = "2024-01-01T12:00:00"

        with patch.object(lucidia_core, "get_contradictions") as mock_get:
            mock_get.return_value = mock_contradictions

            response = test_client.get("/knowledge/contradictions")

            assert response.status_code == 200
            data = response.json()

            assert "contradictions" in data
            assert "count" in data
            assert data["count"] == 1
            assert len(data["contradictions"]) == 1

            contradiction = data["contradictions"][0]
            assert contradiction["id"] == "contradiction_1"
            assert len(contradiction["facts"]) == 2
            assert contradiction["confidence"] == 0.8

    def test_quarantine_contradiction_success(self, test_client, lucidia_core):
        """Test successful contradiction quarantine."""
        quarantine_data = {
            "proposition": {
                "type": "assertion",
                "content": "The capital of France is Lyon",
                "confidence": 0.6,
            },
            "conflicting_facts": ["fact_123", "fact_456"],
            "metadata": {"detection_method": "curator_agent", "conflict_strength": 0.9},
        }

        with patch.object(lucidia_core, "quarantine_contradiction") as mock_quarantine:
            mock_quarantine.return_value = {"contradiction_id": "new_contradiction_789"}

            response = test_client.post(
                "/knowledge/quarantine_contradiction", json=quarantine_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "quarantined"
            assert data["contradiction_id"] == "new_contradiction_789"

            mock_quarantine.assert_called_once()

    def test_quarantine_contradiction_missing_fields(self, test_client):
        """Test quarantine with missing required fields."""
        response = test_client.post(
            "/knowledge/quarantine_contradiction",
            json={"proposition": {"content": "test"}},
        )

        assert response.status_code == 400
        assert "proposition and conflicting_facts required" in response.json()["error"]


class TestIdentityOperations:
    """Test PS-SHA\u221e identity operations."""

    def test_get_current_identity_success(self, test_client, mock_ps_sha_infinity):
        """Test successful identity retrieval."""
        mock_ps_sha_infinity.get_continuity_events.return_value = [
            {"event": "system_start", "timestamp": "2024-01-01T00:00:00"},
            {"event": "learning_session", "timestamp": "2024-01-01T12:00:00"},
        ]

        response = test_client.get("/identity/current")

        assert response.status_code == 200
        data = response.json()

        assert "current_hash" in data
        assert "chain_length" in data
        assert "continuity_events" in data
        assert data["current_hash"] == "test_hash_12345"
        assert data["chain_length"] == 3
        assert len(data["continuity_events"]) == 2


class TestTelemetryOperations:
    """Test system telemetry and monitoring."""

    def test_get_agent_telemetry_success(self, test_client, lucidia_bridge):
        """Test successful telemetry retrieval."""
        # Setup bridge state
        lucidia_bridge.active_agents = {
            "test-agent-1": {
                "type": "Curator",
                "status": "active",
                "registered_at": "2024-01-01T12:00:00",
                "last_heartbeat": "2024-01-01T12:30:00",
            }
        }

        lucidia_bridge.agent_metrics = {
            "test-agent-1": {"facts_learned": 25, "quality_score": 0.87}
        }

        lucidia_bridge.learning_events = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "agent_id": "test-agent-1",
                "content_hash": "hash_123",
                "confidence": 0.9,
                "type": "assertion",
            }
        ]

        with patch.object(
            lucidia_bridge.lucidia, "get_fact_count"
        ) as mock_count, patch.object(
            lucidia_bridge.lucidia, "get_contradictions"
        ) as mock_contradictions:

            mock_count.return_value = 150
            mock_contradictions.return_value = []

            response = test_client.get("/telemetry/agents")

            assert response.status_code == 200
            data = response.json()

            assert "active_agents" in data
            assert "agent_metrics" in data
            assert "recent_learning_events" in data
            assert "system_stats" in data

            # Verify system stats
            assert data["system_stats"]["total_facts"] == 150
            assert data["system_stats"]["active_contradictions"] == 0
            assert data["system_stats"]["identity_chain_length"] == 3

            # Verify agent data
            assert "test-agent-1" in data["active_agents"]
            assert data["active_agents"]["test-agent-1"]["type"] == "Curator"


class TestErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON in requests."""
        response = test_client.post(
            "/knowledge/learn",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_database_error_handling(self, test_client, lucidia_core):
        """Test handling of database errors."""
        with patch.object(lucidia_core, "learn") as mock_learn:
            mock_learn.side_effect = Exception("Database connection failed")

            response = test_client.post(
                "/knowledge/learn",
                json={
                    "type": "assertion",
                    "content": "Test content",
                    "confidence": 0.8,
                },
            )

            assert response.status_code == 500
            assert "error" in response.json()

    def test_large_request_handling(self, test_client):
        """Test handling of very large requests."""
        large_content = "x" * 10000  # 10KB content

        response = test_client.post(
            "/knowledge/learn",
            json={"type": "assertion", "content": large_content, "confidence": 0.8},
        )

        # Should handle large requests gracefully
        assert response.status_code in [200, 413, 422]  # Success or appropriate error
