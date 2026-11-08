"""
InfraMiner AI — Configuration

Loads environment variables from the project-root .env file and exposes
them as a simple Settings object for the rest of the codebase.

The LLM provider is configurable so agents do not depend directly on
Gemini or Groq. Supported providers:
    - groq
    - gemini
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Locate and load .env from the project root
# ---------------------------------------------------------------------------
# config.py lives at <project_root>/src/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH)


# ---------------------------------------------------------------------------
# Settings container
# ---------------------------------------------------------------------------

class Settings:
    """Central configuration for InfraMiner AI."""

    def __init__(self) -> None:
        # -- LLM provider ------------------------------------------------
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")

        # -- Google Gemini -----------------------------------------------
        self.google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
        self.google_model: str = os.getenv(
            "GOOGLE_MODEL",
            "gemini-2.0-flash",
        )

        # -- Groq --------------------------------------------------------
        self.groq_api_key: str | None = os.getenv("GROQ_API_KEY")
        self.groq_model: str = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b",
        )

        # -- Shared LLM settings ----------------------------------------
        self.llm_temperature: float = float(
            os.getenv("LLM_TEMPERATURE", "0.2")
        )

        # -- Project paths ----------------------------------------------
        self.project_root: Path = _PROJECT_ROOT
        self.data_dir: Path = _PROJECT_ROOT / "data"
        self.documents_dir: Path = _PROJECT_ROOT / "documents"
        self.agents_dir: Path = _PROJECT_ROOT / "agents"

    @property
    def is_llm_configured(self) -> bool:
        """True when the selected LLM provider has an API key configured."""

        if self.llm_provider.lower() == "groq":
            return (
                self.groq_api_key is not None
                and len(self.groq_api_key.strip()) > 0
            )

        if self.llm_provider.lower() == "gemini":
            return (
                self.google_api_key is not None
                and len(self.google_api_key.strip()) > 0
            )

        return False

    def __repr__(self) -> str:
        provider = self.llm_provider.lower()

        if provider == "groq":
            key_status = (
                "SET"
                if self.groq_api_key
                and self.groq_api_key.strip()
                else "NOT SET"
            )
        elif provider == "gemini":
            key_status = (
                "SET"
                if self.google_api_key
                and self.google_api_key.strip()
                else "NOT SET"
            )
        else:
            key_status = "UNKNOWN PROVIDER"

        return (
            f"Settings(\n"
            f"  llm_provider   = {self.llm_provider!r},\n"
            f"  api_key        = {key_status},\n"
            f"  google_model   = {self.google_model!r},\n"
            f"  groq_model     = {self.groq_model!r},\n"
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