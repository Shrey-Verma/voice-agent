"""Base LLM client interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False
    ) -> Union[str, dict[str, Any]]:
        """Complete a prompt with optional system message.
        
        Args:
            prompt: The user prompt
            system: Optional system message
            json_mode: Whether to return structured JSON
            
        Returns:
            String response or JSON object if json_mode=True
        """
        pass
