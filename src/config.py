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
    llm_provider: str          # "ollama" | "anthropic"
    anthropic_api_key: str
    anthropic_model: str
    ollama_model: str
    ollama_base_url: str
    workspace_dir: Path        # carpeta que usan Filesystem/Git MCP (Fase 3)
    log_file: Path


def load_config() -> Config:
    llm_provider = os.environ.get("LLM_PROVIDER", "ollama").lower()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    workspace_dir = Path(os.environ.get("MCP_WORKSPACE_DIR", "mcp_workspace")).resolve()

    return Config(
        llm_provider=llm_provider,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
        ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        workspace_dir=workspace_dir,
        log_file=log_dir / "interactions.jsonl",
    )
