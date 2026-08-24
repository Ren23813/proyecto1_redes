"""
Proveedor: modelo local vía Ollama, con soporte de tool-calling.

Formato de Ollama (para referencia, distinto al de Anthropic):
- Se manda `tools=[{"type":"function","function":{"name","description",
  "parameters"}}, ...]` (estilo OpenAI).
- Si el modelo quiere usar una tool, `message.tool_calls` trae una lista
  de `{"function": {"name", "arguments"}}` (arguments ya viene como dict,
  no como string JSON). No trae un "id" por llamada.
- Se responde agregando el mensaje del assistant tal cual (incluye
  tool_calls), y por cada tool_call un mensaje `{"role":"tool",
  "content": resultado}`.
"""
from typing import Callable, Dict, List, Optional

import requests

from src.interaction_logger import InteractionLogger
from src.llm.base import LLMProvider
from src.llm.types import MAX_TOOL_ITERATIONS, ToolCall, ToolSpec


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, logger: InteractionLogger, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.logger = logger

    def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolSpec]] = None,
        tool_executor: Optional[Callable[[ToolCall], str]] = None,
        max_tokens: int = 1024,
    ) -> str:
        ollama_tools = (
            [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": t.input_schema},
                }
                for t in tools
            ]
            if tools
            else None
        )

        conversation = list(messages)  # copia local; solo vive durante este turno

        for iteration in range(MAX_TOOL_ITERATIONS):
            payload = {
                "model": self.model,
                "messages": conversation,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
            if ollama_tools:
                payload["tools"] = ollama_tools

            self.logger.log("request", "llm", payload, method=f"chat (iter {iteration})")

            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            message = data["message"]

            self.logger.log("response", "llm", message, method=f"chat (iter {iteration})")

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return message.get("content", "")

            if tool_executor is None:
                return "[El modelo pidió usar una tool, pero no hay tool_executor configurado.]"

            conversation.append(message)

            for raw_call in tool_calls:
                fn = raw_call["function"]
                call = ToolCall(name=fn["name"], arguments=fn.get("arguments", {}))
                result_text = tool_executor(call)
                conversation.append({"role": "tool", "content": result_text})

        return "[El modelo excedió el número máximo de llamadas a herramientas permitidas.]"
