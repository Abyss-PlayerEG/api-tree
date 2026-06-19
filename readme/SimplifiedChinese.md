# API Tree CLI

> ⬆️ [English](../README.md) | [繁體中文](TraditionalChinese.md)

一个轻量级 CLI 工具，将 OpenAPI (Swagger) 规范渲染为美观的终端树状图。支持本地文件和远程服务器，具备关键词搜索、LLM 优化输出和 RAG 知识库导出功能。

## 特性

- **零依赖** — 纯 Python 3 标准库，无需安装第三方包。
- **多源支持** — 读取本地 JSON 文件或远程 OpenAPI 服务器。
- **智能搜索** — `-s` 参数按路径、方法或摘要过滤接口。
- **色彩高亮** — 不同 HTTP 方法使用不同颜色：

  | 方法 | 颜色 |
  |------|------|
  | GET | 绿色 |
  | POST | 蓝色 |
  | PUT | 黄色 |
  | DELETE | 红色 |
  | PATCH | 紫色 |

- **HTML 导出** — `--html` 导出带 Catppuccin 浅色/暗色主题切换的 HTML 文件。
- **Agent 输出** — `--agent-output` 生成 LLM 友好格式，适用于 AI 辅助开发。
- **RAG 导出** — `--rag-output` 生成结构化切片，适用于向量数据库和检索系统。
- **智能路径合并** — 自动折叠单子节点路径段，输出更简洁。
- **Springdoc 兼容** — 自动在裸 URL 后追加 `/v3/api-docs`。

## 安装

### pipx（推荐）

```bash
pipx install api-tree
```

### uv

```bash
uv tool install api-tree
```

### 独立可执行文件

从 [GitHub Releases](https://github.com/Abyss-PlayerEG/api-tree/releases) 下载，无需 Python 环境。

## 快速开始

```bash
# 连接本地服务器（默认 localhost:8080）
api-tree

# 指定服务器
api-tree http://localhost:9090

# 读取本地文件
api-tree ./openapi.json
```

## 用法

### 基础

```bash
api-tree                              # 默认连接 localhost:8080
api-tree http://localhost:9090        # 指定服务器
api-tree /path/to/openapi.json        # 本地文件
api-tree -s auth                      # 搜索含 "auth" 的接口
api-tree --html                       # 导出 HTML
```

> 如果 URL 不含路径（如 `http://localhost:9090`），工具会自动追加 `/v3/api-docs`。若接口文档在其他路径，请直接指定完整 URL。

### Agent 输出（AI 辅助开发）

生成 LLM 优化的 API 结构表示，适用于向 AI 编程助手提供 API 上下文。

```bash
api-tree --agent-output markdown      # Markdown 表格
api-tree --agent-output json          # 结构化 JSON
api-tree --agent-output curl          # 可直接使用的 curl 命令
```

**使用场景：**
- 将 API 结构喂给 ChatGPT/Claude 生成代码
- 批量生成 curl 命令用于接口测试
- 为 AI 结对编程创建 API 参考文档

### RAG 知识库导出

为向量数据库和 RAG 检索系统生成结构化切片。

```bash
api-tree --rag-output jsonl           # 每行一个 JSON 对象（向量库导入用）
api-tree --rag-output json            # 完整 JSON 结构
api-tree --rag-chunk-size 20          # 每个切片的接口数（默认：10）
```

**使用场景：**
- 构建可搜索的 API 知识库
- 为 RAG 系统注入接口上下文
- 向嵌入模型管道喂结构化数据

### 配置

```bash
api-tree --init-config                # 生成 ~/.config/api-tree/config.json
api-tree --show-config                # 查看当前配置
```

配置文件：
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

## 从源码构建

```bash
git clone https://github.com/Abyss-PlayerEG/api-tree.git
cd api-tree
uv sync

# 直接运行
uv run api-tree

# 构建可执行文件
bash script/mac-build.sh        # macOS / Linux
script\win-build.bat            # Windows
```

## 效果展示

![终端树状图](/readme/img/1.png)

![搜索过滤](/readme/img/2.png)

![HTML 导出](/readme/img/3.png)

![色彩高亮](/readme/img/4.png)
