"""Integration tests for workflow execution."""

import pytest

from app.core.engine import WorkflowEngine
from app.domain.models import Node, NodeType, Workflow


@pytest.fixture
def greeting_workflow() -> Workflow:
    """Create a simple greeting workflow."""
    return Workflow(
        id="test-greeting",
        name="Test Greeting",
        version=1,
        variables={},
        nodes=[
            Node(
                id="ask_name",
                type=NodeType.PROMPT,
                config={
                    "text": "Hi! What's your name?"
                },
                next="reply"
            ),
            Node(
                id="reply",
                type=NodeType.OUTPUT,
                config={
                    "text": "Thanks, {{name}}!"
                }
            )
        ]
    )


def test_workflow_execution(greeting_workflow: Workflow) -> None:
    """Test complete workflow execution."""
    # Create engine
    engine = WorkflowEngine(greeting_workflow)
    
    # Start workflow
    state = engine.start()
    
    # Check initial message
    assert len(state.messages) == 1
    assert state.messages[0].role == "assistant"
    assert state.messages[0].content == "Hi! What's your name?"
    assert state.last_node == "ask_name"
    assert not state.done
    
    # Step with user input
    state = engine.step(state, "Alice")
    
    # Check final message
    assert len(state.messages) == 3  # prompt + user + reply
    assert state.messages[-1].role == "assistant"
    assert state.messages[-1].content == "Thanks, Alice!"
    assert state.last_node == "reply"
    assert state.done
