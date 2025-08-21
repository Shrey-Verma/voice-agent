"""OpenAI API client implementation."""

import json
from typing import Any, Optional, Union

from openai import OpenAI
from openai.types.chat.completion_create_params import ResponseFormat

from app.infra.llm.base_client import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""

    def __init__(self, api_key: str) -> None:
        """Initialize with API key."""
        self.client = OpenAI(api_key=api_key)

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False
    ) -> Union[str, dict[str, Any]]:
        """Complete a prompt using OpenAI API."""
        messages = []
        
        # Add system message if provided
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        # Add user prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Call API
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or other model
            messages=messages,
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
            temperature=0 if json_mode else 0.7
        )
        
        # Get response content
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI API")
        
        # Parse JSON if requested
        if json_mode:
            return json.loads(content)
        
        return content