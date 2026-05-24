from __future__ import annotations

from rag_core import SYSTEM_PROMPT, build_messages


def test_build_messages_returns_role_content_structure() -> None:
    messages = build_messages("如何清洁机台？", [])

    assert messages == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "参考资料：\n未检索到参考资料。\n\n用户问题：\n如何清洁机台？",
        },
    ]


def test_build_messages_contains_system_prompt() -> None:
    messages = build_messages("报警怎么处理？", [])

    assert messages[0]["role"] == "system"
    assert "半导体工厂的工艺知识助手" in messages[0]["content"]


def test_context_format_includes_source_marker() -> None:
    contexts = [
        {
            "doc_type": "SOP",
            "filename": "XX机台清洁.pdf",
            "text": "关闭气源后执行清洁。",
            "distance": 0.12,
        }
    ]

    messages = build_messages("清洁前要做什么？", contexts)

    assert "【SOP - XX机台清洁.pdf】" in messages[1]["content"]
    assert "关闭气源后执行清洁。" in messages[1]["content"]


def test_empty_contexts_build_normally() -> None:
    messages = build_messages("没有资料时如何回答？", [])

    assert len(messages) == 2
    assert "未检索到参考资料。" in messages[1]["content"]
