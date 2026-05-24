from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from config import get_config
from ingest import ingest_file
from ingest.registry import get_registered_files, load_registry
from retrieval.search import get_collection, search
from rag_core import build_messages, stream_chat


REGISTRY_PATH = Path("data/registry.json")
DOC_TYPE_OPTIONS = ["全部", "SOP", "异常报告", "FA", "Alarm", "Spec", "其他"]


def get_type_pill_class(doc_type: str) -> str:
    if doc_type == "Spec":
        return "type-pill type-spec"
    if doc_type in {"异常报告", "FA", "Alarm"}:
        return "type-pill type-hauler"
    return "type-pill"


def apply_layout_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #FF8400;
            --primary-foreground: #FFFFFF;
            --background: #F2F3F0;
            --foreground: #111111;
            --muted-foreground: #111111;
            --card: #FFFFFF;
            --border: #CBCCC9;
            --sidebar: #E7E8E5;
            --sidebar-border: #CBCCC9;
            --sidebar-accent: #CBCCC9;
            --sidebar-foreground: #111111;
            --sidebar-accent-foreground: #18181B;
            --secondary: #E7E8E5;
            --muted: #F2F3F0;
            --user-bubble: #EFF6FF;
            --user-bubble-text: #111111;
            --assistant-bubble: #FFFFFF;
            --assistant-bubble-border: #CBCCC9;
            --success-bg: #DFE6E1;
            --success-text: #111111;
            --warning-bg: #E9E3D8;
            --warning-text: #111111;
            --error-bg: #E5DCDA;
            --error-text: #111111;
        }

        html,
        body,
        .stApp,
        .stApp * {
            font-family: Geist, "JetBrains Mono", "Noto Sans SC", "Microsoft YaHei", sans-serif;
            letter-spacing: 0;
        }

        .stApp {
            color: var(--foreground) !important;
        }

        .stApp p,
        .stApp span,
        .stApp div,
        .stApp label,
        .stApp a,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp th,
        .stApp td,
        .stApp textarea,
        .stApp button,
        .stApp input {
            color: var(--foreground) !important;
        }

        .stApp {
            background: var(--background);
        }

        [data-testid="stHeader"] {
            display: none;
        }

        [data-testid="stToolbar"] {
            display: none;
        }

        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stAppViewContainer"] {
            min-width: 1440px;
        }

        [data-testid="stMain"] {
            background: var(--background);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: none;
            padding: 32px;
            padding-bottom: 32px;
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--sidebar-border);
            min-width: 280px !important;
            width: 280px !important;
        }

        [data-testid="stSidebar"] > div {
            padding: 0;
        }

        [data-testid="stSidebarHeader"] {
            display: none;
        }

        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebar"] [data-testid="stElementContainer"],
        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            margin: 0 !important;
            padding: 0 !important;
            width: 280px !important;
        }

        [data-testid="stSidebarUserContent"] {
            transform: translateX(-10px);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
        }

        .app-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--foreground);
            font-size: 18px;
            font-weight: 700;
            border-bottom: 1px solid var(--border);
            height: 88px;
            margin: 0;
            padding: 24px 32px;
            width: 280px;
        }

        .app-brand-icon {
            align-items: center;
            background: var(--primary);
            border-radius: 9999px;
            color: var(--primary-foreground);
            display: inline-flex;
            height: 32px;
            justify-content: center;
            width: 32px;
        }

        .sidebar-section-title {
            color: var(--sidebar-foreground);
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif;
            font-size: 14px;
            line-height: 16px;
            margin: 24px 16px 0;
            padding: 16px;
            width: 248px;
        }

        [data-testid="stSidebar"] .stRadio > div {
            gap: 0;
            padding: 0 16px;
        }

        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
            border-radius: 9999px;
            color: var(--sidebar-accent-foreground) !important;
            height: 48px;
            padding: 12px 16px;
            transition: background 120ms ease, color 120ms ease;
            width: 248px;
        }

        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {
            background: var(--sidebar-accent);
            color: var(--sidebar-accent-foreground);
            font-weight: 400;
        }

        [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:disabled) {
            cursor: not-allowed;
            opacity: 0.55;
        }

        [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
            color: var(--sidebar-accent-foreground) !important;
            font-size: 16px;
            line-height: 24px;
            margin: 0;
        }


        .page-title {
            align-items: center;
            display: flex;
            justify-content: space-between;
            margin-bottom: 24px;
            min-height: 32px;
        }

        .page-title h1,
        .chat-title {
            color: var(--foreground);
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
            font-weight: 600;
            letter-spacing: 0;
            line-height: 1.3;
            margin: 0 0 6px;
        }

        .page-title h1 {
            font-size: 22px !important;
            margin: 0;
        }

        .chat-title {
            font-size: 20px !important;
        }

        .page-title p {
            color: var(--muted-foreground);
            font-size: 13px;
            font-family: Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
            line-height: 1.5;
            margin: 0;
        }

        .section-heading {
            color: var(--foreground) !important;
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            line-height: 22px !important;
            margin: 0 0 16px !important;
        }

        [data-testid="stFileUploader"] {
            margin: 0;
            padding: 0;
            width: 100%;
        }

        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p {
            color: var(--foreground) !important;
            font-size: 15px !important;
        }

        [data-testid="stFileUploader"] section {
            align-items: center;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            height: 160px;
            justify-content: center;
            min-height: 160px;
            width: 100%;
        }

        [data-testid="stFileUploaderDropzone"] {
            align-items: center;
            background: transparent !important;
            border: 0 !important;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 10px;
            height: 160px !important;
            justify-content: center;
            min-height: 160px !important;
            width: 100% !important;
        }

        [data-testid="stFileUploaderDropzone"] > div {
            align-items: center;
            display: flex;
            flex-direction: column;
            gap: 10px;
            justify-content: center;
            min-width: 0;
        }

        [data-testid="stFileUploaderDropzone"] button {
            align-items: center !important;
            background: var(--primary) !important;
            border: 0 !important;
            border-radius: 999px !important;
            color: var(--primary-foreground) !important;
            display: inline-flex !important;
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            height: 40px !important;
            justify-content: center !important;
            line-height: 20px !important;
            min-width: 96px !important;
            padding: 10px 16px !important;
            white-space: nowrap !important;
            width: auto !important;
        }

        [data-testid="stFileUploaderDropzone"] button p {
            color: var(--primary-foreground) !important;
            font-size: 14px !important;
            line-height: 20px !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        .stButton > button,
        .stButton > button[kind="primary"] {
            background: var(--primary);
            border: 0;
            border-radius: 9999px;
            color: var(--primary-foreground);
            font-size: 14px;
            font-weight: 600;
            min-height: 40px;
            padding: 10px 18px;
        }

        .stButton > button:hover,
        .stButton > button[kind="primary"]:hover {
            background: #E77700;
            border: 0;
            color: var(--primary-foreground);
        }

        .docs-table {
            border: 1px solid var(--border);
            border-collapse: collapse;
            border-radius: 0;
            border-spacing: 0;
            color: var(--foreground);
            font-size: 14px;
            height: 549px;
            overflow: hidden;
            width: 100%;
        }

        .docs-table th,
        .docs-table td {
            border-bottom: 1px solid var(--border);
            color: var(--foreground);
            height: 44px;
            line-height: 20px;
            padding: 12px 14px;
            text-align: left;
            vertical-align: middle;
        }

        .docs-table tr:last-child td {
            border-bottom: 1px solid var(--border);
        }

        .docs-table th {
            background: var(--secondary);
            color: var(--muted-foreground) !important;
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif !important;
            font-weight: 400 !important;
        }

        .docs-table td {
            color: var(--foreground) !important;
            font-weight: 400;
            height: 56px;
        }

        .docs-table .filename-col {
            width: 320px;
        }

        .docs-table .doc-type-col {
            width: 120px;
        }

        .docs-table .chunk-count-col {
            width: 100px;
        }

        .type-pill {
            background: var(--success-bg);
            border-radius: 9999px;
            color: var(--success-text);
            display: inline-flex;
            font-family: "JetBrains Mono", Geist, "Noto Sans SC", "Microsoft YaHei", sans-serif;
            font-size: 12px;
            font-weight: 400;
            padding: 4px 10px;
        }

        .type-pill.type-hauler {
            background: #DFDFE6;
            color: var(--foreground);
        }

        .type-pill.type-spec {
            background: var(--warning-bg);
            color: var(--warning-text);
        }

        .section-header {
            align-items: center;
            display: flex;
            height: 23px;
            justify-content: space-between;
            margin: 24px 0;
        }

        .upload-screen {
            display: flex;
            flex-direction: column;
            gap: 16px;
            width: 100%;
        }

        .element-container:has(.upload-screen) {
            margin-top: -16px;
        }

        .upload-screen .page-title {
            margin: 0;
        }

        .upload-screen .section-header {
            margin: 0;
        }

        .element-container:has(.upload-screen) + .element-container {
            margin-top: 16px;
        }

        .upload-rest {
            display: flex;
            flex-direction: column;
            gap: 24px;
            margin-top: 24px;
            width: 100%;
        }

        .upload-rest .section-header {
            margin: 0;
        }

        .chat-topbar {
            align-items: center;
            border-bottom: 1px solid var(--border);
            box-sizing: border-box;
            display: flex;
            height: 64px;
            justify-content: space-between;
            min-height: 64px;
            padding: 16px 32px;
            width: 1160px;
        }

        .chat-title {
            margin: 0;
        }

        .design-filter {
            align-items: center;
            display: flex;
            gap: 12px;
            height: 36px;
            width: 228px;
        }

        .design-filter span {
            color: var(--muted-foreground);
            font-size: 14px;
            line-height: 20px;
        }

        .design-filter strong {
            align-items: center;
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--foreground);
            display: inline-flex;
            font-size: 14px;
            font-weight: 400;
            height: 36px;
            padding: 8px 28px 8px 12px;
            position: relative;
            width: 160px;
        }

        .design-filter em {
            color: var(--foreground);
            font-size: 12px;
            font-style: normal;
            margin-left: -34px;
            z-index: 1;
        }

        .chat-divider {
            display: none;
        }

        .chat-surface {
            box-sizing: border-box;
            height: 760px;
            padding: 24px 32px;
            width: 100%;
        }

        [data-testid="stChatMessage"] {
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 16px;
            padding: 12px 16px;
        }

        [data-testid="stChatMessageAvatarUser"],
        [data-testid="stChatMessageAvatarAssistant"] {
            display: none !important;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: var(--user-bubble);
            border: 0;
            color: var(--user-bubble-text) !important;
            margin-left: 120px;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
            color: var(--user-bubble-text) !important;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background: var(--assistant-bubble);
            border: 1px solid var(--assistant-bubble-border);
            color: var(--foreground);
            margin-right: 120px;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) * {
            color: var(--foreground) !important;
        }

        [data-testid="stChatInput"] {
            background: var(--background);
            border-top: 1px solid var(--border);
            padding: 16px 32px;
        }

        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"],
        [data-testid="stBottomBlockContainer"] + div,
        [data-testid="stBottom"] div:has(> [data-testid="stBottomBlockContainer"]) {
            background: var(--background) !important;
        }

        [data-testid="stBottomBlockContainer"] {
            padding: 0 !important;
        }

        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] > div > div,
        [data-testid="stChatInput"] [data-baseweb="textarea"],
        [data-testid="stChatInput"] [data-baseweb="base-input"],
        [data-testid="stChatInput"] [data-baseweb="base-input"] > div {
            background: var(--background) !important;
            border-color: var(--border) !important;
            color: var(--foreground) !important;
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInputTextArea"] {
            background: var(--background) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            color: var(--foreground) !important;
            min-height: 44px;
        }

        [data-testid="stChatInputTextArea"]::placeholder {
            color: var(--muted-foreground) !important;
            opacity: 1 !important;
        }

        [data-testid="stChatInputSubmitButton"] {
            background: var(--primary) !important;
            border: 0 !important;
            color: var(--primary-foreground) !important;
        }

        [data-testid="stChatInputSubmitButton"] svg,
        [data-testid="stChatInputSubmitButton"] path {
            color: var(--primary-foreground) !important;
            fill: currentColor !important;
            stroke: currentColor !important;
        }

        .empty-state {
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--muted-foreground);
            font-size: 14px;
            padding: 20px;
        }

        .element-container:has(.chat-topbar),
        .element-container:has(.chat-surface) {
            margin-left: -32px;
            margin-right: -32px;
            width: calc(100% + 64px) !important;
        }

        .element-container:has(.chat-topbar) {
            margin-top: -48px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def init_app() -> tuple[dict[str, Any], Any]:
    """Initialize shared app resources once per Streamlit process."""
    config = get_config()
    collection = get_collection()
    return config, collection


def handle_upload(uploaded_files: list[Any], collection: Any, registry: dict[str, Any], upload_dir: Path) -> None:
    """Save uploaded files, ingest them, and render per-file results."""
    if not uploaded_files:
        return

    upload_dir.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str]] = []
    for uploaded_file in uploaded_files:
        destination = upload_dir / uploaded_file.name
        with st.spinner(f"正在处理 {uploaded_file.name}..."):
            try:
                destination.write_bytes(uploaded_file.getbuffer())
                result = ingest_file(destination, collection, registry, REGISTRY_PATH)
            except Exception as exc:  # Streamlit should keep processing other files.
                results.append(("error", f"{uploaded_file.name} — 入库失败：{exc}"))
                continue

        if result is None:
            results.append(("info", f"{uploaded_file.name} — 已存在，跳过"))
        else:
            results.append(
                (
                    "success",
                    f"{result['filename']} — 入库成功（{result['chunk_count']} 个文本块）",
                )
            )

    for status, message in results:
        if status == "success":
            st.success(message)
        elif status == "info":
            st.info(message)
        else:
            st.error(message)


def build_registered_docs_table(registry: dict[str, Any]) -> str:
    """Build registered documents table HTML."""
    files = get_registered_files(registry)
    if not files:
        return '<div class="empty-state">暂无文档，请先上传。</div>'

    rows = []
    for item in sorted(files, key=lambda value: value.get("filename", "")):
        filename = escape(str(item.get("filename", "未知文件")))
        doc_type = escape(str(item.get("doc_type", "其他")))
        chunk_count = escape(str(item.get("chunk_count", "")))
        ingested_at = escape(str(item.get("ingested_at", ""))[:10])
        pill_class = get_type_pill_class(str(item.get("doc_type", "其他")))
        rows.append(
            f"""
            <tr>
                <td class="filename-col">{filename}</td>
                <td class="doc-type-col"><span class="{pill_class}">{doc_type}</span></td>
                <td class="chunk-count-col">{chunk_count}</td>
                <td>{ingested_at}</td>
            </tr>
            """
        )

    return f"""
        <table class="docs-table">
            <thead>
                <tr>
                    <th class="filename-col">文件名</th>
                    <th class="doc-type-col">文档类型</th>
                    <th class="chunk-count-col">文本块数</th>
                    <th>入库时间</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """


def render_registered_docs(registry: dict[str, Any]) -> None:
    """Render registered documents as a compact table."""
    st.html(build_registered_docs_table(registry))


def render_chat(collection: Any, config: dict[str, Any], doc_type_filter: str | None, has_documents: bool) -> None:
    """Render chat history, input box, retrieval, and streaming answer."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not has_documents:
        st.markdown(
            '<div class="empty-state">📭 知识库为空，请先到“文档上传”页面上传文档。</div>',
            unsafe_allow_html=True,
        )
        return

    chat_history = st.container()
    with chat_history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    question = st.chat_input("请输入您的问题，例如：XX机台的清洁SOP是什么？")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with chat_history:
        with st.chat_message("user"):
            st.markdown(question)

    with chat_history:
        with st.chat_message("assistant"):
            try:
                contexts = search(
                    collection,
                    question,
                    top_k=config["TOP_K"],
                    doc_type_filter=doc_type_filter,
                )
            except Exception:
                st.error("AI 服务暂时不可用，请稍后再试")
                return

            if not contexts:
                answer = "未找到相关资料，请尝试换个关键词或检查是否已上传相关文档。"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                return

            messages = build_messages(question, contexts)
            placeholder = st.empty()
            collected = ""
            try:
                for delta in stream_chat(messages):
                    collected += delta
                    placeholder.markdown(collected)
            except Exception:
                st.error("AI 服务暂时不可用，请稍后再试")
                return

            st.session_state.messages.append({"role": "assistant", "content": collected})


def render_upload_page(collection: Any, config: dict[str, Any], registry: dict[str, Any]) -> None:
    """Render the document upload and registry management page."""
    st.html(
        f"""
        <div class="upload-screen">
            <div class="page-title">
                <h1>文档上传</h1>
                <p>上传并管理半导体工艺相关文档</p>
            </div>
        </div>
        """
    )
    uploaded_files = st.file_uploader(
        "拖拽文件至此或点击上传",
        help="支持 PDF / Word / Excel",
        type=["pdf", "docx", "doc", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    handle_upload(uploaded_files, collection, registry, config["UPLOAD_DIR"])
    st.html(
        f"""
        <div class="upload-rest">
            <div class="section-header">
                <h2 class="section-heading">已入库文档</h2>
            </div>
            {build_registered_docs_table(load_registry(REGISTRY_PATH))}
        </div>
        """
    )


def render_search_page(collection: Any, config: dict[str, Any], registry: dict[str, Any]) -> None:
    """Render the retrieval filter and chat page."""
    topbar_title, topbar_filter = st.columns([4, 1])
    with topbar_title:
        st.markdown('<div class="chat-title">知识检索</div>', unsafe_allow_html=True)
    with topbar_filter:
        selected_doc_type = st.selectbox(
            "文档类型",
            DOC_TYPE_OPTIONS,
            index=0,
            key="doc_type_filter",
        )
    doc_type_filter = None if selected_doc_type == "全部" else selected_doc_type

    st.markdown('<div class="chat-surface">', unsafe_allow_html=True)
    render_chat(
        collection=collection,
        config=config,
        doc_type_filter=doc_type_filter,
        has_documents=bool(get_registered_files(registry)),
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> str:
    """Render the fixed navigation and return the selected page."""
    if "page" in st.query_params:
        st.query_params.clear()

    page_options = ["文档上传", "知识检索"]
    page = st.session_state.get("active_page", "文档上传")
    if page not in page_options:
        page = "文档上传"

    def active_class(label: str) -> str:
        return "active" if page == label else ""

    with st.sidebar:
        st.markdown(
            f"""
            <div class="app-brand">
                <span class="app-brand-icon"></span>
                <span>LUNARIS</span>
            </div>
            <div class="sidebar-section-title">知识库工作台</div>
            """,
            unsafe_allow_html=True,
        )
        page = st.radio(
            "导航",
            page_options,
            index=page_options.index(page),
            key="active_page",
            label_visibility="collapsed",
        )
        return page


def main() -> None:
    st.set_page_config(
        page_title="半导体工艺知识助手",
        page_icon="🔬",
        layout="wide",
    )
    apply_layout_styles()

    try:
        config, collection = init_app()
    except RuntimeError as exc:
        st.error(f"配置错误：{exc}")
        st.stop()

    page = render_sidebar()

    if page == "文档上传":
        render_upload_page(collection, config, load_registry(REGISTRY_PATH))
    elif page == "知识检索":
        render_search_page(collection, config, load_registry(REGISTRY_PATH))


if __name__ == "__main__":
    main()
