"""
Interfaz común para proveedores de LLM. Permite intercambiar el backend
(Anthropic, Ollama local, etc.) sin tocar el resto del chatbot.

`complete()` sirve tanto para una respuesta simple (sin tools) como para
un turno completo con tool-calling: si se le pasan `tools` y
`tool_executor`, el proveedor se encarga internamente del ciclo
"pedir tool -> ejecutar -> mandar resultado -> repetir" hasta que el
modelo entregue una respuesta de texto final, y regresa solo ese texto.
Los mensajes intermedios (tool_use/tool_calls, tool_result) son un detalle
interno de cada proveedor y nunca se filtran al historial externo.
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from src.llm.types import ToolCall, ToolSpec


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolSpec]] = None,
        tool_executor: Optional[Callable[[ToolCall], str]] = None,
        max_tokens: int = 1024,
    ) -> str:
        """Manda el historial al LLM y regresa el texto final de la respuesta."""
        raise NotImplementedError