from __future__ import annotations

from ingest.chunker import chunk_document


def test_normal_chunking_keeps_chunks_under_max_chars() -> None:
    text = "\n\n".join(["这是一段工艺说明。" * 30 for _ in range(8)])

    chunks = chunk_document(text, "XX机台SOP.pdf", "SOP", target_chars=300, max_chars=500)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 500 for chunk in chunks)


def test_short_text_generates_one_chunk() -> None:
    text = "这是一段很短的 SOP 内容，用于验证短文本不会被过度拆分。"

    chunks = chunk_document(text, "short_sop.pdf", "SOP")

    assert len(chunks) == 1
    assert chunks[0].text == text


def test_empty_text_returns_empty_list() -> None:
    assert chunk_document("   \n\n ", "empty.pdf", "其他") == []


def test_chunk_id_format_is_correct() -> None:
    chunks = chunk_document("第一段内容。\n\n第二段内容。", "XX机台清洁.pdf", "SOP", target_chars=10)

    assert chunks[0].id == "SOP_XX机台清洁_chunk_0"
    assert chunks[0].filename == "XX机台清洁.pdf"
    assert chunks[0].chunk_index == 0


def test_long_chinese_paragraph_splits_on_sentence_boundaries() -> None:
    text = "第一句内容很重要。" * 20 + "第二句内容也很重要！" * 20

    chunks = chunk_document(text, "晶圆破裂分析.docx", "FA", target_chars=80, max_chars=120)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 120 for chunk in chunks)
    assert all(not chunk.text.endswith(("，", "、")) for chunk in chunks)
