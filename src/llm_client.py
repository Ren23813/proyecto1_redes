"""
Sesión de chat: mantiene el historial de conversación (contexto, siempre
como texto plano user/assistant) y delega al LLMProvider tanto la llamada
simple como -si hay un MCPToolRouter conectado- el ciclo completo de
tool-calling. El historial externo nunca guarda los mensajes intermedios
de tool_use/tool_result: eso es responsabilidad interna del provider
durante un solo `send()`.
"""
from typing import Dict, List, Optional

from src.interaction_logger import InteractionLogger
from src.llm.base import LLMProvider
from src.mcp.tool_router import MCPToolRouter


class LLMClient:
    def __init__(
        self,
        provider: LLMProvider,
        logger: InteractionLogger,
        tool_router: Optional[MCPToolRouter] = None,
    ):
        self.provider = provider
        self.logger = logger
        self.tool_router = tool_router
        self.history: List[Dict[str, str]] = []

    def send(self, user_text: str, max_tokens: int = 1024) -> str:
        self.history.append({"role": "user", "content": user_text})

        tools = self.tool_router.list_tool_specs() if self.tool_router else None
        tool_executor = self.tool_router.execute if self.tool_router else None

        text = self.provider.complete(
            self.history,
            tools=tools,
            tool_executor=tool_executor,
            max_tokens=max_tokens,
        )

        self.history.append({"role": "assistant", "content": text})
        return text

    def reset(self) -> None:
        """Limpia el historial. Útil si luego agregas un comando /reset."""
        self.history = []