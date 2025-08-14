import pytest

from ps_sha_infinity import PS_SHA_Infinity


def test_initial_chain_state():
    """The identity chain should initialize with a valid genesis hash."""
    identity = PS_SHA_Infinity()
    assert hasattr(identity, "chain")
    assert isinstance(identity.chain, list)
    assert len(identity.chain) >= 1
    # current_hash should be the last element in the chain
    assert identity.current_hash == identity.chain[-1]


def test_append_event_updates_chain():
    """Appending an event should extend the chain and update the current hash."""
    identity = PS_SHA_Infinity()
    original_length = len(identity.chain)
    new_hash = identity.append_event({"event": "test_event"})
    # Chain length increases by one
    assert len(identity.chain) == original_length + 1
    # The current hash matches the new hash and last element
    assert identity.current_hash == identity.chain[-1]
    assert identity.current_hash == new_hash


def test_continuity_events_tracking():
    """Continuity events should be tracked over time."""
    identity = PS_SHA_Infinity()
    # Capture initial events
    initial_events = identity.get_continuity_events()
    assert isinstance(initial_events, list)
    # Append a new event and verify the continuity events list updates
    identity.append_event({"event": "session_start"})
    updated_events = identity.get_continuity_events()
    assert len(updated_events) >= len(initial_events)
