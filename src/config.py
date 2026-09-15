"""
InfraMiner AI — Configuration

Loads environment variables from the project-root .env file and exposes
them as a simple Settings object for the rest of the codebase.

Usage
-----
    from src.config import settings

    llm = ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
    )

The module is safe to import even when .env is empty or the API key is
not yet configured — settings.google_api_key will simply be None, and
callers can check before making LLM calls.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Locate and load .env from the project root
# ---------------------------------------------------------------------------
# config.py lives at  <project_root>/src/config.py
# so the project root is one level up from this file's directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH)


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------

class Settings:
    """Central configuration for InfraMiner AI.

    All values are read from environment variables (loaded via .env).
    Defaults are provided so the module never crashes on import even
    when the .env file is empty.
    """

    def __init__(self) -> None:
        # -- Google Gemini / LLM -----------------------------------------
        self.google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
        self.google_model: str = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
        self.llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

        # -- Project paths -----------------------------------------------
        self.project_root: Path = _PROJECT_ROOT
        self.data_dir: Path = _PROJECT_ROOT / "data"
        self.documents_dir: Path = _PROJECT_ROOT / "documents"
        self.agents_dir: Path = _PROJECT_ROOT / "agents"

    @property
    def is_llm_configured(self) -> bool:
        """True when the Google API key has been set."""
        return self.google_api_key is not None and len(self.google_api_key.strip()) > 0

    def __repr__(self) -> str:
        key_status = "SET" if self.is_llm_configured else "NOT SET"
        return (
            f"Settings(\n"
            f"  google_api_key = {key_status},\n"
            f"  google_model   = {self.google_model!r},\n"
            f"  llm_temperature = {self.llm_temperature},\n"
            f"  project_root   = {self.project_root},\n"
            f"  data_dir       = {self.data_dir},\n"
            f"  documents_dir  = {self.documents_dir},\n"
            f"  agents_dir     = {self.agents_dir},\n"
            f")"
        )


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------
settings = Settings()

