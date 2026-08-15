"""
Carga de configuración desde variables de entorno (.env).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_key: str
    model: str
    log_file: Path


def load_config() -> Config:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("No se encontró ANTHROPIC_API_KEY. Verificar .env")

    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4.5")

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    return Config(
        api_key=api_key,
        model=model,
        log_file=log_dir / "interactions.jsonl",
    )
