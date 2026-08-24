"""
Punto de entrada del chatbot.

Fase 1: conexión LLM + contexto + logging.
Fase 2: el LLM ahora puede invocar tools de servidores MCP conectados.

Por ahora solo se conecta el servidor de prueba `echo-test` para validar

Uso:
    python main.py
"""
import sys

from src.config import load_config
from src.interaction_logger import InteractionLogger
from src.llm.factory import build_provider
from src.llm_client import LLMClient
from src.mcp.client import MCPClient
from src.mcp.stdio_transport import StdioTransport
from src.mcp.tool_router import MCPToolRouter


def connect_mcp_servers(logger: InteractionLogger) -> list[MCPClient]:
    """
    Lanza y conecta todos los servidores MCP que el chatbot debe usar.

    TODO (Fase 3): agregar aquí Filesystem y Git oficiales, ej.:
        MCPClient(
            name="filesystem",
            transport=StdioTransport(["npx", "-y", "@modelcontextprotocol/server-filesystem", "<dir>"]),
            logger=logger,
        )
    TODO (Fase 4): servidor custom local (eventualmente)
    """
    servers = [
        MCPClient(
            name="echo-test",
            transport=StdioTransport([sys.executable, "scripts/echo_server.py"]),
            logger=logger,
        ),
    ]
    for client in servers:
        client.connect()
        print(f"[MCP] Conectado a '{client.name}' -- tools: {[t['name'] for t in client.tools]}")
    return servers


def print_banner(provider_name: str) -> None:
    print("  Chatbot MCP - Proyecto 1 (Redes)")
    print(f"  Proveedor de LLM: {provider_name}")
    print("  Comandos: 'salir' para terminar, 'reset' para limpiar contexto")



def main() -> None:
    config = load_config()
    logger = InteractionLogger(log_file=config.log_file)
    provider = build_provider(config, logger)

    mcp_servers = connect_mcp_servers(logger)
    tool_router = MCPToolRouter(mcp_servers)

    llm = LLMClient(provider=provider, logger=logger, tool_router=tool_router)

    print_banner(config.llm_provider)

    try:
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
    finally:
        for client in mcp_servers:
            client.close()


if __name__ == "__main__":
    main()