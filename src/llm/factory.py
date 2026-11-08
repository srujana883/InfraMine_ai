"""
InfraMiner AI - Provider-independent LLM factory.

The rest of the project should obtain LLMs through get_llm()
instead of directly constructing provider-specific LLM clients.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from src.config import settings


def get_llm() -> BaseChatModel:
    """
    Create the configured LLM provider.

    Supported providers:
        - groq
        - gemini
    """

    provider = settings.llm_provider.strip().lower()

    if provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured in the .env file."
            )

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=settings.llm_temperature,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured in the .env file."
            )

        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: '{settings.llm_provider}'. "
        "Supported providers are: groq, gemini."
    )