"""
Tipos genéricos para exponerle tools (herramientas MCP) a un LLMProvider,
sin que este último necesite saber nada de MCP -- solo ve nombre,
descripción y JSON Schema de cada tool.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None  # usado por Anthropic para correlacionar el tool_result


@dataclass
class ToolInteraction:
    """Un tool call + su resultado, ocurrido durante un solo turno."""

    tool_name: str
    arguments: Dict[str, Any]
    result_text: str


@dataclass
class CompletionResult:
    text: str
    tool_interactions: List[ToolInteraction]


# Límite de vueltas del ciclo "modelo pide tool -> ejecutamos -> le damos el
# resultado" dentro de UN turno de usuario. Evita loops infinitos si el
# modelo se queda pidiendo tools indefinidamente (más común en modelos
# locales pequeños).
MAX_TOOL_ITERATIONS = 10