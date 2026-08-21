"""
Servidor MCP de prueba ("echo") — solo para validar el MCPClient inicial
Solo es para probar antes de implementar el Filesystem/Git conectados y el servidor propio

Implementado a mano (initialize, tools/list, tools/call) leyendo JSON-RPC
newline-delimited por stdin y respondiendo por stdout. 
Igual que hará el servidor custom más adelante
"""
import json
import sys


def send(message) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def handle(message) -> None:
    method = message.get("method")
    msg_id = message.get("id")

    if method == "initialize":
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "echo-test-server", "version": "0.1.0"},
                },
            }
        )
    elif method == "notifications/initialized":
        pass  # notificación: no se responde
    elif method == "tools/list":
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "echo",
                            "description": "Repite el texto que se le envía.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"text": {"type": "string"}},
                                "required": ["text"],
                            },
                        }
                    ]
                },
            }
        )
    elif method == "tools/call":
        params = message.get("params", {})
        if params.get("name") == "echo":
            text = params.get("arguments", {}).get("text", "")
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": f"echo: {text}"}]},
                }
            )
        else:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Tool desconocida: {params.get('name')}"},
                }
            )
    elif msg_id is not None:
        send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Método no soportado: {method}"}})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(message)


if __name__ == "__main__":
    main()
