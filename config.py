from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _get_streamlit_secret(name: str) -> str | None:
    """Read a top-level Streamlit secret when running on Streamlit Cloud."""
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return None
    if value is None:
        return None
    return str(value)


def _get_setting(name: str, default: str | None = None) -> str | None:
    return os.getenv(name) or _get_streamlit_secret(name) or default


def get_config() -> dict[str, Any]:
    """Load application configuration from .env, environment variables, or Streamlit secrets."""
    load_dotenv()

    api_key = _get_setting("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is required. On Streamlit Cloud, add it in App settings > Secrets."
        )

    return {
        "DASHSCOPE_API_KEY": api_key,
        "UPLOAD_DIR": Path(_get_setting("UPLOAD_DIR", "data/uploads") or "data/uploads"),
        "CHROMA_DIR": Path(_get_setting("CHROMA_DIR", "chroma_db") or "chroma_db"),
        "COLLECTION_NAME": _get_setting("COLLECTION_NAME", "semiconductor_knowledge"),
        "EMBEDDING_MODEL": _get_setting("EMBEDDING_MODEL", "text-embedding-v3"),
        "CHAT_MODEL": _get_setting("CHAT_MODEL", "qwen-plus"),
        "TOP_K": int(_get_setting("TOP_K", "5") or "5"),
    }
