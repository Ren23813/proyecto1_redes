"""
Cliente MCP implementado a mano (sin SDK)

Ciclo de vida:
  1. connect() -> lanza el transporte, hace el handshake "initialize"
     y descubre las tools disponibles ("tools/list").
  2. call_tool(...) -> invoca una tool ("tools/call") las veces que haga
     falta durante la sesión.
  3. close() -> termina el transporte.

No depende del transporte, pues funciona igual con StdioTransport
que con HttpTransport, siempre que el objeto exponga
start() / send() / receive() / stop().
"""
from typing import Any, Dict, List, Optional

from src.interaction_logger import InteractionLogger
from src.mcp.jsonrpc import JsonRpcError, is_response, make_notification, make_request

MCP_PROTOCOL_VERSION = "2025-11-25"


class MCPClient:
    def __init__(self, name: str, transport: Any, logger: InteractionLogger):
        """
        name: identificador corto del servidor (ej. "filesystem", "git",
              "custom-local", "custom-remote"). Se usa como `source` en el
              log, así se distingue en logs/interactions.jsonl qué servidor
              generó cada mensaje.
        transport: StdioTransport o HttpTransport ya configurado
        """
        self.name = name
        self.transport = transport
        self.logger = logger
        self.server_info: Optional[Dict[str, Any]] = None
        self.tools: List[Dict[str, Any]] = []

    # ---- ciclo de vida ----------------------------------------------

    def connect(self) -> None:
        self.transport.start()
        self._initialize()
        self._discover_tools()

    def close(self) -> None:
        self.transport.stop()

    # ---- protocolo ----------------------------------------------

    def _initialize(self) -> None:
        request = make_request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "proyecto1-chatbot", "version": "1.0.0"},
            },
        )
        response = self._request(request)
        self.server_info = response.get("result", {})

        # El cliente confirma con una notificación (sin id, sin respuesta).
        self._send(make_notification("notifications/initialized"))

    def _discover_tools(self) -> None:
        response = self._request(make_request("tools/list"))
        self.tools = response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        response = self._request(make_request("tools/call", {"name": tool_name, "arguments": arguments}))
        return response.get("result", {})

    # ---- envío/recepción + logging ----------------------------------------------

    def _send(self, message: Dict[str, Any]) -> None:
        direction = "request" if "id" in message else "notification_out"
        self.logger.log(direction, f"mcp:{self.name}", message, method=message.get("method"))
        self.transport.send(message)

    def _request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self._send(request)
        while True:
            message = self.transport.receive()
            if is_response(message) and message.get("id") == request["id"]:
                self.logger.log("response", f"mcp:{self.name}", message, method=request.get("method"))
                if "error" in message:
                    raise JsonRpcError.from_error_obj(message["error"])
                return message
            self.logger.log("notification_in", f"mcp:{self.name}", message)