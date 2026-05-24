from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_type: str
    filename: str
    chunk_index: int
    text: str


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？；\n])")


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = [part.strip() for part in SENTENCE_BOUNDARY_RE.split(paragraph) if part.strip()]
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            for start in range(0, len(sentence), max_chars):
                piece = sentence[start : start + max_chars].strip()
                if piece:
                    chunks.append(piece)
            continue

        separator = "\n" if current else ""
        candidate = f"{current}{separator}{sentence}"
        if len(candidate) > max_chars and current.strip():
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())
    return chunks


def _normalize_paragraphs(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    normalized: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            normalized.extend(_split_long_paragraph(paragraph, max_chars))
        else:
            normalized.append(paragraph)
    return normalized


def _make_chunk(text: str, filename: str, doc_type: str, index: int) -> Chunk:
    filename_stem = Path(filename).stem
    return Chunk(
        id=f"{doc_type}_{filename_stem}_chunk_{index}",
        doc_type=doc_type,
        filename=filename,
        chunk_index=index,
        text=text.strip(),
    )


def chunk_document(
    text: str,
    filename: str,
    doc_type: str,
    target_chars: int = 800,
    max_chars: int = 1000,
) -> list[Chunk]:
    """Split parsed document text into stable chunks."""
    if not text or not text.strip():
        return []
    if target_chars <= 0 or max_chars <= 0:
        raise ValueError("target_chars and max_chars must be positive")
    if target_chars > max_chars:
        raise ValueError("target_chars must be less than or equal to max_chars")

    paragraphs = _normalize_paragraphs(text, max_chars)
    raw_chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        separator = "\n\n" if current else ""
        candidate = f"{current}{separator}{paragraph}"
        if current and len(candidate) > target_chars:
            raw_chunks.append(current.strip())
            current = paragraph
        else:
            current = candidate

    if current.strip():
        raw_chunks.append(current.strip())

    chunks: list[Chunk] = []
    for raw in raw_chunks:
        stripped = raw.strip()
        if stripped:
            chunks.append(_make_chunk(stripped, filename, doc_type, len(chunks)))
    return chunks
