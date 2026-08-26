"""
Sesión de chat: mantiene el historial de conversación y delega al
LLMProvider tanto la llamada simple como -si hay un MCPToolRouter
conectado- el ciclo completo de tool-calling.

Detalle importante: cuando un turno usa tools, lo que se GUARDA en
`self.history` es el texto visible + un bloque compacto con los
resultados reales de esas tools (incluye ids concretos, ej. "med-003").
Sin esto, en el siguiente turno el modelo solo ve su propio resumen en
lenguaje natural (que nunca conserva ids literales) y tiende a
inventarlos -- es un problema real que se observó probando el proyecto:
el modelo alucinaba medication_id en la segunda vuelta de una compra.
Lo que se MUESTRA al usuario (el valor de retorno de send()) es solo el
texto visible, sin ese bloque.
"""
from typing import Dict, List, Optional

from src.interaction_logger import InteractionLogger
from src.llm.base import LLMProvider
from src.llm.types import ToolInteraction
from src.mcp.tool_router import MCPToolRouter

TOOL_CONTEXT_HEADER = (
    "\n\n[Contexto de herramientas usadas en este turno -- usa estos datos "
    "EXACTOS (incluidos los ids) si la conversación continúa; nunca inventes "
    "un id distinto a los que aparecen aquí]"
)


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

    def send(self, user_text: str, max_tokens: int = 2048) -> str:
        self.history.append({"role": "user", "content": user_text})

        tools = self.tool_router.list_tool_specs() if self.tool_router else None
        tool_executor = self.tool_router.execute if self.tool_router else None

        result = self.provider.complete(
            self.history,
            tools=tools,
            tool_executor=tool_executor,
            max_tokens=max_tokens,
        )

        stored_text = result.text
        if result.tool_interactions:
            stored_text += TOOL_CONTEXT_HEADER
            stored_text += self._format_tool_context(result.tool_interactions)

        self.history.append({"role": "assistant", "content": stored_text})
        return result.text

    @staticmethod
    def _format_tool_context(interactions: List[ToolInteraction]) -> str:
        lines = []
        for interaction in interactions:
            lines.append(f"\n- {interaction.tool_name}({interaction.arguments}) -> {interaction.result_text}")
        return "".join(lines)

    def reset(self) -> None:
        """Limpia el historial. Útil si luego agregas un comando /reset."""
        self.history = []