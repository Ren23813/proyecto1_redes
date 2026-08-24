"""
Proveedor: API de Anthropic (SDK oficial), con soporte de tool-calling.

Formato de Anthropic (para referencia):
- Se manda `tools=[{"name","description","input_schema"}, ...]`.
- Si el modelo quiere usar una tool, `response.stop_reason == "tool_use"`
  y `response.content` trae uno o más bloques `{"type":"tool_use","id",
  "name","input"}` (puede venir junto con texto).
- Se responde agregando el turno del assistant tal cual, y un turno de
  usuario con bloques `{"type":"tool_result","tool_use_id","content"}`,
  uno por cada tool_use que se haya recibido.
"""
from typing import Callable, Dict, List, Optional

from anthropic import Anthropic

from src.interaction_logger import InteractionLogger
from src.llm.base import LLMProvider
from src.llm.types import MAX_TOOL_ITERATIONS, ToolCall, ToolSpec


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, logger: InteractionLogger):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = logger

    def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolSpec]] = None,
        tool_executor: Optional[Callable[[ToolCall], str]] = None,
        max_tokens: int = 1024,
    ) -> str:
        anthropic_tools = (
            [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in tools]
            if tools
            else None
        )

        conversation = list(messages)  # copia local; solo vive durante este turno

        for iteration in range(MAX_TOOL_ITERATIONS):
            request_payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": conversation,
                "tools": anthropic_tools,
            }
            self.logger.log(
                "request", "llm", request_payload, method=f"messages.create (iter {iteration})"
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=conversation,
                tools=anthropic_tools,
            )

            response_summary = {
                "stop_reason": response.stop_reason,
                "content": [block.model_dump() for block in response.content],
            }
            self.logger.log(
                "response", "llm", response_summary, method=f"messages.create (iter {iteration})"
            )

            if response.stop_reason != "tool_use":
                return "".join(block.text for block in response.content if block.type == "text")

            if tool_executor is None:
                return "[El modelo pidió usar una tool, pero no hay tool_executor configurado.]"

            conversation.append({"role": "assistant", "content": response.content})

            tool_result_blocks = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                call = ToolCall(name=block.name, arguments=block.input, call_id=block.id)
                result_text = tool_executor(call)
                tool_result_blocks.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result_text}
                )
            conversation.append({"role": "user", "content": tool_result_blocks})

        return "[El modelo excedió el número máximo de llamadas a herramientas permitidas.]"
