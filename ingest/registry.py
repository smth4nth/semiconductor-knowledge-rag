from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = Path("data/registry.json")


def compute_file_hash(file_path: str | Path) -> str:
    sha256 = hashlib.sha256()
    with Path(file_path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)
    return sha256.hexdigest()


def load_registry(registry_path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    path = Path(registry_path)
    if not path.exists():
        return {"files": {}}
    with path.open("r", encoding="utf-8") as file:
        registry = json.load(file)
    registry.setdefault("files", {})
    return registry


def save_registry(registry: dict[str, Any], registry_path: str | Path = DEFAULT_REGISTRY_PATH) -> None:
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(registry, file, ensure_ascii=False, indent=2)


def is_registered(file_hash: str, registry: dict[str, Any]) -> bool:
    return file_hash in registry.get("files", {})


def register_file(
    registry: dict[str, Any],
    file_hash: str,
    filename: str,
    doc_type: str,
    chunk_count: int,
) -> dict[str, Any]:
    registry.setdefault("files", {})
    registry["files"][file_hash] = {
        "filename": filename,
        "doc_type": doc_type,
        "chunk_count": chunk_count,
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
    }
    return registry


def get_registered_files(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return list(registry.get("files", {}).values())
