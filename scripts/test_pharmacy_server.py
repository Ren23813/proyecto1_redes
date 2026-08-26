"""
Valida el servidor de Farmacia + Mini Clínica (Fase 4) directamente vía
MCP, ejercitando las 8 tools SIN pasar por el LLM -- confirma que el
protocolo y la lógica de negocio funcionan antes de confiarle la decisión
al modelo.

Uso (desde la raíz del proyecto):
    python scripts/test_pharmacy_server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.interaction_logger import InteractionLogger  # noqa: E402
from src.llm.types import ToolCall  # noqa: E402
from src.mcp.client import MCPClient  # noqa: E402
from src.mcp.stdio_transport import StdioTransport  # noqa: E402
from src.mcp.tool_router import MCPToolRouter  # noqa: E402


def show(label, result):
    print(f"\n>>> {label}")
    print(result)


def main() -> None:
    logger = InteractionLogger(log_file=Path("logs") / "test_pharmacy_server.jsonl")

    client = MCPClient(
        name="pharmacy",
        transport=StdioTransport([sys.executable, "server_local/server.py"]),
        logger=logger,
    )
    client.connect()
    router = MCPToolRouter([client])

    print("Tools disponibles:", [s.name for s in router.list_tool_specs()])

    show(
        "1) Buscar medicamentos para 'dolor de cabeza'",
        router.execute(ToolCall(name="pharmacy__search_medications", arguments={"query": "dolor de cabeza"})),
    )

    show(
        "2) Detalle de med-001",
        router.execute(ToolCall(name="pharmacy__get_medication_details", arguments={"medication_id": "med-001"})),
    )

    show(
        "3) Comprar 2 unidades de med-001",
        router.execute(
            ToolCall(
                name="pharmacy__purchase_medication",
                arguments={"medication_id": "med-001", "quantity": 2, "customer_name": "Ana Pérez"},
            )
        ),
    )

    show(
        "4) Comprar cantidad excesiva (debe fallar con isError, no tronar el servidor)",
        router.execute(
            ToolCall(
                name="pharmacy__purchase_medication",
                arguments={"medication_id": "med-001", "quantity": 99999, "customer_name": "Ana Pérez"},
            )
        ),
    )

    show(
        "5) Horarios disponibles de Pediatría",
        router.execute(ToolCall(name="pharmacy__list_available_slots", arguments={"specialty": "Pediatría"})),
    )

    show(
        "6) Agendar cita en slot-ped-1",
        router.execute(
            ToolCall(
                name="pharmacy__schedule_appointment",
                arguments={"patient_name": "Ana Pérez", "specialty": "Pediatría", "slot_id": "slot-ped-1"},
            )
        ),
    )

    show(
        "7) Historial de Ana Pérez (debe traer la orden y la cita)",
        router.execute(ToolCall(name="pharmacy__get_customer_history", arguments={"customer_name": "Ana Pérez"})),
    )

    show(
        "8) Cancelar la orden (order-0001) -- repone stock",
        router.execute(ToolCall(name="pharmacy__cancel_order", arguments={"order_id": "ord-0001"})),
    )

    show(
        "9) Cancelar la cita (apt-0001) -- libera el horario",
        router.execute(ToolCall(name="pharmacy__cancel_appointment", arguments={"appointment_id": "apt-0001"})),
    )

    client.close()
    print("\nOK: las 8 tools respondieron correctamente vía MCP real.")


if __name__ == "__main__":
    main()