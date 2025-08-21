"""Variable manipulation node implementation."""

from typing import Any, Callable, Dict

import jmespath

from app.domain.models import ConversationState, NodeIO
from app.domain.nodes.base import BaseNode


class SetVarNode(BaseNode):
    """Node that sets variables from expressions."""

    def validate(self) -> None:
        """Ensure required config is present."""
        if "variables" not in self.config:
            raise ValueError(
                f"Node {self.node.id} missing required 'variables' config"
            )
        
        if not isinstance(self.config["variables"], dict):
            raise ValueError(
                f"Node {self.node.id} 'variables' config must be a dictionary"
            )

    def to_graph_fn(self) -> Callable[[ConversationState], ConversationState]:
        """Create a function that sets variables from expressions."""
        # Pre-compile expressions
        expressions: Dict[str, Any] = {}
        for var_name, expr in self.config["variables"].items():
            if isinstance(expr, str):
                # JMESPath expression
                expressions[var_name] = jmespath.compile(expr)
            else:
                # Static value
                expressions[var_name] = expr
        
        def setvar_fn(state: ConversationState) -> ConversationState:
            # Convert state to dict for JMESPath
            state_dict = state.model_dump()
            
            # Evaluate each expression
            for var_name, expr in expressions.items():
                if isinstance(expr, jmespath.parser.ParsedResult):
                    # JMESPath expression
                    value = expr.search(state_dict)
                else:
                    # Static value
                    value = expr
                
                # Update state
                state.variables[var_name] = value
            
            state.last_node = self.node.id
            return state
        
        return setvar_fn

    def describe_io(self) -> NodeIO:
        """Document node I/O."""
        return NodeIO(
            inputs={
                "variables": "Current variables for expressions"
            },
            outputs={
                var_name: f"Set from {expr}"
                for var_name, expr in self.config.get("variables", {}).items()
            },
            description="Sets variables from expressions or static values"
        )
