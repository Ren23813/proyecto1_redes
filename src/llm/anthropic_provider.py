"""
Proveedor: API de Anthropic (SDK oficial).
Aquí sí se usa SDK, porque el enunciado solo lo prohíbe en el uso directo de MCP. 
"""
from typing import Dict, List

from anthropic import Anthropic

from src.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def complete(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text")
