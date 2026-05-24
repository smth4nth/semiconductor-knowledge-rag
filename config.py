from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def get_config() -> dict[str, Any]:
    """Load application configuration from .env and environment variables."""
    load_dotenv()

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required")

    return {
        "DASHSCOPE_API_KEY": api_key,
        "UPLOAD_DIR": Path(os.getenv("UPLOAD_DIR", "data/uploads")),
        "CHROMA_DIR": Path(os.getenv("CHROMA_DIR", "chroma_db")),
        "COLLECTION_NAME": os.getenv("COLLECTION_NAME", "semiconductor_knowledge"),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "text-embedding-v3"),
        "CHAT_MODEL": os.getenv("CHAT_MODEL", "qwen-plus"),
        "TOP_K": int(os.getenv("TOP_K", "5")),
    }
