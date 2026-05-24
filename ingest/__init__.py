from __future__ import annotations

from pathlib import Path
from typing import Any

from config import get_config
from ingest.chunker import Chunk, chunk_document
from ingest.parser import detect_doc_type, extract_text
from ingest.registry import (
    compute_file_hash,
    is_registered,
    register_file,
    save_registry,
)


BATCH_SIZE = 10


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts with DashScope TextEmbedding in batches."""
    if not texts:
        return []

    import dashscope
    from dashscope import TextEmbedding

    config = get_config()
    dashscope.api_key = config["DASHSCOPE_API_KEY"]
    embeddings: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = TextEmbedding.call(
            model=config["EMBEDDING_MODEL"],
            input=batch,
            api_key=config["DASHSCOPE_API_KEY"],
        )
        output = getattr(response, "output", None)
        if output is None and isinstance(response, dict):
            output = response.get("output")
        if not output or "embeddings" not in output:
            status_code = getattr(response, "status_code", None)
            code = getattr(response, "code", None)
            message = getattr(response, "message", None)
            if isinstance(response, dict):
                status_code = status_code or response.get("status_code")
                code = code or response.get("code")
                message = message or response.get("message")
            details = "，".join(str(part) for part in (status_code, code, message) if part)
            if details:
                raise RuntimeError(f"向量生成失败：{details}")
            raise RuntimeError("向量生成失败：DashScope 未返回 embeddings")
        items = output["embeddings"]
        embeddings.extend(item["embedding"] for item in items)

    return embeddings


def ingest_file(
    file_path: str | Path,
    collection: Any,
    registry: dict[str, Any],
    registry_path: str | Path = "data/registry.json",
) -> dict[str, Any] | None:
    """Parse, chunk, embed, persist, and register one document."""
    path = Path(file_path)
    file_hash = compute_file_hash(path)
    if is_registered(file_hash, registry):
        return None

    doc_type = detect_doc_type(path.name)
    text = extract_text(path)
    chunks = chunk_document(text=text, filename=path.name, doc_type=doc_type)
    if not chunks:
        raise ValueError("文档内容为空，可能是扫描件")

    embeddings = embed_texts([chunk.text for chunk in chunks])
    metadatas = [
        {
            "doc_type": chunk.doc_type,
            "filename": chunk.filename,
            "chunk_index": chunk.chunk_index,
            "file_hash": file_hash,
        }
        for chunk in chunks
    ]
    collection.add(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=metadatas,
        embeddings=embeddings,
    )

    register_file(registry, file_hash, path.name, doc_type, len(chunks))
    save_registry(registry, registry_path)
    return {"filename": path.name, "doc_type": doc_type, "chunk_count": len(chunks)}


__all__ = ["Chunk", "chunk_document", "embed_texts", "ingest_file"]
