"""
Prepara el workspace usado por los servidores MCP de Filesystem y Git
(Fase 3). Se ejecuta solo una vez al arrancar el chatbot, antes de lanzar los
servidores MCP -- fuera del protocolo MCP en sí.
"""
import subprocess
from pathlib import Path


def ensure_workspace(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_git_repo(path: Path) -> None:
    """
    Se asegura de que `path` sea un repositorio git válido antes de lanzar
    el servidor MCP de git.

    Nota: Git oficial no puede hacer "git innit", sino que tiene que estar el repo ya iniciado, y lo demás sí se puede hacer :)
    """
    if (path / ".git").exists():
        return

    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    # Identidad mínima para que "git commit" no falle en un entorno limpio
    subprocess.run(["git", "-C", str(path), "config", "user.email", "chatbot@proyecto1.local"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Proyecto1 Chatbot"], check=True)
