# 半导体工艺知识助手 - 实施计划

## 目标

为工厂建立一个统一的工艺知识库问答系统。工程师可以通过网页界面，用自然语言查询 SOP、异常报告、FA Report、Alarm Code、客户 Spec 等资料，系统基于 RAG 检索相关内容并生成回答和来源引用。

核心目标：**资料太多找不到 → 一个入口问就行。**

## 用户与规模

- 工厂人数：< 100 人
- 主要用户：工程师、技术员
- 文档语言：中文为主，部分英文（客户 Spec）

## 技术路线

| 组件 | 选型 | 理由 |
|------|------|------|
| 前端/应用 | Streamlit | 快速开发，够用 |
| LLM | 通义千问（qwen-plus） | 国内直连、便宜、中文好 |
| Embedding | 通义 text-embedding-v3 | 配套通义，国内快 |
| 向量数据库 | ChromaDB 本地持久化 | 轻量，数据量不大够用 |
| 文档解析 | `unstructured` | 统一处理 PDF/Word/Excel |
| OCR | `unstructured` + `paddleocr` | 处理扫描件 PDF |
| 部署 | 阿里云 ECS（2C4G） | 全厂可访问 |

## 数据源

| 类型 | 说明 | 典型格式 |
|------|------|----------|
| SOP | 标准作业程序 | PDF / Word |
| 异常报告 | 生产异常记录与处理 | Word / Excel / PDF |
| FA Report | 失效分析报告 | PDF / Word |
| Alarm Code | 设备报警代码与处理方式 | Excel / PDF |
| 客户 Spec | 客户产品规格书 | PDF（可能英文） |

## 文件结构

```text
semiconductor_knowledge_rag/
├── PLAN.md
├── app.py                      # Streamlit 主界面
├── config.py                   # 配置管理（API key、路径等）
├── ingest/
│   ├── __init__.py
│   ├── parser.py               # 文档解析（PDF/Word/Excel → 文本）
│   ├── chunker.py              # 分块策略
│   └── registry.py             # 文件 hash 去重 + 增量入库
├── retrieval/
│   ├── __init__.py
│   └── search.py               # 向量检索 + metadata 过滤
├── rag_core.py                 # Prompt 构建 + LLM 调用
├── data/
│   └── uploads/                # 上传的原始文档存放
├── chroma_db/                  # 向量库（运行时生成）
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Metadata 设计

每个 chunk 携带以下 metadata，用于检索过滤和来源引用：

```python
{
    "id": "sop_XX机台SOP_v2_chunk_3",
    "doc_type": "SOP",           # SOP / 异常报告 / FA / Alarm / Spec
    "filename": "XX机台SOP_v2.pdf",
    "chunk_index": 3,
    "text": "...",
    # 以下为预留字段（MVP 可先不填）
    "machine": "",               # 机台编号
    "product": "",               # 产品型号
    "date": "",                  # 文档日期
}
```

## 引用格式

回答中引用来源格式：

```
【SOP - XX机台SOP_v2.pdf】
【FA - 20240315_晶圆破裂分析.pdf】
【Alarm - E-1234 主轴过热】
```

## 分块策略

1. 用 `unstructured` 解析文档，获取 elements（段落、表格、标题等）。
2. 按 element 类型合并：
   - 标题 + 后续段落归为一组
   - 表格单独成 chunk（保留表格结构）
3. 目标 chunk 大小：500-1000 中文字符。
4. 超长段落按句子边界拆分（`。`、`！`、`？`、`；`）。

## RAG 管道

```text
用户问题
  → 通义 embedding
  → ChromaDB 检索 top-5（可选 metadata filter）
  → 构建 system prompt + 上下文 + 用户问题
  → 通义千问流式生成
  → 中文回答 + 来源引用
```

### System Prompt

```
你是半导体工厂的工艺知识助手。请根据提供的参考资料回答问题。

要求：
1. 基于参考资料作答，不要编造信息。
2. 每个关键信息标注来源，格式为【文档类型 - 文件名】。
3. 如果资料不足以回答，请如实说明。
4. 回答要准确、简洁、有条理。
5. 如果问题涉及操作步骤，请按步骤列出。
6. 支持中英文问答。
```

## 实施阶段

### Phase 1: MVP（核心问答）

目标：能上传文档、能问能答。

- [ ] 项目初始化（依赖、配置、目录结构）
- [ ] `parser.py`：用 unstructured 解析 PDF / Word / Excel
- [ ] `chunker.py`：分块 + 生成 metadata
- [ ] `registry.py`：文件 hash 去重，避免重复入库
- [ ] `search.py`：ChromaDB 向量检索
- [ ] `rag_core.py`：通义千问 prompt 构建 + 流式调用
- [ ] `app.py`：Streamlit 界面（文档上传 + 问答聊天）
- [ ] 本地测试通过
- [ ] 部署到阿里云 ECS

### Phase 2: 体验优化

- [ ] 文档类型过滤（用户可选择只查 SOP / 只查 FA 等）
- [ ] 历史对话记录
- [ ] 上传进度显示 + 已入库文档列表
- [ ] 支持扫描件 OCR（PaddleOCR）

### Phase 3: 自动化

- [ ] 监听文件夹自动入库（watchdog 或定时扫描）
- [ ] 文档版本管理（同名文件新版本替换旧版本）
- [ ] 批量导入工具

### Phase 4: 权限与管理

- [ ] 登录认证（简单账号密码 或 对接公司 LDAP）
- [ ] 角色权限（管理员可上传，普通用户只能查）
- [ ] 文档访问控制（如：客户 Spec 限特定人员查看）
- [ ] 管理后台（查看使用统计、管理文档）

## 部署方案

### 阿里云 ECS

```
阿里云 ECS (2C4G, Ubuntu)
├── Streamlit app      → 端口 8501
├── ChromaDB           → 本地文件存储
├── Nginx（可选）       → 反向代理，加域名 / HTTPS
└── 数据备份           → 定期备份 chroma_db/ 和 data/uploads/
```

访问方式：`http://公网IP:8501` 或绑定域名

### 预估成本

| 项目 | 月费用（估算） |
|------|---------------|
| 阿里云 ECS 2C4G | ¥100-200 |
| 通义千问 API | ¥50-200（取决于使用量） |
| 域名（可选） | ¥50/年 |
| **合计** | **¥150-400/月** |

## 依赖清单

```
streamlit
dashscope                # 通义千问 SDK
chromadb
unstructured[all-docs]   # PDF/Word/Excel 解析
paddleocr                # 扫描件 OCR（Phase 2）
paddlepaddle
python-dotenv
```

## 关键风险

| 风险 | 严重度 | 应对 |
|------|--------|------|
| 扫描件 PDF 解析质量差 | 中 | Phase 1 先跳过扫描件，Phase 2 加 OCR |
| 表格内容检索效果差 | 中 | 表格单独成 chunk，保留结构化格式 |
| 通义千问回答质量不够 | 低 | 可随时切换到 qwen-max 或其他模型 |
| 文档量增大后检索变慢 | 低 | <100 人工厂文档量有限，ChromaDB 够用 |
| ECS 数据丢失 | 中 | 定期备份 chroma_db + uploads 到 OSS |

## 验收标准（Phase 1 MVP）

- [ ] 能上传 PDF / Word / Excel 文档
- [ ] 上传后自动解析、分块、入库
- [ ] 重复上传同一文件不会重复入库
- [ ] 中文问题得到中文回答
- [ ] 英文 Spec 相关问题也能回答
- [ ] 回答包含来源引用【文档类型 - 文件名】
- [ ] 资料不足时能说明"未找到相关资料"
- [ ] 阿里云部署后全厂可访问
