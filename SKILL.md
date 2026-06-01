---
name: api-tree
description: 使用 api-tree CLI 工具查看和搜索 OpenAPI/Swagger 接口的终端树状图。当用户需要查看 API 接口结构、路由树、搜索特定 API 路径/端点，或提到 "api-tree"、"接口树"、"API 树"、"路由列表"、"swagger 接口"、"openapi 接口"、"查看接口"、"API 端点"、"接口结构"、"show api routes" 时使用。
---

# api-tree

在终端中以彩色树状图展示 OpenAPI 接口结构，支持搜索和过滤。支持多种输出格式，包括为 LLM Agent 优化的输出和 RAG 知识库输出。

## 命令

| 命令 | 说明 |
|------|------|
| `api-tree` | 默认连接 `http://localhost:8080`，自动追加 `/v3/api-docs` |
| `api-tree <url>` | 连接指定 OpenAPI 文档地址 |
| `api-tree <file.json>` | 读取本地 OpenAPI JSON 文件 |
| `api-tree <url> -s <keyword>` | 搜索含关键词的路径/方法/摘要 |
| `api-tree <url> --html` | 同时导出带主题切换的 HTML 文件 |
| `api-tree <url> --agent-output <format>` | 为 LLM Agent 优化的输出（markdown/json/curl） |
| `api-tree <url> --rag-output <format>` | 为 RAG 知识库优化的输出（jsonl/json） |
| `api-tree <url> --rag-chunk-size <n>` | 设置 RAG 切片大小（默认 10 个端点） |
| `api-tree --init-config` | 生成默认配置文件 |
| `api-tree --show-config` | 显示当前配置 |
| `api-tree -h` | 查看帮助 |

## 参数

- **位置参数**: OpenAPI 文档的 URL 或本地 JSON 文件路径。若 URL 不含具体路径（以 `/` 结尾或无路径），自动追加 `/v3/api-docs`。
- **`-s <keyword>`**: 搜索过滤（不区分大小写），匹配路径、摘要或 HTTP 方法。
- **`--html`**: 额外生成 HTML 文件，内置 Catppuccin 浅色/暗色主题切换。输出目录可通过配置文件自定义。
- **`--init-config`**: 在 `~/.config/api-tree/` 目录下生成默认配置文件，用于自定义输出目录和默认URL等设置。
- **`--show-config`**: 显示当前配置文件内容和位置。
- **`--agent-output <format>`**: 为 LLM Agent 优化的输出格式：
  - `markdown`: 精简的 Markdown 格式，包含层次结构和端点详情
  - `json`: 结构化的 JSON 格式，便于程序化处理
  - `curl`: CURL 请求模板，包含示例请求头和请求体
- **`--rag-output <format>`**: 为 RAG 知识库优化的输出格式：
  - `jsonl`: JSON Lines 格式，每行一个切片，便于批量导入向量数据库
  - `json`: JSON 格式，包含完整的切片数组
- **`--rag-chunk-size <n>`**: 设置 RAG 切片大小，默认 10 个端点每片。
- **`-v` / `--version`**: 显示版本信息。
- **`-h` / `--help`**: 打印帮助信息。

## RAG 切片详细说明

### 切片内容结构

每个 RAG 切片包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `chunk_id` | 切片唯一标识 | `/api/v1/users_10` |
| `title` | 切片标题 | `My API - /api/v1/users endpoints` |
| `path_prefix` | 路径前缀 | `/api/v1/users` |
| `endpoint_count` | 端点数量 | `10` |
| `endpoints` | 端点详细信息数组 | 见下方 |
| `text` | **可直接向量化的文本** | 包含完整描述 |
| `metadata` | 元数据信息 | API标题、切片类型等 |

### 切片文本内容（用于向量化）

每个切片的 `text` 字段包含可直接用于向量化的文本内容：

```
My API - /api/v1/users endpoints
Path prefix: /api/v1/users
Number of endpoints: 10

GET /api/v1/users
  Description: List all registered users
POST /api/v1/users
  Description: Create a new user account
GET /api/v1/users/{userId}
  Description: Get user profile by ID
```

### 端点信息结构

每个端点包含以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| `method` | HTTP 方法 | `GET`、`POST`、`PUT`、`DELETE` |
| `path` | API 路径 | `/api/v1/users/{userId}` |
| `summary` | 端点描述 | `Get user profile by ID` |
| `path_prefix` | 路径前缀 | `/api/v1/users` |
| `context` | 上下文信息 | 包含父路径、当前段等 |

### 切片大小选择指南

| 切片大小 | 适用场景 | 优点 | 缺点 |
|----------|----------|------|------|
| **小（5-10）** | 精确检索特定功能 | 检索精度高 | 上下文信息可能不完整 |
| **中（10-20）** | 平衡检索和上下文 | 平衡精度和完整性 | - |
| **大（20-50）** | 需要完整上下文 | 上下文信息完整 | 检索精度可能降低 |

### 切片生成逻辑

1. **按路径前缀分组**：将 API 端点按路径前缀进行分组
2. **智能分割**：每个切片最多包含 `chunk_size` 个端点
3. **保持上下文**：同一路径前缀的端点尽量在同一个切片中
4. **自动合并**：如果添加某个分组会超过 `chunk_size`，会先完成当前切片

## 输出颜色

| 方法 | 颜色 |
|------|------|
| GET | 绿色 |
| POST | 蓝色 |
| PUT | 黄色 |
| DELETE | 红色 |
| PATCH | 品红色 |

## Agent 自主调用指南

### 重要说明

当 Agent 需要自主查看 API 接口时，应优先使用 `--agent-output` 参数，而不是普通终端输出。

**原因**：
- `--agent-output` 的输出格式专门为 AI 解析优化，更容易被 Agent 理解和处理
- 普通终端输出包含颜色、树状图等视觉元素，适合人类阅读但不适合 AI 解析
- Agent 自主调用时，默认使用 `--agent-output markdown` 获取 API 结构

### Agent 自主调用默认行为

当 Agent 需要自主查看 API 接口时，应遵循以下规则：
1. **默认使用** `--agent-output markdown` 获取 API 结构（易读，包含层次结构）
2. **如果需要程序化处理**，使用 `--agent-output json`（结构化，便于解析）
3. **如果需要生成请求代码**，使用 `--agent-output curl`（包含完整请求模板）
4. **只有当用户明确要求"终端显示"或"终端查看"时**，才使用基本用法

### 意图识别规则

根据用户输入识别意图，选择对应的参数：

| 用户意图关键词 | 参数选择 |
|---------------|----------|
| "查看接口"、"接口树"、"API 树"、"路由列表"（Agent 自主调用） | `--agent-output markdown` |
| "终端显示"、"终端查看"（用户明确要求） | 基本用法（无特殊参数） |
| "搜索"、"查找"、"过滤" | `-s <keyword>` |
| "导出 HTML"、"生成网页" | `--html` |
| "生成配置"、"初始化配置"、"配置文件" | `--init-config` |
| "查看配置"、"显示配置"、"当前配置" | `--show-config` |
| "给 Agent 用"、"LLM 使用"、"Markdown 格式" | `--agent-output markdown` |
| "JSON 数据"、"结构化数据" | `--agent-output json` |
| "CURL 模板"、"请求示例" | `--agent-output curl` |
| "RAG"、"知识库"、"向量数据库" | `--rag-output jsonl` |
| "切片"、"分块" | `--rag-chunk-size <n>` |

### 参数选择决策树

```
用户输入
├── Agent 自主调用（需要查看 API）
│   └── 默认 → --agent-output markdown
├── 包含"终端显示/终端查看"（用户明确要求） → 基本用法
├── 包含"搜索/查找/过滤" → 添加 -s <keyword>
├── 包含"HTML/网页/导出" → 添加 --html
├── 包含"生成配置/初始化配置/配置文件" → --init-config
├── 包含"查看配置/显示配置/当前配置" → --show-config
├── 包含"Agent/LLM/给AI用"
│   ├── 需要 Markdown → --agent-output markdown
│   ├── 需要 JSON → --agent-output json
│   └── 需要 CURL → --agent-output curl
├── 包含"RAG/知识库/向量"
│   ├── 默认 → --rag-output jsonl
│   └── 需要 JSON → --rag-output json
└── 无特殊需求 → 基本用法
```

### 输出格式选择建议

| 场景 | 推荐格式 | 原因 |
|------|----------|------|
| Agent 自主调用查看 API | markdown | 易读，包含层次结构，专门为 AI 优化 |
| 程序化处理 | json | 结构化，便于解析 |
| 生成请求代码 | curl | 包含完整请求模板 |
| 批量导入向量数据库 | jsonl | 每行一个切片，便于流式处理 |
| 单次处理 | json | 完整数组，便于一次性加载 |
| 用户明确要求终端显示 | 基本用法 | 包含颜色和树状图，适合人类阅读 |

### 参数组合示例

```bash
# Agent 自主调用查看 API（默认）
api-tree <url> --agent-output markdown

# Agent 搜索接口
api-tree <url> -s auth --agent-output markdown

# Agent 获取 JSON 数据
api-tree <url> --agent-output json

# 用户明确要求终端显示
api-tree <url>  # 无 --agent-output 参数

# 搜索 + RAG 输出
api-tree <url> -s user --rag-output jsonl

# RAG 输出 + 自定义切片大小
api-tree <url> --rag-output jsonl --rag-chunk-size 20
```

## 使用场景与决策

### 场景1：Agent 自主查看接口结构（推荐）
**用户输入**: "帮我看看 192.168.1.100:3000 的接口"
**决策**: Agent 自主调用，使用 `--agent-output markdown`
**命令**: `api-tree http://192.168.1.100:3000 --agent-output markdown`

### 场景2：用户明确要求终端显示
**用户输入**: "在终端显示 192.168.1.100:3000 的接口树"
**决策**: 用户明确要求终端显示，使用基本用法
**命令**: `api-tree http://192.168.1.100:3000`

### 场景3：搜索特定接口
**用户输入**: "搜索 auth 相关的接口"
**决策**: 使用 -s 参数过滤，Agent 自主调用时加 `--agent-output`
**命令**: `api-tree -s auth --agent-output markdown` 或 `api-tree <url> -s auth --agent-output markdown`

### 场景4：导出 HTML 文件
**用户输入**: "导出接口树状图为 HTML"
**决策**: 使用 --html 参数
**命令**: `api-tree <url> --html`

### 场景5：为 Agent 生成优化输出
**用户输入**: "生成 Markdown 格式的 API 文档给 Agent 使用"
**决策**: 使用 --agent-output markdown
**命令**: `api-tree <url> --agent-output markdown`

### 场景6：为 RAG 知识库生成切片
**用户输入**: "生成 RAG 切片数据用于向量数据库"
**决策**: 使用 --rag-output jsonl
**命令**: `api-tree <url> --rag-output jsonl`

### 场景7：组合功能
**用户输入**: "搜索 user 接口并生成 JSON 格式给 Agent"
**决策**: 组合 -s 和 --agent-output
**命令**: `api-tree <url> -s user --agent-output json`

### 场景8：配置文件管理
**用户输入**: "生成配置文件" 或 "初始化配置"
**决策**: 使用 --init-config 参数
**命令**: `api-tree --init-config`
**说明**: 在 `~/.config/api-tree/config.json` 创建默认配置文件，可用于自定义输出目录和默认URL。

**用户输入**: "查看配置" 或 "显示当前配置"
**决策**: 使用 --show-config 参数
**命令**: `api-tree --show-config`
**说明**: 显示当前配置文件的内容和位置。

## 快速参考

### 常用命令速查

| 场景 | 命令 |
|------|------|
| Agent 自主查看 API（推荐） | `api-tree <url> --agent-output markdown` |
| 用户明确要求终端显示 | `api-tree <url>` |
| 查看本地文件 | `api-tree /path/to/openapi.json --agent-output markdown` |
| 搜索接口 | `api-tree <url> -s <keyword> --agent-output markdown` |
| 导出 HTML | `api-tree <url> --html` |
| 生成配置文件 | `api-tree --init-config` |
| 查看配置 | `api-tree --show-config` |
| Agent 输出 | `api-tree <url> --agent-output <format>` |
| RAG 输出 | `api-tree <url> --rag-output <format>` |

### 参数速查

| 参数 | 说明 | 值 |
|------|------|-----|
| `-s` | 搜索关键词 | 字符串 |
| `--html` | 导出 HTML | 无值 |
| `--init-config` | 生成默认配置文件 | 无值 |
| `--show-config` | 显示当前配置 | 无值 |
| `--agent-output` | Agent 输出格式（Agent 自主调用时优先使用） | markdown/json/curl |
| `--rag-output` | RAG 输出格式 | jsonl/json |
| `--rag-chunk-size` | RAG 切片大小 | 正整数（默认10） |

## 示例

### 基本用法

输入: "帮我看看 192.168.1.100:3000 的接口"
动作: `api-tree http://192.168.1.100:3000`

输入: "搜索 auth 相关的接口"
动作: `api-tree -s auth` 或 `api-tree <url> -s auth`

输入: "导出接口树状图为 HTML"
动作: `api-tree <url> --html`

输入: "查看本地 openapi.json"
动作: `api-tree /path/to/openapi.json`

输入: "搜索本地文件中的 user 接口"
动作: `api-tree /path/to/openapi.json -s user`

输入: "导出 HTML 并搜索 auth 接口"
动作: `api-tree <url> -s auth --html`

### Agent 优化输出

输入: "生成 Markdown 格式的 API 文档给 Agent 使用"
动作: `api-tree <url> --agent-output markdown`

输入: "搜索 auth 接口并生成 Markdown"
动作: `api-tree <url> -s auth --agent-output markdown`

输入: "生成 JSON 格式的 API 结构数据"
动作: `api-tree <url> --agent-output json`

输入: "搜索 user 接口并生成 JSON"
动作: `api-tree <url> -s user --agent-output json`

输入: "生成 CURL 请求模板"
动作: `api-tree <url> --agent-output curl`

输入: "搜索 product 接口并生成 CURL 模板"
动作: `api-tree <url> -s product --agent-output curl`

输入: "搜索本地文件中的 auth 接口并生成 Markdown"
动作: `api-tree /path/to/openapi.json -s auth --agent-output markdown`

### RAG 知识库输出

输入: "生成 RAG 切片数据用于向量数据库"
动作: `api-tree <url> --rag-output jsonl`

输入: "搜索 auth 接口并生成 RAG 切片"
动作: `api-tree <url> -s auth --rag-output jsonl`

输入: "生成 JSON 格式的 RAG 切片"
动作: `api-tree <url> --rag-output json`

输入: "搜索 user 接口并生成 JSON 格式 RAG 切片"
动作: `api-tree <url> -s user --rag-output json`

输入: "生成 RAG 切片，每片 20 个端点"
动作: `api-tree <url> --rag-output jsonl --rag-chunk-size 20`

输入: "搜索 product 接口并生成 RAG 切片，每片 15 个端点"
动作: `api-tree <url> -s product --rag-output jsonl --rag-chunk-size 15`

输入: "生成搜索结果的 RAG 切片"
动作: `api-tree <url> -s user --rag-output jsonl`

输入: "搜索本地文件中的 auth 接口并生成 RAG 切片"
动作: `api-tree /path/to/openapi.json -s auth --rag-output jsonl`

### 配置文件管理

输入: "生成配置文件"
动作: `api-tree --init-config`

输入: "初始化配置"
动作: `api-tree --init-config`

输入: "查看配置"
动作: `api-tree --show-config`

输入: "显示当前配置"
动作: `api-tree --show-config`

**配置文件内容**：
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

**配置说明**：
- `output_dir`: HTML 导出和其他文件输出的目录
- `default_url`: 未指定 URL 时使用的默认 OpenAPI 服务器地址