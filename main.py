"""
Punto de entrada del chatbot.

Fase 1: conexión LLM + contexto + logging.
Fase 2: el LLM puede invocar tools de servidores MCP conectados.
Fase 3: se conectan los servidores oficiales Filesystem y Git.
Fase 4: se conecta el servidor custom local (Farmacia + Mini Clínica).

Uso:
    python main.py
"""
import sys
from pathlib import Path
from typing import List

from src.config import Config, load_config
from src.interaction_logger import InteractionLogger
from src.llm.factory import build_provider
from src.llm_client import LLMClient
from src.mcp.client import MCPClient
from src.mcp.stdio_transport import StdioTransport
from src.mcp.tool_router import MCPToolRouter
from src.workspace import ensure_git_repo, ensure_workspace


def connect_mcp_servers(logger: InteractionLogger, config: Config) -> List[MCPClient]:
    """
    Lanza y conecta todos los servidores MCP que el chatbot debe usar.

    Filesystem y Git operan sobre `config.workspace_dir` -- una carpeta
    dedicada para que el chatbot juegue con archivos/commits sin tocar el
    repositorio real del proyecto. Ver src/workspace.py para el porqué del
    bootstrap de `git init` antes de lanzar el servidor de git.
    """
    ensure_workspace(config.workspace_dir)
    ensure_git_repo(config.workspace_dir)

    servers = [
        MCPClient(
            name="filesystem",
            transport=StdioTransport(
                # Yo tengo Bun como manejador de nodejs, pero si quien lo corre tiene npm, cambiarlo por npx
                ["bunx", "-y", "@modelcontextprotocol/server-filesystem", str(config.workspace_dir)]
            ),
            logger=logger,
        ),
        MCPClient(
            name="git",
            transport=StdioTransport(["uvx", "mcp-server-git", "--repository", str(config.workspace_dir)]),
            logger=logger,
        ),
        MCPClient(
            name="pharmacy",
            transport=StdioTransport([sys.executable, "server_local/server.py"]),
            logger=logger,
        ),
    ]
    for client in servers:
        client.connect()
        print(f"[MCP] Conectado a '{client.name}' -- tools: {[t['name'] for t in client.tools]}")
    return servers


def print_banner(provider_name: str, workspace_dir: Path) -> None:
    print("  Chatbot MCP - Proyecto 1 (Redes)")
    print(f"  Proveedor de LLM: {provider_name}")
    print(f"  Workspace (Filesystem/Git): {workspace_dir}")
    print("  Comandos: 'salir' para terminar, 'reset' para limpiar contexto")



def main() -> None:
    config = load_config()
    logger = InteractionLogger(log_file=config.log_file)
    provider = build_provider(config, logger)

    mcp_servers = connect_mcp_servers(logger, config)
    tool_router = MCPToolRouter(mcp_servers)

    llm = LLMClient(provider=provider, logger=logger, tool_router=tool_router)

    print_banner(config.llm_provider, config.workspace_dir)

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


##crea un archivo README.md que diga 'Hola desde MCP' y luego agrégalo y haz commit al repositorio con el mensaje "primer commit"
##dime exactamente la ubicacion del archivo
##edita el mismo archivo y agrega tu nombre de modelo "Hola desde MPC - te habla [modelo]"
