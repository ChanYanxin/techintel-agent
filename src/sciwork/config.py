"""Configuration and immutable local input boundaries."""
import os
from pathlib import Path

ROOT = Path(os.getenv("SCIW_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))).resolve()
PAPERS = ROOT / "data" / "papers_demo.json"
EXPERIMENTS = ROOT / "data" / "experiments_demo.csv"


def model_mode() -> str:
    mode = os.getenv("SCIW_MODEL_MODE", "offline").lower()
    if mode not in {"offline", "openai"}:
        raise ValueError("SCIW_MODEL_MODE must be offline or openai")
    return mode


def use_mcp() -> bool:
    return os.getenv("SCIW_USE_MCP", "false").lower() in {"1", "yes", "true"}


def experiments_path() -> Path:
    return Path(os.getenv("SCIW_EXPERIMENTS_CSV", str(EXPERIMENTS))).resolve()
