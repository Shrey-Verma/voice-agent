"""Prompt node implementation."""

from typing import Callable

from app.domain.models import ConversationState, Message, NodeIO
from app.domain.nodes.base import BaseNode
from app.utils.templating import render_template


class PromptNode(BaseNode):
    """Node that sends a templated prompt to the user."""

    def validate(self) -> None:
        """Ensure text is present in config."""
        if "text" not in self.config:
            raise ValueError(f"Node {self.node.id} missing required 'text' config")

    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Create a function that adds an AI message to the conversation."""
        def prompt_fn(state: ConversationState) -> ConversationState:
            # If we have a user message, store it as user_input
            if state.messages and state.messages[-1].role == "user":
                state.variables["user_input"] = state.messages[-1].content
            
            # Render template with current variables
            text = render_template(self.config["text"], state.variables)
            
            # Add message to conversation
            state.messages.append(Message(role="assistant", content=text))
            state.last_node = self.node.id
            
            return state
        
        return prompt_fn

    def describe_io(self) -> NodeIO:
        """Document node I/O."""
        return NodeIO(
            inputs={
                "variables": "Current variable state for template rendering"
            },
            outputs={
                "message": "Rendered prompt message"
            },
            description="Sends a templated message to the user"
        )
