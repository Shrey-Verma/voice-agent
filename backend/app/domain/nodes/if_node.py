"""Conditional branching node implementation."""

from typing import Callable, Optional

from app.core.router import create_router
from app.domain.models import ConversationState, NodeIO
from app.domain.nodes.base import BaseNode


class IfNode(BaseNode):
    """Node that evaluates a condition and routes to different targets."""

    def validate(self) -> None:
        """Ensure required config is present."""
        required = {"condition", "true_target", "false_target"}
        missing = required - self.config.keys()
        if missing:
            raise ValueError(
                f"Node {self.node.id} missing required config: {missing}"
            )

    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Create a function that evaluates condition and updates next node."""
        router = create_router(self.config["condition"])
        
        def if_fn(state: ConversationState) -> ConversationState:
            # Evaluate condition
            result = router(state)
            
            # Set next node based on result
            next_node = (
                self.config["true_target"]
                if result
                else self.config["false_target"]
            )
            
            # Update state
            state.last_node = self.node.id
            state.variables["_next"] = next_node
            
            return state
        
        return if_fn

    def describe_io(self) -> NodeIO:
        """Document node I/O."""
        return NodeIO(
            inputs={
                "variables": "Variables used in condition"
            },
            outputs={
                "_next": "ID of next node based on condition"
            },
            description=(
                f"Routes to {self.config.get('true_target')} if "
                f"{self.config.get('condition')} is true, else to "
                f"{self.config.get('false_target')}"
            )
        )
