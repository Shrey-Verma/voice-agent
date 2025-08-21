"""Conditional routing helper for workflow edges."""

from typing import Any, Callable

import jmespath

from app.domain.models import ConversationState


def create_router(condition: str) -> Callable[[ConversationState], bool]:
    """Create a routing function from a condition string.
    
    Supports two formats:
    1. JMESPath expression that evaluates to boolean
    2. Simple equality check: variable == "value"
    
    Args:
        condition: Routing condition
        
    Returns:
        Function that evaluates condition on state
        
    Examples:
        >>> router = create_router("variables.age > 18")
        >>> router(state)  # True if age > 18
        
        >>> router = create_router("response == 'yes'")
        >>> router(state)  # True if response variable equals 'yes'
    """
    if "==" in condition:
        # Simple equality check
        var, value = condition.split("==")
        var = var.strip()
        value = value.strip().strip('"\'')
        
        def check_equality(state: ConversationState) -> bool:
            return state.variables.get(var) == value
        
        return check_equality
    else:
        # JMESPath expression
        expression = jmespath.compile(condition)
        
        def evaluate_expression(state: ConversationState) -> bool:
            # Convert state to dict for JMESPath
            state_dict = state.model_dump()
            result = expression.search(state_dict)
            
            if not isinstance(result, bool):
                raise ValueError(
                    f"Condition '{condition}' must evaluate to boolean, got: {type(result)}"
                )
            return result
        
        return evaluate_expression
