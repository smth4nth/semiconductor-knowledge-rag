from __future__ import annotations

from typing import Any

import chromadb

from config import get_config
from ingest import embed_texts


def get_collection() -> Any:
    config = get_config()
    client = chromadb.PersistentClient(path=str(config["CHROMA_DIR"]))
    return client.get_or_create_collection(
        name=config["COLLECTION_NAME"],
        metadata={"hnsw:space": "cosine"},
    )


def search(
    collection: Any,
    query: str,
    top_k: int = 5,
    doc_type_filter: str | None = None,
) -> list[dict[str, Any]]:
    query_embedding = embed_texts([query])[0]
    where = {"doc_type": doc_type_filter} if doc_type_filter is not None else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    items: list[dict[str, Any]] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        metadata = metadata or {}
        items.append(
            {
                "doc_type": metadata.get("doc_type", ""),
                "filename": metadata.get("filename", ""),
                "text": document,
                "distance": distance,
            }
        )
    return items
