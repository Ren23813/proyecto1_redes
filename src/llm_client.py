"""
Sesión de chat: mantiene el historial de conversación (contexto) y
delega la llamada real al LLM al `LLMProvider` inyectado (Anthropic,
Ollama, ...). El logging de requests/responses es idéntico sin importar
el proveedor
"""
from typing import Dict, List


from src.interaction_logger import InteractionLogger
from src.llm.base import LLMProvider


class LLMClient:
    def __init__(self, provider: LLMProvider, logger: InteractionLogger):
        self.provider = provider
        self.logger = logger
        # Historial completo de la sesión: se manda entero en cada request, así mantiene el contexto
        self.history: List[Dict[str, str]] = []

    def send(self, user_text: str, max_tokens: int = 1024) -> str:
        self.history.append({"role": "user", "content": user_text})

        self.logger.log(
            "request", "llm", {"messages": self.history, "max_tokens": max_tokens}, method="complete"
        )

        text = self.provider.complete(self.history, max_tokens=max_tokens)

        self.logger.log("response", "llm", {"role": "assistant", "content": text}, method="complete")

        self.history.append({"role": "assistant", "content": text})
        return text

    def reset(self) -> None:
        """Limpia el historial"""
        self.history = []
