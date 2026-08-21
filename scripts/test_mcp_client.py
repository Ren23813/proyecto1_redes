"""
Valida el MCPClient contra el echo_server de prueba.

Uso 
    python scripts/test_mcp_client.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.interaction_logger import InteractionLogger  # noqa: E402
from src.mcp.client import MCPClient  # noqa: E402
from src.mcp.stdio_transport import StdioTransport  # noqa: E402


def main() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = InteractionLogger(log_file=log_dir / "interactions.jsonl")

    transport = StdioTransport(command=[sys.executable, "scripts/echo_server.py"])
    client = MCPClient(name="echo-test", transport=transport, logger=logger)

    client.connect()
    print("\n>>> Tools descubiertas:", [t["name"] for t in client.tools])

    result = client.call_tool("echo", {"text": "Hola MCP !"})
    print("\n>>> Resultado de tools/call:", result)

    client.close()


if __name__ == "__main__":
    main()
