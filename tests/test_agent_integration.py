import pytest
from unittest.mock import patch


def test_agent_registration_updates_bridge(lucidia_bridge, test_client):
    """Registering an agent via the API should update the bridge's active_agents."""
    agent_data = {
        "agent_id": "integration-test-agent",
        "agent_type": "Curator",
        "capabilities": ["learning"]
    }
    response = test_client.post("/agent/register", json=agent_data)
    assert response.status_code == 200
    assert agent_data["agent_id"] in lucidia_bridge.active_agents
    assert lucidia_bridge.active_agents[agent_data["agent_id"]]["type"] == agent_data["agent_type"]


def test_agent_heartbeat_updates_metrics(lucidia_bridge, test_client):
    """Heartbeats should update agent metrics on the bridge."""
    agent_data = {
        "agent_id": "integration-heartbeat",
        "agent_type": "Analyzer"
    }
    # Register agent first
    test_client.post("/agent/register", json=agent_data)
    metrics = {"analysis_runs": 5, "quality_score": 0.9}
    res = test_client.post(
        f"/agent/{agent_data['agent_id']}/heartbeat",
        json={"metrics": metrics}
    )
    assert res.status_code == 200
    assert agent_data["agent_id"] in lucidia_bridge.agent_metrics
    for k, v in metrics.items():
        assert lucidia_bridge.agent_metrics[agent_data["agent_id"]][k] == v


def test_learning_event_recorded(lucidia_bridge, test_client, lucidia_core):
    """Learning a proposition via the API should record a learning event on the bridge."""
    initial_len = len(lucidia_bridge.learning_events)
    # Register curator agent
    agent_data = {
        "agent_id": "integration-curator",
        "agent_type": "Curator"
    }
    test_client.post("/agent/register", json=agent_data)
    proposition = {
        "type": "assertion",
        "content": "Integration test fact",
        "confidence": 0.9,
        "metadata": {"source": "integration_test"},
        "agent_id": agent_data["agent_id"]
    }
    # Mock the core learn method to control the returned IDs
    with patch.object(lucidia_core, 'learn') as mock_learn:
        mock_learn.return_value = {
            "content_hash": "hash_integration",
            "fact_id": "fact_integration"
        }
        res = test_client.post("/knowledge/learn", json=proposition)
        assert res.status_code == 200
        # Bridge should record a new learning event
        assert len(lucidia_bridge.learning_events) == initial_len + 1
        event = lucidia_bridge.learning_events[-1]
        assert event["agent_id"] == agent_data["agent_id"]
        assert event["content_hash"] == "hash_integration"
        assert event["confidence"] == proposition["confidence"]
        assert event["type"] == proposition["type"]
