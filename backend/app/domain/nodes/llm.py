"""LLM node implementation."""

from typing import Any, Callable, Dict, List

from app.domain.models import ConversationState, Message, NodeIO
from app.domain.nodes.base import BaseNode
from app.infra.llm.base import LLMClient
from app.utils.templating import render_template


class LLMNode(BaseNode):
    """Node that processes input through an LLM and extracts variables."""

    def validate(self) -> None:
        """Ensure required config is present."""
        required = {"prompt", "extract"}
        missing = required - self.config.keys()
        if missing:
            raise ValueError(
                f"Node {self.node.id} missing required config: {missing}"
            )
        
        if not isinstance(self.config["extract"], list):
            raise ValueError(
                f"Node {self.node.id} 'extract' config must be a list"
            )

    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Create a function that processes input through LLM."""
        def llm_fn(state: ConversationState) -> ConversationState:
            # Get last user message
            user_message = None
            for msg in reversed(state.messages):
                if msg.role == "user":
                    user_message = msg
                    break
            
            if not user_message:
                raise ValueError("LLM node requires a user message")
            
            # Render prompt template
            prompt = render_template(self.config["prompt"], {
                **state.variables,
                "user_input": user_message.content
            })
            
            # Get LLM client
            client = LLMClient.get_client()
            
            # Call LLM with JSON mode
            result = client.complete(
                prompt=prompt,
                system="Extract information from the user's message.",
                json_mode=True
            )
            
            # Extract variables
            if isinstance(result, dict):
                extracted: Dict[str, Any] = {}
                for field in self.config["extract"]:
                    if field in result:
                        extracted[field] = result[field]
                
                # Update state
                state.variables.update(extracted)
                
                # Add LLM response to messages
                state.messages.append(Message(
                    role="assistant",
                    content=extracted.get("response", str(result))
                ))
            
            state.last_node = self.node.id
            return state
        
        return llm_fn

    def describe_io(self) -> NodeIO:
        """Document node I/O."""
        extract_fields: List[str] = self.config.get("extract", [])
        
        return NodeIO(
            inputs={
                "user_input": "Last user message",
                "variables": "Current variables for template"
            },
            outputs={
                field: "Extracted from LLM response"
                for field in extract_fields
            },
            description="Processes input through LLM and extracts variables"
        )
