"""Unit tests for workflow nodes."""

import pytest

from app.domain.models import ConversationState, Message, Node, NodeType
from app.domain.nodes.base import NodeRegistry
from app.domain.nodes.prompt import PromptNode
from app.domain.nodes.output import OutputNode


@pytest.fixture(autouse=True)
def setup_nodes():
    """Register node types before each test."""
    # Register using the enum values
    NodeRegistry.register(NodeType.PROMPT.value, PromptNode)
    NodeRegistry.register(NodeType.OUTPUT.value, OutputNode)


def test_prompt_node() -> None:
    """Test prompt node behavior."""
    # Create node
    node = Node(
        id="test",
        type=NodeType.PROMPT,
        config={
            "text": "Hello {{name}}!"
        }
    )
    
    # Create instance
    prompt_node = PromptNode(node)
    
    # Create state
    state = ConversationState(
        variables={"name": "Alice"}
    )
    
    # Run node
    result = prompt_node.to_graph_fn()(state)
    
    # Check results
    assert len(result.messages) == 1
    assert result.messages[0].role == "assistant"
    assert result.messages[0].content == "Hello Alice!"
    assert result.last_node == "test"


def test_output_node() -> None:
    """Test output node behavior."""
    # Create node
    node = Node(
        id="test",
        type=NodeType.OUTPUT,
        config={
            "text": "Goodbye {{name}}!"
        }
    )
    
    # Create instance
    output_node = OutputNode(node)
    
    # Create state
    state = ConversationState(
        variables={"name": "Alice"}
    )
    
    # Run node
    result = output_node.to_graph_fn()(state)
    
    # Check results
    assert len(result.messages) == 1
    assert result.messages[0].role == "assistant"
    assert result.messages[0].content == "Goodbye Alice!"
    assert result.last_node == "test"
    assert result.done is True


def test_node_registry() -> None:
    """Test node registry factory."""
    # Register nodes
    NodeRegistry.register("Prompt", PromptNode)
    NodeRegistry.register("Output", OutputNode)
    
    # Create node
    node = Node(
        id="test",
        type=NodeType.PROMPT,
        config={
            "text": "Hello!"
        }
    )
    
    # Create instance
    instance = NodeRegistry.create(node)
    
    # Check type
    assert isinstance(instance, PromptNode)
    
    # Check error for unknown type
    with pytest.raises(ValueError):
        NodeRegistry.create(Node(
            id="test",
            type="Unknown",  # type: ignore
            config={}
        ))
