"""
Agrupa varios MCPClient ya conectados y hace de puente hacia el LLMProvider:

- list_tool_specs()  -> traduce las tools de todos los servidores conectados
                         a ToolSpec genéricos (name, description, input_schema),
                         prefijando el nombre con el servidor de origen
                         ("filesystem__read_file", "git__commit", "echo-test__echo", ...)
                         para evitar colisiones si dos servidores exponen
                         una tool con el mismo nombre.
- execute(tool_call) -> dado un ToolCall con nombre prefijado, encuentra
                         el MCPClient dueño y ejecuta tools/call sobre él.

"""
from typing import Dict, List

from src.llm.types import ToolCall, ToolSpec
from src.mcp.client import MCPClient

SEPARATOR = "__"


class MCPToolRouter:
    def __init__(self, clients: List[MCPClient]):
        self.clients: Dict[str, MCPClient] = {client.name: client for client in clients}

    def list_tool_specs(self) -> List[ToolSpec]:
        specs = []
        for client in self.clients.values():
            for tool in client.tools:
                specs.append(
                    ToolSpec(
                        name=f"{client.name}{SEPARATOR}{tool['name']}",
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {"type": "object", "properties": {}}),
                    )
                )
        return specs

    def execute(self, call: ToolCall) -> str:
        server_name, _, tool_name = call.name.partition(SEPARATOR)
        client = self.clients.get(server_name)
        if client is None:
            return f"Error: no existe un servidor MCP conectado llamado '{server_name}'."

        result = client.call_tool(tool_name, call.arguments)
        # El resultado de MCP viene como {"content": [{"type": "text", "text": "..."}]}
        parts = [block.get("text", "") for block in result.get("content", []) if block.get("type") == "text"]
        return "\n".join(parts) if parts else str(result)