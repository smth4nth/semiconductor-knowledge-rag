from __future__ import annotations

from pathlib import Path
from typing import Any


class TextElement:
    def __init__(self, text: str) -> None:
        self.text = text


def _parse_pdf_with_pypdf(path: Path) -> list[TextElement]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    elements = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            elements.append(TextElement(text.strip()))
    return elements


def _has_text(elements: list[Any]) -> bool:
    return any(getattr(element, "text", "").strip() for element in elements)


def parse_document(file_path: str | Path) -> list[Any]:
    """Parse PDF, Word, or Excel documents with unstructured."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        from unstructured.partition.pdf import partition_pdf

        elements = list(partition_pdf(filename=str(path), strategy="fast"))
        if _has_text(elements):
            return elements
        return _parse_pdf_with_pypdf(path)
    if suffix == ".docx":
        from unstructured.partition.docx import partition_docx

        return list(partition_docx(filename=str(path)))
    if suffix == ".doc":
        from unstructured.partition.doc import partition_doc

        return list(partition_doc(filename=str(path)))
    if suffix == ".xlsx":
        from unstructured.partition.xlsx import partition_xlsx

        return list(partition_xlsx(filename=str(path)))
    if suffix == ".xls":
        from unstructured.partition.xls import partition_xls

        return list(partition_xls(filename=str(path)))

    raise ValueError(f"Unsupported document format: {suffix}")


def extract_text(file_path: str | Path) -> str:
    """Extract non-empty text from all parsed elements."""
    elements = parse_document(file_path)
    parts = []
    for element in elements:
        text = getattr(element, "text", None)
        if text and text.strip():
            parts.append(text.strip())

    content = "\n\n".join(parts).strip()
    if not content:
        raise ValueError("文档内容为空，可能是扫描件")
    return content


def detect_doc_type(filename: str) -> str:
    """Infer semiconductor document type from filename keywords."""
    name = filename.lower()
    if "sop" in name:
        return "SOP"
    if "异常" in filename or "abnormal" in name:
        return "异常报告"
    if "fa" in name or "failure" in name:
        return "FA"
    if "alarm" in name:
        return "Alarm"
    if "spec" in name:
        return "Spec"
    return "其他"
