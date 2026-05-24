from __future__ import annotations

from collections.abc import Generator
from typing import Any

from config import get_config


SYSTEM_PROMPT = """你是半导体工厂的工艺知识助手。请根据提供的参考资料回答问题。

要求：
1. 基于参考资料作答，不要编造信息。
2. 每个关键信息标注来源，格式为【文档类型 - 文件名】。
3. 如果资料不足以回答，请如实说明"未找到相关资料"。
4. 回答要准确、简洁、有条理。
5. 如果问题涉及操作步骤，请按步骤列出。
6. 支持中英文问答。"""


def _format_contexts(contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return "未检索到参考资料。"

    formatted = []
    for context in contexts:
        doc_type = context.get("doc_type", "未知类型")
        filename = context.get("filename", "未知文件")
        text = context.get("text", "")
        formatted.append(f"【{doc_type} - {filename}】\n{text}")
    return "\n\n".join(formatted)


def build_messages(question: str, contexts: list[dict[str, Any]]) -> list[dict[str, str]]:
    reference = _format_contexts(contexts)
    user_content = f"参考资料：\n{reference}\n\n用户问题：\n{question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _extract_message_content(response: Any) -> str:
    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")

    choices = output["choices"]
    message = choices[0]["message"] if isinstance(choices[0], dict) else choices[0].message
    if isinstance(message, dict):
        return message.get("content", "")
    return getattr(message, "content", "")


def stream_chat(messages: list[dict[str, str]]) -> Generator[str, None, None]:
    from dashscope import Generation

    config = get_config()
    responses = Generation.call(
        model=config["CHAT_MODEL"],
        messages=messages,
        result_format="message",
        stream=True,
        api_key=config["DASHSCOPE_API_KEY"],
        temperature=0.3,
        max_tokens=2000,
    )

    previous = ""
    for response in responses:
        current = _extract_message_content(response)
        if current.startswith(previous):
            delta = current[len(previous) :]
        else:
            delta = current
        previous = current
        if delta:
            yield delta


def chat(messages: list[dict[str, str]]) -> str:
    from dashscope import Generation

    config = get_config()
    response = Generation.call(
        model=config["CHAT_MODEL"],
        messages=messages,
        result_format="message",
        api_key=config["DASHSCOPE_API_KEY"],
        temperature=0.3,
        max_tokens=2000,
    )
    return _extract_message_content(response)
