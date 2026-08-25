"""
Valida el escenario de la Fase 3 (crear README, agregarlo, hacer commit)
directamente contra los servidores MCP reales de Filesystem y Git, sin
pasar por el LLM todavía -- así confirmamos que la integración con los
servidores oficiales funciona antes de confiarle la decisión al modelo.

Uso (desde la raíz del proyecto):
    python scripts/test_filesystem_git.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config  # noqa: E402
from src.interaction_logger import InteractionLogger  # noqa: E402
from src.mcp.client import MCPClient  # noqa: E402
from src.mcp.stdio_transport import StdioTransport  # noqa: E402
from src.mcp.tool_router import MCPToolRouter  # noqa: E402
from src.llm.types import ToolCall  # noqa: E402
from src.workspace import ensure_git_repo, ensure_workspace  # noqa: E402


def main() -> None:
    config = load_config()
    logger = InteractionLogger(log_file=Path("logs") / "test_filesystem_git.jsonl")

    ensure_workspace(config.workspace_dir)
    ensure_git_repo(config.workspace_dir)
    print(f"Workspace: {config.workspace_dir}")

    fs = MCPClient(
        name="filesystem",
        ## Yo tengo Bun como manejador de nodejs, pero si quien lo corre tiene npm, cambiarlo por npx
        transport=StdioTransport(["bunx", "-y", "@modelcontextprotocol/server-filesystem", str(config.workspace_dir)]),
        logger=logger,
    )
    git = MCPClient(
        name="git",
        transport=StdioTransport(["uvx", "mcp-server-git", "--repository", str(config.workspace_dir)]),
        logger=logger,
    )
    fs.connect()
    git.connect()

    router = MCPToolRouter([fs, git])
    print("\nTools disponibles:", [s.name for s in router.list_tool_specs()])

    print("\n>>> 1) Crear README.md vía filesystem__write_file")
    print(
        router.execute(
            ToolCall(
                name="filesystem__write_file",
                arguments={
                    "path": str(config.workspace_dir / "README.md"),
                    "content": "# Proyecto 1 - MCP\n\nCreado por el chatbot vía MCP (Fase 3).\n",
                },
            )
        )
    )

    print("\n>>> 2) git add README.md vía git__git_add")
    print(
        router.execute(
            ToolCall(
                name="git__git_add",
                arguments={"repo_path": str(config.workspace_dir), "files": ["README.md"]},
            )
        )
    )

    print("\n>>> 3) git commit vía git__git_commit")
    print(
        router.execute(
            ToolCall(
                name="git__git_commit",
                arguments={
                    "repo_path": str(config.workspace_dir),
                    "message": "Add README via MCP chatbot (Fase 3)",
                },
            )
        )
    )

    print("\n>>> 4) git log vía git__git_log (para confirmar el commit)")
    print(router.execute(ToolCall(name="git__git_log", arguments={"repo_path": str(config.workspace_dir)})))

    fs.close()
    git.close()
    print("\nOK: escenario completo (README + add + commit) funcionó vía MCP real.")


if __name__ == "__main__":
    main()