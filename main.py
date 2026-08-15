"""
Punto de entrada del chatbot (conexión LLM + contexto + logging).

Uso:
    python main.py
"""
from src.config import load_config
from src.interaction_logger import InteractionLogger
from src.llm_client import LLMClient


def print_banner() -> None:
    print("-" * 60)
    print("  Chatbot MCP - Proyecto 1 (Redes)")
    print("  Comandos: 'salir' para terminar, 'reset' para limpiar contexto")
    print("-" * 60)


def main() -> None:
    config = load_config()
    logger = InteractionLogger(log_file=config.log_file)
    llm = LLMClient(api_key=config.api_key, model=config.model, logger=logger)

    print_banner()

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
