# Plan 3: UI 重新设计 — 从 Streamlit 默认样式到专业界面

## 概述

当前 `app.py` 使用 Streamlit 的默认 `st.tabs` 布局。本次重新设计要求将界面升级为 **左侧固定导航栏 + 右侧内容区** 的专业布局，颜色更浅、更清爽，适合半导体公司内部使用。

**不更换框架**，仍然使用 Streamlit，通过 `st.markdown` 注入自定义 CSS 实现视觉升级。

## 设计规范

### 色彩系统

| Token | 值 | 用途 |
|-------|---|------|
| `--primary` | `#2563EB` | 主色调（按钮、高亮导航项） |
| `--primary-foreground` | `#FFFFFF` | 主色上的文字 |
| `--background` | `#FFFFFF` | 页面背景 |
| `--foreground` | `#0F172A` | 主要文字 |
| `--muted-foreground` | `#64748B` | 次要文字、占位符 |
| `--card` | `#FFFFFF` | 卡片背景 |
| `--border` | `#E2E8F0` | 边框、分割线 |
| `--sidebar` | `#F8FAFC` | 侧边栏背景 |
| `--sidebar-border` | `#E2E8F0` | 侧边栏右边框 |
| `--sidebar-accent` | `#EFF6FF` | 侧边栏高亮项背景 |
| `--sidebar-foreground` | `#334155` | 侧边栏文字 |
| `--user-bubble` | `#EFF6FF` | 用户聊天气泡背景 |
| `--user-bubble-text` | `#1E40AF` | 用户聊天气泡文字 |
| `--assistant-bubble` | `#FFFFFF` | 助手聊天气泡背景 |
| `--assistant-bubble-border` | `#E2E8F0` | 助手聊天气泡边框 |
| `--success` | `#16A34A` | 成功状态 |
| `--warning` | `#F59E0B` | 警告状态 |
| `--error` | `#DC2626` | 错误状态 |

### 字体

- 标题：`Inter, "Noto Sans SC", sans-serif`，font-weight: 600
- 正文：`Inter, "Noto Sans SC", sans-serif`，font-weight: 400
- 正文字号：14px，行高 1.5
- 标题字号：20px

### 圆角

- 按钮：`9999px`（全圆角药丸形）
- 卡片/输入框：`8px`
- 聊天气泡：`12px`

## 页面布局

### 整体结构

```
┌─────────────────────────────────────────────────────────────┐
│                     1440 x 900 viewport                     │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ Sidebar  │              Content Area                        │
│  280px   │           fill remaining                         │
│          │                                                  │
│ 固定导航  │          根据当前页面切换内容                       │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

### 左侧导航栏（固定，所有页面共用）

- 宽度：280px
- 背景色：`--sidebar` (#F8FAFC)
- 右边框：1px solid `--sidebar-border`
- 内边距：顶部 24px
- 垂直布局，间距 24px

内容：
1. **应用标题区**（Section Title）
   - 显示应用 logo/icon + "知识助手" 标题
   - 内边距：16px
   - 字号：16px，font-weight: 600

2. **导航项目**（可点击切换页面）
   - `文档上传` — 对应上传页面
   - `知识检索` — 对应聊天页面
   - `系统设置` — 预留（灰色不可点击或不实现）

3. **导航项样式**
   - 宽度：248px（侧边栏内居中）
   - 高度：48px
   - 内边距：12px 16px
   - 间距：16px（图标到文字）
   - **Active 状态**：背景 `--sidebar-accent` (#EFF6FF)，文字 `--primary`，圆角 100px
   - **Default 状态**：无背景，文字 `--sidebar-foreground` (#334155)

---

## 页面一：文档上传

当导航栏选中"文档上传"时显示此内容区。

### 布局

```
┌──────────────────────────────────────────────────────────────┐
│  Content Area (padding: 32px, vertical layout, gap: 24px)    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 页面标题                                                │  │
│  │ "📄 文档上传"  (20px, bold, --foreground)                │  │
│  │ "上传文档到知识库，支持..."  (14px, --muted-foreground)   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 上传区域                                                │  │
│  │ ┌──────────────────────────────────────────────────┐   │  │
│  │ │  虚线边框的拖拽上传区                               │   │  │
│  │ │  📄 拖拽文件到此处，或点击选择文件                    │   │  │
│  │ │  支持 PDF / Word / Excel                          │   │  │
│  │ └──────────────────────────────────────────────────┘   │  │
│  │  [上传并入库] 按钮（--primary 蓝色, 白色文字, 药丸形）   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 已入库文档                                              │  │
│  │ "📚 已入库文档"  (16px, bold)                            │  │
│  │ ┌────────────────────────────────────────────────────┐ │  │
│  │ │ Table                                              │ │  │
│  │ │ ┌─────────┬──────────────────┬──────────┐         │ │  │
│  │ │ │ 文件名   │ 文档类型          │  状态     │         │ │  │
│  │ │ ├─────────┼──────────────────┼──────────┤         │ │  │
│  │ │ │ XX机台.. │ SOP              │ ✅ 已入库 │         │ │  │
│  │ │ │ 异常报.. │ 异常报告          │ ✅ 已入库 │         │ │  │
│  │ │ │ E3021.. │ Alarm            │ ✅ 已入库 │         │ │  │
│  │ │ └─────────┴──────────────────┴──────────┘         │ │  │
│  │ └────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 表格规格

- 带 1px `--border` 边框
- 表头：font-weight 600，背景微灰
- 行高：44px
- 列宽：
  - 文件名：自适应填充
  - 文档类型：160px
  - 状态：120px
- 状态列使用标签样式：
  - "已入库" — 绿色标签 (成功色背景 + 白/深色文字)
  - "处理中" — 橙色标签

### 交互逻辑（不变）

- `st.file_uploader` 选择文件
- 点击"上传并入库"后逐个处理
- 处理结果用 `st.success` / `st.info` / `st.error` 显示
- 已入库文档列表从 `registry.json` 读取

---

## 页面二：知识检索（聊天）

当导航栏选中"知识检索"时显示此内容区。

### 布局

```
┌──────────────────────────────────────────────────────────────┐
│  Content Area (vertical layout, no padding, full height)     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Top Bar (height: 64px, padding: 16px 32px)             │  │
│  │ 左: "🔍 知识检索" (20px, bold)                          │  │
│  │ 右: [文档类型 ▾] 下拉筛选器                              │  │
│  │     宽 160px, 高 36px, 圆角 6px, 带边框                  │  │
│  │     选项: 全部 / SOP / 异常报告 / FA / Alarm / Spec / 其他│  │
│  │ 底部: 1px solid --border                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Messages Area (flex: 1, padding: 24px 32px, gap: 16px) │  │
│  │ 背景: --background, 垂直滚动                            │  │
│  │                                                        │  │
│  │    ┌─────────────────────────────────┐  ← 用户消息右对齐 │  │
│  │    │ CMP机台的清洁SOP是什么？          │                  │  │
│  │    └─────────────────────────────────┘                  │  │
│  │  用户气泡: 背景 #EFF6FF, 文字 #1E40AF, 圆角 12px        │  │
│  │  左侧留空 120px, 内容靠右                                │  │
│  │                                                        │  │
│  │  ┌─────────────────────────────────────┐  ← 助手靠左    │  │
│  │  │ 根据SOP文档，CMP机台清洁流程如下：     │                │  │
│  │  │                                     │                │  │
│  │  │ 1. 关闭设备电源并确认安全锁定          │                │  │
│  │  │ 2. 使用去离子水冲洗研磨垫表面          │                │  │
│  │  │ 3. 用专用清洁布擦拭Platen区域         │                │  │
│  │  │ 4. 检查Slurry供应管路是否堵塞         │                │  │
│  │  │ 5. 清洁完成后记录维护日志              │                │  │
│  │  └─────────────────────────────────────┘                │  │
│  │  助手气泡: 背景 #FFFFFF, 边框 1px --border, 圆角 12px    │  │
│  │  右侧留空 120px, 内容靠左                                │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Input Bar (padding: 16px 32px, gap: 12px)              │  │
│  │ 顶部: 1px solid --border                               │  │
│  │ 背景: --background                                     │  │
│  │                                                        │  │
│  │ [  请输入您的问题，例如：XX机台的清洁SOP是什么？  ] [发送]  │  │
│  │                                                        │  │
│  │ 输入框: fill width, 高 44px, 圆角 8px, 带边框             │  │
│  │ 发送按钮: --primary 背景, 白色文字, 药丸形, "发送"         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 聊天气泡样式

**用户消息：**
- 容器：`justify-content: flex-end`，左侧 padding 120px
- 气泡：背景 `#EFF6FF`，文字 `#1E40AF`，圆角 12px，padding 12px 16px
- 字号：14px

**助手消息：**
- 容器：`justify-content: flex-start`，右侧 padding 120px
- 气泡：背景 `#FFFFFF`，边框 1px solid `#E2E8F0`，圆角 12px，padding 12px 16px
- 标题行：14px，font-weight 600，`--foreground`
- 内容行：14px，`--foreground`，行高 1.6
- 字号：14px

### 聊天交互逻辑（与现有代码一致）

```python
# 1. 用户输入问题 → 添加到 session_state.messages
# 2. 调用 search() 检索相关文档块
#    - 如果选了文档类型过滤，传入 doc_type_filter
# 3. 如果检索结果为空 → 显示"未找到相关资料"
# 4. 调用 build_messages() 构建 prompt
# 5. 调用 stream_chat() 流式输出回答
# 6. 助手回答添加到 session_state.messages
```

### 空状态

当知识库无文档时：
- 消息区域显示提示卡片："📭 知识库为空，请先到"文档上传"页面上传文档。"
- 输入框禁用（`disabled=True`）

---

## 实现指南

### 方案：Streamlit + 自定义 CSS

由于仍然使用 Streamlit，通过以下技术实现新设计：

#### 1. 使用 `st.sidebar` 做导航栏

```python
# 在 sidebar 中用 radio 模拟导航
with st.sidebar:
    # 应用标题
    st.markdown("### 🔬 知识助手")
    
    # 导航选择
    page = st.radio(
        "导航",
        ["文档上传", "知识检索", "系统设置"],
        label_visibility="collapsed",
    )
```

#### 2. 注入自定义 CSS

在 `app.py` 开头通过 `st.markdown` 注入 CSS，覆盖 Streamlit 默认样式：

```python
st.markdown("""
<style>
/* 侧边栏样式 */
[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    border-right: 1px solid #E2E8F0;
    width: 280px !important;
}

/* 侧边栏 radio 按钮样式 → 导航项 */
[data-testid="stSidebar"] .stRadio > div {
    gap: 4px;
}
[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent;
    border-radius: 100px;
    padding: 12px 16px;
    color: #334155;
    font-size: 14px;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 600;
}

/* 主按钮样式 */
.stButton > button[kind="primary"] {
    background-color: #2563EB;
    color: white;
    border-radius: 9999px;
    border: none;
    padding: 10px 16px;
    font-size: 14px;
}

/* 聊天气泡 - 用户 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #EFF6FF;
    border-radius: 12px;
    border: none;
    color: #1E40AF;
}

/* 聊天气泡 - 助手 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

/* 页面背景 */
.main .block-container {
    padding: 32px;
    background-color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)
```

> **注意：** 以上 CSS 选择器为示例参考，Streamlit 版本更新可能改变内部 class 名。实现时需要用浏览器 DevTools 检查当前版本的实际选择器并调整。

#### 3. 页面切换

```python
# 不再使用 st.tabs，改用 sidebar radio 控制
if page == "文档上传":
    render_upload_page(collection, config, registry)
elif page == "知识检索":
    render_search_page(collection, config, registry)
else:
    st.info("系统设置功能即将推出")
```

#### 4. 已入库文档表格

用 `st.dataframe` 或手动构建 HTML 表格替代当前的 `st.write` 列表：

```python
import pandas as pd

files = get_registered_files(registry)
if files:
    df = pd.DataFrame(files)
    df = df[["filename", "doc_type"]].rename(
        columns={"filename": "文件名", "doc_type": "文档类型"}
    )
    df["状态"] = "✅ 已入库"
    st.dataframe(df, use_container_width=True, hide_index=True)
```

---

## 修改清单

只需要修改 **`app.py`** 这一个文件：

| 改动 | 说明 |
|------|------|
| 删除 `st.tabs` | 不再使用 tab 布局 |
| 添加 CSS 注入 | `st.markdown(css, unsafe_allow_html=True)` |
| 改为 `st.sidebar` + `st.radio` 导航 | 用 radio 模拟左侧导航 |
| `render_upload_page()` 调整 | 加页面标题/描述，表格用 `st.dataframe` |
| `render_search_page()` 调整 | 顶部加过滤栏，聊天区域样式优化 |
| `render_registered_docs()` 调整 | 改为表格形式，不再用 expander 分组 |
| `main()` 重构 | 改为 sidebar 导航 + 条件渲染 |

## 不要修改的文件

- `config.py` — 配置不变
- `ingest/` — 所有解析和入库逻辑不变
- `retrieval/` — 检索逻辑不变
- `rag_core.py` — LLM 调用不变
- `requirements.txt` — 无需新增依赖（pandas 已被 streamlit 依赖引入）

## 验收标准

- [ ] `streamlit run app.py` 正常启动
- [ ] 左侧显示固定导航栏（浅灰背景 #F8FAFC）
- [ ] 导航栏有 3 个菜单项：文档上传、知识检索、系统设置
- [ ] 当前页面对应的导航项高亮（浅蓝背景 #EFF6FF + 蓝色文字）
- [ ] 点击导航项可切换页面内容
- [ ] 文档上传页面：标题 + 上传区 + 蓝色"上传并入库"按钮 + 已入库文档表格
- [ ] 知识检索页面：顶部过滤栏 + 聊天消息区 + 底部输入栏
- [ ] 用户聊天气泡为浅蓝色 (#EFF6FF)
- [ ] 助手聊天气泡为白色带灰色边框
- [ ] 整体配色浅色清爽，没有深色/暗色区域
- [ ] 所有原有功能正常：上传、去重、检索、流式回答
- [ ] 空知识库时显示提示
