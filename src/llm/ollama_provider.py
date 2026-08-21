"""
Proveedor: modelo local servido por Ollama (http://localhost:11434 por
defecto). 

Obtener el modelo descargado con `ollama pull <modelo>` y correr con `ollama serve` 

Usa el endpoint nativo POST /api/chat (no el compatible con OpenAI) porque
es el más simple y no agrega dependencias extra (solo `requests`).
"""
from typing import Dict, List

import requests

from src.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
