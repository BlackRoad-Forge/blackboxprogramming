import pytest


def test_learn_and_query_basic(lucidia_core):
    """Test that learning and querying returns correct results."""
    # Learn a simple fact
    result = lucidia_core.learn(
        prop_type="assertion",
        content="The sky is blue",
        confidence=0.9,
        context={"domain": "common_sense"},
        evidence=[],
    )
    assert result.get("content_hash")
    assert result.get("fact_id")

    # Query for the content we just learned
    query_res = lucidia_core.query(
        content="sky",
        confidence={"min": 0.5},
        limit=5
    )
    assert "results" in query_res
    assert any(
        fact["content"] == "The sky is blue"
        for fact in query_res["results"]
    )


def test_update_confidence(lucidia_core):
    """Test that updating confidence modifies the stored fact."""
    # Learn a fact
    learn_res = lucidia_core.learn(
        prop_type="assertion",
        content="Water boils at 100C",
        confidence=0.5,
        context={"domain": "physics"},
        evidence=[],
    )
    fact_id = learn_res["fact_id"]

    # Update confidence
    new_confidence = 0.8
    lucidia_core.update_confidence(fact_id, new_confidence)

    # Query and check updated confidence
    query_res = lucidia_core.query(
        content="Water boils",
        confidence={"min": 0.0},
        limit=5
    )
    # find our fact
    fact = next(
        (f for f in query_res["results"] if f["id"] == fact_id),
        None
    )
    assert fact is not None
    assert abs(fact["confidence"] - new_confidence) < 1e-6


def test_contradiction_handling(lucidia_core):
    """Test that contradictions can be detected and quarantined."""
    # Learn two contradictory statements
    res1 = lucidia_core.learn(
        prop_type="assertion",
        content="The earth is flat",
        confidence=0.3,
        context={"domain": "science"},
        evidence=[],
    )
    res2 = lucidia_core.learn(
        prop_type="assertion",
        content="The earth is spherical",
        confidence=0.9,
        context={"domain": "science"},
        evidence=[],
    )

    # Check if contradictions exist
    contradictions = lucidia_core.get_contradictions()
    assert isinstance(contradictions, (list, tuple))

    # Quarantine one of the contradictory propositions
    proposition = {
        "type": "assertion",
        "content": "The earth is flat",
        "confidence": 0.3
    }
    conflicting = [res2["fact_id"]]
    quarantine_res = lucidia_core.quarantine_contradiction(
        proposition=proposition,
        conflicting_facts=conflicting,
        metadata={"test": True}
    )
    assert "contradiction_id" in quarantine_res


def test_invalid_learn_inputs(lucidia_core):
    """Test that invalid inputs to learn raise an exception."""
    with pytest.raises(Exception):
        lucidia_core.learn(
            prop_type="assertion",
            content=None,
            confidence=0.5,
            context={},
            evidence=[]
        )
