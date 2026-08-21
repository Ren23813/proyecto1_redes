"""
Interfaz común para proveedores de LLM. Permite intercambiar el backend
(Anthropic, Ollama local, etc.) sin tocar el resto del chatbot -- el resto
del código solo conoce este contrato, nunca el SDK/API concreto.
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """Manda el historial de mensajes al LLM y regresa el texto de la respuesta."""
        raise NotImplementedError
