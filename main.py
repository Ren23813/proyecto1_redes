"""
Punto de entrada del chatbot (Fase 1: conexión LLM + contexto + logging).

Uso:
    python main.py
"""
from src.config import load_config
from src.interaction_logger import InteractionLogger
from src.llm.factory import build_provider
from src.llm_client import LLMClient


def print_banner(provider_name: str) -> None:
    print("  Chatbot MCP - Proyecto 1 (Redes)")
    print(f"  Proveedor de LLM: {provider_name}")
    print("  Comandos: 'salir' para terminar, 'reset' para limpiar contexto")



def main() -> None:
    config = load_config()
    logger = InteractionLogger(log_file=config.log_file)
    provider = build_provider(config)
    llm = LLMClient(provider=provider, logger=logger)

    print_banner(config.llm_provider)

    while True:
        try:
            user_input = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesión terminada.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break

        if user_input.lower() == "reset":
            llm.reset()
            print("[Contexto limpiado]")
            continue

        try:
            reply = llm.send(user_input)
            print(f"\nClaude: {reply}")
        except Exception as e:
            print(f"\n[Error al llamar a la API]: {e}")


if __name__ == "__main__":
    main()
