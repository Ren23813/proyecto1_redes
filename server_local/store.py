"""
Store de datos para el servidor de Farmacia + Mini Clínica.

Separa la lógica de negocio (buscar medicamentos, comprar, agendar citas)
del bucle de protocolo JSON-RPC en server.py -- así cada uno se puede leer
y probar por separado.

Persistencia: se usa un archivo semilla (catalog_seed.json, versionado en
git) que se copia UNA vez a un archivo de runtime (pharmacy_data.json,
ignorado por git) la primera vez que se arranca el servidor. A partir de
ahí, cada compra/cita se escribe de inmediato en el archivo de runtime,
así el estado (stock, citas ocupadas) persiste entre sesiones del chatbot
sin ensuciar el dato semilla que vive en el repositorio.
"""
import json
import shutil
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent / "data"
SEED_FILE = DATA_DIR / "catalog_seed.json"
RUNTIME_FILE = DATA_DIR / "pharmacy_data.json"


class ToolError(Exception):
    """
    Error de negocio esperado (ej. "stock insuficiente", "id no existe").
    server.py lo traduce a un resultado de tools/call con isError=true,
    NO a un error de protocolo JSON-RPC -- el servidor sigue funcionando
    normalmente después de este tipo de error, igual que hacen Filesystem
    y Git oficiales.
    """


class PharmacyStore:
    def __init__(self) -> None:
        self._lock = Lock()
        if not RUNTIME_FILE.exists():
            shutil.copy(SEED_FILE, RUNTIME_FILE)
        self._load()

    def _load(self) -> None:
        with open(RUNTIME_FILE, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

    def _save(self) -> None:
        with open(RUNTIME_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------------
    # Farmacia
    # ---------------------------------------------------------------

    def search_medications(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        results = []
        for med in self.data["medications"]:
            haystack = med["name"].lower() + " " + " ".join(med.get("symptoms", []))
            if q in haystack:
                results.append(med)
        return results

    def get_medication_details(self, medication_id: str) -> Dict[str, Any]:
        return self._find_medication(medication_id)

    def purchase_medication(self, medication_id: str, quantity: int, customer_name: str) -> Dict[str, Any]:
        with self._lock:
            if quantity <= 0:
                raise ToolError("La cantidad debe ser mayor a 0.")

            med = self._find_medication(medication_id)
            if med["stock"] < quantity:
                raise ToolError(
                    f"Stock insuficiente para '{med['name']}' (disponible: {med['stock']}, solicitado: {quantity})."
                )

            med["stock"] -= quantity
            order = {
                "id": self._next_id("orders", "ord"),
                "medication_id": medication_id,
                "medication_name": med["name"],
                "quantity": quantity,
                "customer_name": customer_name,
                "total": round(med["price"] * quantity, 2),
                "status": "confirmed",
            }
            self.data["orders"].append(order)
            self._save()
            return order

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        with self._lock:
            order = self._find_order(order_id)
            if order["status"] == "cancelled":
                raise ToolError(f"La orden '{order_id}' ya estaba cancelada.")

            med = self._find_medication(order["medication_id"])
            med["stock"] += order["quantity"]
            order["status"] = "cancelled"
            self._save()
            return order

    # ---------------------------------------------------------------
    # Mini clínica
    # ---------------------------------------------------------------

    def list_available_slots(
        self, specialty: Optional[str] = None, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        slots = [s for s in self.data["appointment_slots"] if not s["occupied"]]
        if specialty:
            slots = [s for s in slots if s["specialty"].lower() == specialty.lower()]
        if date:
            slots = [s for s in slots if s["date"] == date]
        return slots

    def schedule_appointment(self, patient_name: str, specialty: str, slot_id: str) -> Dict[str, Any]:
        with self._lock:
            slot = self._find_slot(slot_id)
            if slot["occupied"]:
                raise ToolError(f"El horario '{slot_id}' ya está ocupado.")
            if slot["specialty"].lower() != specialty.lower():
                raise ToolError(f"El horario '{slot_id}' es de {slot['specialty']}, no de {specialty}.")

            slot["occupied"] = True
            appointment = {
                "id": self._next_id("appointments", "apt"),
                "patient_name": patient_name,
                "specialty": specialty,
                "slot_id": slot_id,
                "date": slot["date"],
                "time": slot["time"],
                "status": "confirmed",
            }
            self.data["appointments"].append(appointment)
            self._save()
            return appointment

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        with self._lock:
            appt = self._find_appointment(appointment_id)
            if appt["status"] == "cancelled":
                raise ToolError(f"La cita '{appointment_id}' ya estaba cancelada.")

            slot = self._find_slot(appt["slot_id"])
            slot["occupied"] = False
            appt["status"] = "cancelled"
            self._save()
            return appt

    # ---------------------------------------------------------------
    # Compartido
    # ---------------------------------------------------------------

    def get_customer_history(self, customer_name: str) -> Dict[str, Any]:
        name = customer_name.strip().lower()
        orders = [o for o in self.data["orders"] if o["customer_name"].strip().lower() == name]
        appointments = [a for a in self.data["appointments"] if a["patient_name"].strip().lower() == name]
        return {"orders": orders, "appointments": appointments}

    # ---------------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------------

    def _find_medication(self, medication_id: str) -> Dict[str, Any]:
        for med in self.data["medications"]:
            if med["id"] == medication_id:
                return med
        raise ToolError(f"No existe un medicamento con id '{medication_id}'.")

    def _find_order(self, order_id: str) -> Dict[str, Any]:
        for order in self.data["orders"]:
            if order["id"] == order_id:
                return order
        raise ToolError(f"No existe una orden con id '{order_id}'.")

    def _find_slot(self, slot_id: str) -> Dict[str, Any]:
        for slot in self.data["appointment_slots"]:
            if slot["id"] == slot_id:
                return slot
        raise ToolError(f"No existe un horario con id '{slot_id}'.")

    def _find_appointment(self, appointment_id: str) -> Dict[str, Any]:
        for appt in self.data["appointments"]:
            if appt["id"] == appointment_id:
                return appt
        raise ToolError(f"No existe una cita con id '{appointment_id}'.")

    def _next_id(self, collection: str, prefix: str) -> str:
        counters = self.data.setdefault("_counters", {})
        n = counters.get(collection, 0) + 1
        counters[collection] = n
        return f"{prefix}-{n:04d}"