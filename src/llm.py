"""LLM wrapper with automatic provider detection and an OFFLINE fallback.

Priority:
  1. If LLM_MODE / API keys select a provider -> use that LLM.
  2. Otherwise run OFFLINE -- callers fall back to deterministic, rule-based
     logic grounded in real RAG retrieval, so the whole system runs without
     any API key or internet access (great for reproducible screenshots).
"""
from __future__ import annotations

from typing import Optional

from . import config

_PROVIDER: Optional[str] = None
_CLIENT = None


def _detect_provider() -> str:
    """Decide which backend to use, once, and cache it."""
    global _PROVIDER, _CLIENT
    if _PROVIDER is not None:
        return _PROVIDER

    mode = config.LLM_MODE
    if mode == "offline":
        _PROVIDER = "offline"
        return _PROVIDER

    # Explicit or auto Gemini
    if mode == "gemini" or (not mode and config.GOOGLE_API_KEY):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            _CLIENT = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", temperature=0.2,
                google_api_key=config.GOOGLE_API_KEY,
            )
            _PROVIDER = "gemini"
            return _PROVIDER
        except Exception as exc:  # pragma: no cover - depends on env
            print(f"[llm] Gemini init failed ({exc}); falling back to offline.")

    # Explicit or auto OpenAI
    if mode == "openai" or (not mode and config.OPENAI_API_KEY):
        try:
            from openai import OpenAI

            _CLIENT = OpenAI(api_key=config.OPENAI_API_KEY)
            _PROVIDER = "openai"
            return _PROVIDER
        except Exception as exc:  # pragma: no cover
            print(f"[llm] OpenAI init failed ({exc}); falling back to offline.")

    _PROVIDER = "offline"
    return _PROVIDER


def provider() -> str:
    """Return the active provider name: 'gemini' | 'openai' | 'offline'."""
    return _detect_provider()


def is_offline() -> bool:
    return provider() == "offline"


def generate(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Return the LLM completion, or None when running offline.

    Callers MUST handle a None result by using their deterministic fallback.
    """
    prov = _detect_provider()
    if prov == "offline":
        return None

    try:
        if prov == "gemini":
            msg = _CLIENT.invoke(
                [("system", system_prompt), ("human", user_prompt)]
            )
            return (msg.content or "").strip()

        if prov == "openai":
            resp = _CLIENT.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # pragma: no cover
        print(f"[llm] generation failed ({exc}); using offline fallback.")
        return None

    return None
