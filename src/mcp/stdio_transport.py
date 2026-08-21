"""
Transporte stdio para MCP.

Según la especificación, en este transporte cada mensaje JSON-RPC va en
una línea (delimitado por '\\n'), sin saltos de línea embebidos dentro del
mensaje. El cliente lanza al servidor como subproceso y se comunica por
sus stdin/stdout.

La lectura ocurre en un hilo aparte porque el servidor puede enviar
mensajes (ej. notificaciones) en cualquier momento, no solo como respuesta
inmediata a algo que mandamos. Los mensajes leídos se van dejando en una
cola (`Queue`) que el cliente consume.
"""
import json
import queue
import subprocess
import threading
from typing import Any, Dict, List, Optional


class StdioTransport:
    def __init__(self, command: List[str], cwd: Optional[str] = None):
        self.command = command
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self._incoming: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _read_loop(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            self._incoming.put(message)

    def send(self, message: Dict[str, Any]) -> None:
        assert self.process and self.process.stdin
        line = json.dumps(message)
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def receive(self, timeout: Optional[float] = 30) -> Dict[str, Any]:
        try:
            return self._incoming.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("No se recibió respuesta del servidor MCP a tiempo.")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()