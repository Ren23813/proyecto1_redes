"""
Cliente del LLM (Anthropic API) con manejo de contexto de conversación.

Esta parte sí usa el SDK oficial de Anthropic. La restricción de no usar SDKs del PDF aplica solo al
protocolo MCP, no a la llamada al LLM en sí.
"""
from typing import Dict, List

from anthropic import Anthropic

from src.interaction_logger import InteractionLogger


class LLMClient:
    def __init__(self, api_key: str, model: str, logger: InteractionLogger):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = logger

        # Historial completo de la sesión: se manda entero en cada request,
        # ya que la API no guarda estado entre llamadas (requisito #2: mantener contexto).
        self.history: List[Dict[str, str]] = []

    def send(self, user_text: str, max_tokens: int = 1024) -> str:
        self.history.append({"role": "user", "content": user_text})

        request_payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": self.history,
        }
        self.logger.log("request", "llm", request_payload, method="messages.create")

        response = self.client.messages.create(**request_payload)

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        self.logger.log(
            "response",
            "llm",
            {"role": "assistant", "content": text, "stop_reason": response.stop_reason},
            method="messages.create",
        )

        self.history.append({"role": "assistant", "content": text})
        return text

    def reset(self) -> None:
        """Limpia el historial"""
        self.history = []
