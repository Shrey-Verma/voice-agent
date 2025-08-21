"""LLM client factory."""

from typing import Optional

from app.core.settings import get_settings
from app.infra.llm.base_client import BaseLLMClient
from app.infra.llm.openai_client import OpenAIClient


class LLMClient:
    """Factory for LLM clients."""

    _instance: Optional[BaseLLMClient] = None

    @classmethod
    def get_client(cls) -> BaseLLMClient:
        """Get or create LLM client instance."""
        if cls._instance is None:

            
            settings = get_settings()
            cls._instance = OpenAIClient(str(settings.openai_api_key))
        
        return cls._instance

    @classmethod
    def set_client(cls, client: BaseLLMClient) -> None:
        """Set a custom client (useful for testing)."""
        cls._instance = client