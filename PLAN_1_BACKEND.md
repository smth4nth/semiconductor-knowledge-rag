# Plan 1: 后端核心 — 文档解析 + 向量检索 + RAG 问答

## 背景

为半导体工厂建立一个工艺知识库 RAG 系统。工程师上传 SOP、异常报告、FA Report、Alarm Code、客户 Spec 等文档，系统解析入库后可用自然语言查询。

本 Plan 只做后端核心模块，不做 Streamlit 界面（界面在 Plan 2）。

## 参考项目

本项目基于 `invest_rag` 项目改造。原项目是对一本书做 RAG 问答，使用 OpenAI + ChromaDB + Streamlit。本项目的主要改动：
- OpenAI → 通义千问（dashscope SDK）
- txt 单格式 → PDF/Word/Excel 多格式（unstructured 库）
- 一次性摄入 → 增量摄入（文件 hash 去重）
- 去掉加密模块（内部使用，不需要加密）

## 要创建的文件

```
semiconductor_knowledge_rag/
├── config.py
├── ingest/
│   ├── __init__.py
│   ├── parser.py
│   ├── chunker.py
│   └── registry.py
├── retrieval/
│   ├── __init__.py
│   └── search.py
├── rag_core.py
├── requirements.txt
├── .env.example
├── .gitignore
└── tests/
    ├── test_chunker.py
    └── test_rag_core.py
```

## 详细规格

### 1. `config.py` — 配置管理

```python
"""
从 .env 或环境变量读取配置。

需要的配置项：
- DASHSCOPE_API_KEY: 通义千问 API Key
- UPLOAD_DIR: 上传文档存放路径，默认 "data/uploads"
- CHROMA_DIR: ChromaDB 持久化路径，默认 "chroma_db"
- COLLECTION_NAME: ChromaDB collection 名称，默认 "semiconductor_knowledge"
- EMBEDDING_MODEL: 通义 embedding 模型，默认 "text-embedding-v3"
- CHAT_MODEL: 通义千问模型，默认 "qwen-plus"
- TOP_K: 检索返回数量，默认 5

用 python-dotenv 加载 .env 文件。
提供一个 get_config() 函数返回 dict，缺少 DASHSCOPE_API_KEY 时 raise RuntimeError。
"""
```

### 2. `ingest/parser.py` — 文档解析

```python
"""
用 unstructured 库解析 PDF / Word / Excel 文档为纯文本 elements。

核心函数：
    parse_document(file_path: str | Path) -> list[Element]
        - 根据文件后缀选择 unstructured 的 partition 函数：
          .pdf  → partition_pdf
          .docx → partition_docx
          .doc  → partition_doc
          .xlsx → partition_xlsx
          .xls  → partition_xls
        - 不支持的格式 raise ValueError
        - 返回 unstructured 的 Element 列表

    extract_text(file_path: str | Path) -> str
        - 调用 parse_document，将所有 element 的 text 拼接为纯文本
        - 空文档 raise ValueError

    detect_doc_type(filename: str) -> str
        - 根据文件名关键词猜测文档类型：
          包含 "sop" (不区分大小写) → "SOP"
          包含 "异常" 或 "abnormal" → "异常报告"
          包含 "fa" 或 "failure" → "FA"
          包含 "alarm" → "Alarm"
          包含 "spec" → "Spec"
          都不匹配 → "其他"

注意：
- MVP 阶段不做 OCR，扫描件 PDF 如果 unstructured 解析出空文本，
  extract_text 应 raise ValueError("文档内容为空，可能是扫描件")
- 表格 element（Table 类型）保留其 text 表示，不丢弃
"""
```

### 3. `ingest/chunker.py` — 分块

```python
"""
将解析后的文档文本分块。

核心数据类：
    @dataclass
    class Chunk:
        id: str              # 格式: "{doc_type}_{filename_stem}_chunk_{index}"
        doc_type: str        # SOP / 异常报告 / FA / Alarm / Spec / 其他
        filename: str        # 原始文件名
        chunk_index: int     # 块序号，从 0 开始
        text: str            # 块文本内容

核心函数：
    chunk_document(
        text: str,
        filename: str,
        doc_type: str,
        target_chars: int = 800,
        max_chars: int = 1000,
    ) -> list[Chunk]

分块逻辑：
1. 按双换行 (\n\n) 拆分段落
2. 合并短段落，累积到 target_chars 时切一个 chunk
3. 单段落超过 max_chars 时，按中文句子边界拆分：。！？；\n
4. 不在 ，、处拆分
5. 去除空白 chunk（strip 后为空的跳过）

chunk id 格式示例：SOP_XX机台清洁_chunk_0, FA_晶圆破裂分析_chunk_3
（filename_stem 即去掉扩展名的文件名）
"""
```

### 4. `ingest/registry.py` — 文件去重与增量入库

```python
"""
管理已入库文档的注册表，基于文件内容 SHA-256 hash 去重。

注册表存储为 JSON 文件：data/registry.json
格式：
{
    "files": {
        "文件SHA256": {
            "filename": "XX机台SOP.pdf",
            "doc_type": "SOP",
            "chunk_count": 12,
            "ingested_at": "2024-03-15T10:30:00"
        }
    }
}

核心函数：
    compute_file_hash(file_path: str | Path) -> str
        - 返回文件内容的 SHA-256 hex digest

    load_registry(registry_path: str | Path = "data/registry.json") -> dict
        - 文件不存在时返回 {"files": {}}

    save_registry(registry: dict, registry_path: str | Path = "data/registry.json") -> None

    is_registered(file_hash: str, registry: dict) -> bool

    register_file(
        registry: dict,
        file_hash: str,
        filename: str,
        doc_type: str,
        chunk_count: int,
    ) -> dict
        - 添加记录，ingested_at 用当前时间 ISO 格式
        - 返回更新后的 registry

    get_registered_files(registry: dict) -> list[dict]
        - 返回所有已注册文件信息列表，方便前端展示
"""
```

### 5. `ingest/__init__.py` — 摄入入口

```python
"""
提供统一的摄入入口函数。

核心函数：
    ingest_file(
        file_path: str | Path,
        collection: chromadb.Collection,
        registry: dict,
        registry_path: str | Path = "data/registry.json",
    ) -> dict | None
        
        完整流程：
        1. compute_file_hash 检查是否已入库 → 已入库返回 None
        2. detect_doc_type 识别文档类型
        3. extract_text 解析文档
        4. chunk_document 分块
        5. 生成 embeddings（调用通义 text-embedding-v3）
        6. 写入 ChromaDB（documents, metadatas, embeddings）
        7. register_file 注册
        8. save_registry 保存
        9. 返回 {"filename": ..., "doc_type": ..., "chunk_count": ...}

    embed_texts(texts: list[str]) -> list[list[float]]
        - 调用 dashscope 的 TextEmbedding API
        - 模型: text-embedding-v3
        - 批量处理，每批最多 25 条（dashscope 限制）
        - 返回 embedding 向量列表

注意 dashscope embedding 调用方式：
    import dashscope
    from dashscope import TextEmbedding
    
    resp = TextEmbedding.call(
        model="text-embedding-v3",
        input=texts,          # list[str]
        api_key=api_key,
    )
    # resp.output["embeddings"] 是 list[dict]，每个有 "embedding" key
"""
```

### 6. `retrieval/search.py` — 向量检索

```python
"""
基于 ChromaDB 的向量检索。

核心函数：
    search(
        collection: chromadb.Collection,
        query: str,
        top_k: int = 5,
        doc_type_filter: str | None = None,
    ) -> list[dict]

    流程：
    1. 对 query 调用通义 embedding（复用 ingest 中的 embed_texts）
    2. 构建 ChromaDB where 条件：
       - doc_type_filter 不为 None 时：where={"doc_type": doc_type_filter}
    3. collection.query(query_embeddings=..., n_results=top_k, where=..., include=["documents", "metadatas", "distances"])
    4. 返回 list[dict]，每个 dict 包含：
       {
           "doc_type": str,
           "filename": str,
           "text": str,
           "distance": float,
       }

    get_collection() -> chromadb.Collection
        - 用 config 中的 CHROMA_DIR 和 COLLECTION_NAME
        - 返回 PersistentClient 的 get_or_create_collection
        - metadata: {"hnsw:space": "cosine"}
"""
```

### 7. `rag_core.py` — Prompt 构建 + LLM 调用

```python
"""
RAG 核心：构建 prompt 并调用通义千问。

SYSTEM_PROMPT = '''你是半导体工厂的工艺知识助手。请根据提供的参考资料回答问题。

要求：
1. 基于参考资料作答，不要编造信息。
2. 每个关键信息标注来源，格式为【文档类型 - 文件名】。
3. 如果资料不足以回答，请如实说明"未找到相关资料"。
4. 回答要准确、简洁、有条理。
5. 如果问题涉及操作步骤，请按步骤列出。
6. 支持中英文问答。'''

核心函数：
    build_messages(question: str, contexts: list[dict]) -> list[dict]
        - 将检索到的 contexts 格式化为参考内容
        - 每条 context 格式：【{doc_type} - {filename}】\n{text}
        - 拼接 system prompt + 参考内容 + 用户问题
        - 返回 messages list（role/content 格式）

    stream_chat(messages: list[dict]) -> Generator[str, None, None]
        - 调用通义千问流式 API
        - 使用 dashscope 的 Generation API：

          from dashscope import Generation
          
          responses = Generation.call(
              model="qwen-plus",
              messages=messages,
              result_format="message",
              stream=True,
              api_key=api_key,
          )
          for response in responses:
              # response.output.choices[0].message.content 是累积文本
              # 需要做增量提取（当前文本减去上次文本）
              yield delta_text

        - temperature: 0.3
        - max_tokens: 2000

    chat(messages: list[dict]) -> str
        - 非流式版本，返回完整回答字符串
        - 用于测试

注意 dashscope 流式返回的是累积文本，不是增量 delta。
需要自己维护上一次的文本来计算增量。
"""
```

### 8. `requirements.txt`

```
streamlit>=1.30.0
dashscope>=1.14.0
chromadb>=0.4.0
unstructured[all-docs]>=0.12.0
python-dotenv>=1.0.0
```

### 9. `.env.example`

```
DASHSCOPE_API_KEY=
UPLOAD_DIR=data/uploads
CHROMA_DIR=chroma_db
```

### 10. `.gitignore`

```
.env
chroma_db/
data/uploads/
data/registry.json
__pycache__/
*.pyc
.streamlit/secrets.toml
```

### 11. `tests/test_chunker.py`

测试 chunker.py 的分块逻辑：
- 测试正常分块：输入一段 2000 字文本，验证每个 chunk 不超过 max_chars
- 测试短文本：输入 100 字文本，验证生成 1 个 chunk
- 测试空文本：验证返回空列表
- 测试 chunk id 格式正确
- 测试中文句子边界拆分

### 12. `tests/test_rag_core.py`

测试 rag_core.py：
- 测试 build_messages 返回正确的 messages 结构
- 测试 build_messages 包含 system prompt
- 测试 context 格式化包含【文档类型 - 文件名】
- 测试空 contexts 列表也能正常构建

## 实施顺序

1. 创建项目目录结构 + requirements.txt + .env.example + .gitignore
2. config.py
3. ingest/parser.py
4. ingest/chunker.py + tests/test_chunker.py
5. ingest/registry.py
6. ingest/__init__.py（embed_texts + ingest_file）
7. retrieval/search.py
8. rag_core.py + tests/test_rag_core.py

## 重要约束

- 所有代码用 Python 3.10+ 语法
- 类型注解使用 `from __future__ import annotations`
- 文件编码统一 UTF-8
- 不要创建 app.py（在 Plan 2 中做）
- 不要创建 README.md
- dashscope API 调用方式参考上面的代码示例，不要用 openai 兼容模式
- ChromaDB 使用 PersistentClient，不要用 ephemeral
