"""
Servidor MCP de Farmacia + Mini Clínica (Fase 4 -- servidor custom local).

Implementado a mano (sin SDK de MCP), igual que el resto del proyecto:
lee JSON-RPC 2.0 newline-delimited por stdin, responde por stdout.
Soporta initialize, notifications/initialized, tools/list y tools/call.

Ver README.md en esta misma carpeta para la especificación completa de
cada tool, sus parámetros y ejemplos de uso.

Uso (normalmente lo lanza el chatbot como subproceso, no se corre a mano):
    python server_local/server.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import PharmacyStore, ToolError  # noqa: E402

PROTOCOL_VERSION = "2025-11-25"

TOOLS = [
    {
        "name": "search_medications",
        "description": "Busca medicamentos de venta libre por síntoma o por nombre (ej. 'dolor de cabeza', 'alergia', 'ibuprofeno').",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Síntoma o nombre del medicamento"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_medication_details",
        "description": "Obtiene el detalle de un medicamento: precio, stock, si requiere receta y descripción.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "medication_id": {
                    "type": "string",
                    "description": "Id EXACTO devuelto por search_medications (ej. 'med-003'). Nunca lo inventes ni lo deduzcas del nombre.",
                }
            },
            "required": ["medication_id"],
        },
    },
    {
        "name": "purchase_medication",
        "description": "Compra un medicamento: descuenta stock y genera una orden de compra.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "medication_id": {
                    "type": "string",
                    "description": "Id EXACTO devuelto por search_medications o get_medication_details (ej. 'med-003'). Nunca lo inventes ni lo deduzcas del nombre.",
                },
                "quantity": {"type": "integer", "minimum": 1},
                "customer_name": {"type": "string"},
            },
            "required": ["medication_id", "quantity", "customer_name"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancela una orden de compra existente y repone el stock del medicamento.",
        "inputSchema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "list_available_slots",
        "description": "Lista los horarios disponibles de la mini clínica. Especialidades válidas: Oftalmología, Medicina General, Pediatría.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "enum": ["Oftalmología", "Medicina General", "Pediatría"],
                },
                "date": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
            },
        },
    },
    {
        "name": "schedule_appointment",
        "description": "Agenda una cita médica en un horario disponible de la clínica.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string"},
                "specialty": {
                    "type": "string",
                    "enum": ["Oftalmología", "Medicina General", "Pediatría"],
                },
                "slot_id": {
                    "type": "string",
                    "description": "Id EXACTO devuelto por list_available_slots (ej. 'slot-ped-1'). Nunca lo inventes.",
                },
            },
            "required": ["patient_name", "specialty", "slot_id"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancela una cita médica ya agendada y libera el horario correspondiente.",
        "inputSchema": {
            "type": "object",
            "properties": {"appointment_id": {"type": "string"}},
            "required": ["appointment_id"],
        },
    },
    {
        "name": "get_customer_history",
        "description": "Consulta el historial de compras y citas de un cliente/paciente por nombre.",
        "inputSchema": {
            "type": "object",
            "properties": {"customer_name": {"type": "string"}},
            "required": ["customer_name"],
        },
    },
]

store = PharmacyStore()

TOOL_HANDLERS = {
    "search_medications": lambda a: store.search_medications(a["query"]),
    "get_medication_details": lambda a: store.get_medication_details(a["medication_id"]),
    "purchase_medication": lambda a: store.purchase_medication(
        a["medication_id"], int(a["quantity"]), a["customer_name"]
    ),
    "cancel_order": lambda a: store.cancel_order(a["order_id"]),
    "list_available_slots": lambda a: store.list_available_slots(a.get("specialty"), a.get("date")),
    "schedule_appointment": lambda a: store.schedule_appointment(
        a["patient_name"], a["specialty"], a["slot_id"]
    ),
    "cancel_appointment": lambda a: store.cancel_appointment(a["appointment_id"]),
    "get_customer_history": lambda a: store.get_customer_history(a["customer_name"]),
}


def send(message) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle_tools_call(msg_id, params) -> None:
    name = params.get("name")
    arguments = params.get("arguments", {})
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Tool desconocida: {name}"}})
        return

    try:
        result = handler(arguments)
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                },
            }
        )
    except ToolError as e:
        # Error de negocio esperado (ej. "stock insuficiente"): el
        # servidor sigue funcionando, se lo reportamos al LLM como
        # resultado con isError=true (igual que hacen Filesystem/Git).
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": str(e)}], "isError": True},
            }
        )
    except (KeyError, TypeError, ValueError) as e:
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": f"Argumentos inválidos: {e}"}], "isError": True},
            }
        )


def handle(message) -> None:
    method = message.get("method")
    msg_id = message.get("id")

    if method == "initialize":
        send(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "pharmacy-clinic-server", "version": "1.0.0"},
                },
            }
        )
    elif method == "notifications/initialized":
        pass  # notificación: no se responde
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        handle_tools_call(msg_id, message.get("params", {}))
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