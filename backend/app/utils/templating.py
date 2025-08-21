"""Simple template rendering utility."""

import re
from typing import Any, Dict


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """Render a template string with variables.
    
    Args:
        template: String with {{variable}} placeholders
        variables: Dictionary of variable values
        
    Returns:
        Rendered string with variables replaced
        
    Example:
        >>> render_template("Hello {{name}}!", {"name": "Alice"})
        'Hello Alice!'
    """
    def replace(match: re.Match[str]) -> str:
        var_name = match.group(1).strip()
        if var_name not in variables:
            return match.group(0)  # Keep original placeholder if variable not found
        return str(variables[var_name])
    
    return re.sub(r"\{\{(.*?)\}\}", replace, template)
