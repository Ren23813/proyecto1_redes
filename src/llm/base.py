"""
Interfaz común para proveedores de LLM. Permite intercambiar el backend
(Anthropic, Ollama local, etc.) sin tocar el resto del chatbot.

`complete()` regresa un CompletionResult con el texto final Y la lista de
tool_interactions (tool + argumentos + resultado) que ocurrieron durante
el turno. Esto es clave para que LLMClient pueda "anclar" datos concretos
(ids reales devueltos por una tool) en el historial -- sin esto, el
modelo tiende a alucinar ids en turnos futuros porque el texto en
lenguaje natural nunca los conserva literalmente.
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from src.llm.types import CompletionResult, ToolCall, ToolSpec


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolSpec]] = None,
        tool_executor: Optional[Callable[[ToolCall], str]] = None,
        max_tokens: int = 2048,
    ) -> CompletionResult:
        raise NotImplementedError