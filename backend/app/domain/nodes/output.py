"""Output node implementation."""

from typing import Callable

from app.domain.models import ConversationState, Message, NodeIO
from app.domain.nodes.base import BaseNode
from app.utils.templating import render_template


class OutputNode(BaseNode):
    """Node that sends a final response and marks the conversation as done."""

    def validate(self) -> None:
        """Ensure text is present in config."""
        if "text" not in self.config:
            raise ValueError(f"Node {self.node.id} missing required 'text' config")

    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Create a function that adds a final message and marks done."""
        def output_fn(state: ConversationState) -> ConversationState:
            # Store user's response in variables
            if state.messages and state.messages[-1].role == "user":
                state.variables["name"] = state.messages[-1].content
            
            # Render template with current variables
            text = render_template(self.config["text"], state.variables)
            
            # Add message and mark done
            state.messages.append(Message(role="assistant", content=text))
            state.last_node = self.node.id
            state.done = True
            
            return state
        
        return output_fn

    def describe_io(self) -> NodeIO:
        """Document node I/O."""
        return NodeIO(
            inputs={
                "variables": "Current variable state for template rendering"
            },
            outputs={
                "message": "Final rendered message",
                "done": "True (conversation complete)"
            },
            description="Sends a final message and marks the conversation as complete"
        )
