"""Base node class and registry for workflow nodes."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Type

from pydantic import BaseModel

from app.domain.models import ConversationState, Node, NodeIO


class BaseNode(ABC):
    """Abstract base class for all workflow nodes."""

    def __init__(self, node: Node) -> None:
        """Initialize the node with its configuration."""
        self.node = node
        self.config = node.config
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """Validate node configuration."""
        pass

    @abstractmethod
    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Convert node to a LangGraph-compatible function."""
        pass

    @abstractmethod
    def describe_io(self) -> NodeIO:
        """Document node inputs and outputs."""
        pass


class NodeRegistry:
    """Factory for creating node instances."""

    _registry: dict[str, type[BaseNode]] = {}

    @classmethod
    def register(cls, node_type: str, node_class: Type[BaseNode]) -> None:
        """Register a node type with its implementation class."""
        cls._registry[node_type] = node_class

    @classmethod
    def create(cls, node: Node) -> BaseNode:
        """Create a node instance from a node definition."""
        if node.type not in cls._registry:
            raise ValueError(f"Unknown node type: {node.type}")
        return cls._registry[node.type](node)

    @classmethod
    def get_registered_types(cls) -> Dict[str, Type[BaseNode]]:
        """Get all registered node types."""
        return cls._registry.copy()
