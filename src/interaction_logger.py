"""
Logger de interacciones (solicitudes/respuestas).

En la Fase 1 se usa para registrar las llamadas al LLM. Está diseñado
para reutilizarse para la Fase 2, para registrar los mensajes
JSON-RPC intercambiados con los servidores MCP (requisito #3 del proyecto).
En fase 2, solo cambia el valor de `source` (ej. "mcp:filesystem", "mcp:git",
"mcp:custom") y `method` (ej. "tools/call", "initialize").

Cada entrada se imprime en consola y además se persiste en
logs/interactions.jsonl (un objeto JSON por línea)
"""
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class LogEntry:
    timestamp: str
    direction: str   # "request" | "response" | "notification"
    source: str       # "llm" | "mcp:filesystem" | "mcp:git" | "mcp:custom" | ...
    method: Optional[str]
    payload: Any


class InteractionLogger:
    def __init__(self, log_file: Path):
        self.log_file = log_file

    def log(
        self,
        direction: str,
        source: str,
        payload: Any,
        method: Optional[str] = None,
    ) -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            direction=direction,
            source=source,
            method=method,
            payload=payload,
        )
        self._print(entry)
        self._persist(entry)

    def _print(self, entry: LogEntry) -> None:
        arrow = "->" if entry.direction == "request" else "<-"
        label = f"[{entry.timestamp}] {arrow} {entry.source}"
        if entry.method:
            label += f" ({entry.method})"
        body = json.dumps(entry.payload, indent=2, ensure_ascii=False, default=str)
        print(f"\n{label}\n{body}")

    def _persist(self, entry: LogEntry) -> None:
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False, default=str) + "\n")
