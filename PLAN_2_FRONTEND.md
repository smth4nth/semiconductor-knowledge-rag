# Plan 2: 前端界面 — Streamlit 文档上传 + 问答聊天

## 前提

Plan 1 的后端核心模块已全部完成，以下文件已存在且可直接 import：

- `config.py` — get_config() 返回配置 dict
- `ingest/__init__.py` — ingest_file(file_path, collection, registry, registry_path) 完成解析+分块+入库
- `ingest/registry.py` — load_registry(), save_registry(), get_registered_files()
- `retrieval/search.py` — search(collection, query, top_k, doc_type_filter), get_collection()
- `rag_core.py` — build_messages(question, contexts), stream_chat(messages)

## 要创建的文件

```
semiconductor_knowledge_rag/
├── app.py                      # Streamlit 主应用（唯一新文件）
```

## `app.py` 详细规格

### 页面配置

```python
st.set_page_config(
    page_title="半导体工艺知识助手",
    page_icon="🔬",
    layout="wide",
)
```

### 页面布局：左侧边栏 + 右侧主区域

```
┌──────────────────────────────────────────────────┐
│  🔬 半导体工艺知识助手                              │
├────────────┬─────────────────────────────────────┤
│  侧边栏     │  主区域                               │
│            │                                     │
│ [上传文档]  │  聊天历史                              │
│            │  ┌─────────────────────────────────┐ │
│ 文档类型过滤 │  │ 用户: alarm E-1234 怎么处理？    │ │
│ ☑ SOP      │  │                                 │ │
│ ☑ 异常报告  │  │ 助手: 根据资料，E-1234 是...     │ │
│ ☑ FA       │  │ 【Alarm - alarm_codes.xlsx】     │ │
│ ☑ Alarm    │  │                                 │ │
│ ☑ Spec     │  └─────────────────────────────────┘ │
│            │                                     │
│ 已入库文档   │  [请输入您的问题...]                   │
│ - SOP (3)  │                                     │
│ - FA (5)   │                                     │
│ - ...      │                                     │
└────────────┴─────────────────────────────────────┘
```

### 侧边栏功能

#### 1. 文档上传区

```python
st.sidebar.header("📄 上传文档")
uploaded_files = st.sidebar.file_uploader(
    "支持 PDF / Word / Excel",
    type=["pdf", "docx", "doc", "xlsx", "xls"],
    accept_multiple_files=True,
)
```

上传流程：
1. 用户选择文件后，显示上传按钮
2. 点击上传按钮后：
   a. 将文件保存到 data/uploads/ 目录
   b. 调用 ingest_file() 处理每个文件
   c. 显示处理结果：成功入库 / 已存在（跳过）/ 解析失败
3. 用 st.spinner("正在处理 {filename}...") 显示进度
4. 处理完成后显示汇总：
   - ✅ XX机台SOP.pdf — 入库成功（12 个文本块）
   - ⏭️ alarm_codes.xlsx — 已存在，跳过
   - ❌ 扫描件.pdf — 解析失败：文档内容为空

#### 2. 文档类型过滤

```python
st.sidebar.header("🔍 检索过滤")
doc_type_filter = st.sidebar.selectbox(
    "文档类型",
    options=["全部", "SOP", "异常报告", "FA", "Alarm", "Spec", "其他"],
    index=0,
)
# "全部" 时传 None 给 search 函数
```

#### 3. 已入库文档列表

```python
st.sidebar.header("📚 已入库文档")
# 从 registry 读取，按 doc_type 分组显示
# 格式：
# SOP (3 份)
#   - XX机台SOP_v2.pdf
#   - YY工序作业指导.docx
#   - ...
# FA (2 份)
#   - 晶圆破裂分析.pdf
#   - ...
```

如果没有任何文档入库，显示提示："暂无文档，请先上传。"

### 主区域功能

#### 聊天界面

参考 invest_rag 的 app.py 实现，改动点：

1. **session_state 管理**
   - `st.session_state.messages`: 聊天历史 list[dict]
   - 每条消息: {"role": "user" | "assistant", "content": str}

2. **聊天输入**
   ```python
   question = st.chat_input("请输入您的问题，例如：XX机台的清洁SOP是什么？")
   ```

3. **回答流程**
   ```python
   # 1. 检索
   contexts = search(collection, question, top_k=config["top_k"], doc_type_filter=filter_value)
   
   # 2. 构建 messages
   messages = build_messages(question, contexts)
   
   # 3. 流式输出
   placeholder = st.empty()
   collected = ""
   for delta in stream_chat(messages):
       collected += delta
       placeholder.markdown(collected)
   ```

4. **空知识库提示**
   - 如果 collection 为空（没有入库任何文档），在主区域显示：
     "📭 知识库为空，请先在左侧上传文档。"
   - 禁用 chat_input

5. **检索无结果提示**
   - 如果 search 返回空列表，直接回复"未找到相关资料，请尝试换个关键词或检查是否已上传相关文档。"
   - 不调用 LLM

### 初始化逻辑

```python
@st.cache_resource
def init_app():
    """应用启动时执行一次"""
    config = get_config()  # 检查 DASHSCOPE_API_KEY
    collection = get_collection()
    return config, collection

# 在 main() 中：
try:
    config, collection = init_app()
except RuntimeError as e:
    st.error(f"配置错误：{e}")
    st.stop()

registry = load_registry()  # 每次刷新都重新读取（不缓存，因为上传会更新）
```

### 错误处理

| 场景 | 处理方式 |
|------|---------|
| 缺少 DASHSCOPE_API_KEY | st.error + st.stop |
| 文档解析失败 | 侧边栏显示 ❌ 错误信息，不影响其他文件 |
| 通义千问 API 调用失败 | st.error("AI 服务暂时不可用，请稍后再试") |
| 上传非支持格式 | file_uploader 的 type 参数已限制 |

### 样式

- 使用 st.sidebar 做侧边栏
- 主区域用 st.chat_message + st.chat_input 做聊天界面
- 上传成功用 st.success，失败用 st.error，跳过用 st.info
- 不需要自定义 CSS

## 完整 app.py 结构

```python
from __future__ import annotations

import shutil
from pathlib import Path

import streamlit as st

from config import get_config
from ingest import ingest_file
from ingest.registry import load_registry, get_registered_files
from retrieval.search import search, get_collection
import rag_core


def main() -> None:
    # 1. 页面配置
    # 2. 标题
    # 3. 初始化 (config, collection) — @st.cache_resource
    # 4. 加载 registry（不缓存）
    # 5. 侧边栏：上传 + 过滤 + 已入库文档列表
    # 6. 主区域：聊天界面
    pass


def handle_upload(uploaded_files, collection, registry) -> None:
    """处理上传的文件列表"""
    # 保存到 data/uploads/
    # 逐个调用 ingest_file
    # 显示处理结果
    pass


def render_sidebar_docs(registry: dict) -> None:
    """侧边栏显示已入库文档列表"""
    pass


def render_chat(collection, config: dict, doc_type_filter: str | None) -> None:
    """主区域聊天界面"""
    # session_state 管理
    # 显示历史消息
    # 处理新问题：检索 → 构建 prompt → 流式回答
    pass


if __name__ == "__main__":
    main()
```

## 重要约束

- 只创建 app.py 这一个文件
- 不要修改 Plan 1 中已创建的任何文件
- 不要创建 README.md
- 所有后端函数直接 import 使用，不要重新实现
- 通义千问的流式调用已在 rag_core.stream_chat() 中实现，app.py 只负责 UI 展示
- 上传文件保存路径：config 中的 UPLOAD_DIR（默认 data/uploads/）
- 文件保存时如果同名文件已存在，覆盖即可
- Python 3.10+，使用 `from __future__ import annotations`

## 验收标准

- [ ] `streamlit run app.py` 能正常启动
- [ ] 侧边栏能上传 PDF/Word/Excel 文件
- [ ] 上传后显示处理结果（成功/跳过/失败）
- [ ] 重复上传同一文件显示"已存在，跳过"
- [ ] 已入库文档列表按类型分组显示
- [ ] 文档类型过滤下拉框可选
- [ ] 聊天输入框可输入中文问题
- [ ] 回答流式输出，包含来源引用
- [ ] 空知识库时显示提示
- [ ] 缺少 API Key 时显示错误
