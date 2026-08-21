"""
Utilidades para construir y clasificar mensajes JSON-RPC 2.0.

MCP usa JSON-RPC 2.0
- Request:      {"jsonrpc":"2.0", "id":N, "method":"...", "params":{...}}
- Notification: igual que un request pero sin "id" , por tanto no se espera respuesta
- Response OK:  {"jsonrpc":"2.0", "id":N, "result":{...}}
- Response err: {"jsonrpc":"2.0", "id":N, "error":{"code":..,"message":".."}}
"""
import itertools
from typing import Any, Dict, Optional

_id_counter = itertools.count(1)


def next_id() -> int:
    return next(_id_counter)


def make_request(
    method: str, params: Optional[Dict[str, Any]] = None, msg_id: Optional[int] = None
) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": msg_id if msg_id is not None else next_id(),
        "method": method,
        "params": params or {},
    }


def make_notification(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params or {}}


def is_response(message: Dict[str, Any]) -> bool:
    return "id" in message and ("result" in message or "error" in message)


def is_request(message: Dict[str, Any]) -> bool:
    return "id" in message and "method" in message


def is_notification(message: Dict[str, Any]) -> bool:
    return "id" not in message and "method" in message


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"JSON-RPC error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data

    @classmethod
    def from_error_obj(cls, error_obj: Dict[str, Any]) -> "JsonRpcError":
        return cls(
            error_obj.get("code", -32000),
            error_obj.get("message", "Unknown error"),
            error_obj.get("data"),
        )