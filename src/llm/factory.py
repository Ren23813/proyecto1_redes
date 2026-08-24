"""
Construye la instancia del proveedor de LLM según LLM_PROVIDER en .env.
"""
from src.config import Config
from src.interaction_logger import InteractionLogger
from src.llm.anthropic_provider import AnthropicProvider
from src.llm.base import LLMProvider
from src.llm.ollama_provider import OllamaProvider


def build_provider(config: Config, logger: InteractionLogger) -> LLMProvider:
    if config.llm_provider == "ollama":
        return OllamaProvider(model=config.ollama_model, base_url=config.ollama_base_url, logger=logger)

    if config.llm_provider == "anthropic":
        if not config.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic pero no hay ANTHROPIC_API_KEY en .env")
        return AnthropicProvider(api_key=config.anthropic_api_key, model=config.anthropic_model, logger=logger)

    raise ValueError(f"LLM_PROVIDER desconocido: {config.llm_provider!r} (usa 'anthropic' u 'ollama')")