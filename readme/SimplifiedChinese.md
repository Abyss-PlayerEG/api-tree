# API Tree CLI

> ⬆️ [English](../README.md) | [繁體中文](TraditionalChinese.md)

一个轻量级的命令行工具，用于从 OpenAPI (Swagger) 规范生成美观的终端树状图。支持从本地文件、远程服务器读取数据，并具备搜索过滤功能。

## 特性

- **零依赖** — 仅使用 Python 3 标准库，无需安装任何第三方包。
- **多源支持** — 支持读取本地 JSON 文件或远程 OpenAPI 服务器（默认端口 `:8080`）。
- **智能搜索** — 通过 `-s` 参数快速过滤包含特定关键词的路径、方法或摘要。
- **色彩高亮** — 不同 HTTP 方法使用不同颜色区分：

  | 方法 | 颜色 |
  |------|------|
  | GET | 绿色 |
  | POST | 蓝色 |
  | PUT | 黄色 |
  | DELETE | 红色 |
  | PATCH | 紫色 |

- **HTML 图像导出** — 使用 `--html` 参数将树状图导出为带样式的 HTML 文件，内置 Catppuccin 浅色/暗色主题切换。输出目录可配置。

- **Agent 优化输出** — 使用 `--agent-output` 参数生成 LLM 友好格式（markdown/json/curl），专为 AI 代理和自动化工作流优化。

- **RAG 知识库输出** — 使用 `--rag-output` 参数生成结构化切片（jsonl/json），适用于向量数据库和 RAG 检索系统。

- **智能路径合并** — 自动合并单子节点路径段，输出更简洁。
- **Springdoc 兼容** — 自动在 URL 后追加 `/v3/api-docs` 路径。

## 快速开始

### 前置要求

- Python 3.6+

### 运行

默认连接 `http://localhost:8080`：
```bash
python main.py
```

### 用法

```bash
python main.py                          # 默认连接 localhost:8080
python main.py http://localhost:9090    # 指定服务器地址
python main.py /path/to/openapi.json   # 读取本地 JSON 文件
python main.py -s auth                  # 搜索含 "auth" 的接口
python main.py --html                   # 同时导出 HTML
python main.py --agent-output markdown  # LLM 优化输出（markdown/json/curl）
python main.py --rag-output jsonl       # RAG 知识库输出（jsonl/json）
python main.py --rag-chunk-size 20      # RAG 切片大小（默认：10）
python main.py --init-config            # 生成默认配置文件
python main.py --show-config            # 显示当前配置
python main.py -h                       # 查看帮助
```

> 如果 URL 不含路径（如 `http://localhost:9090`），工具会自动追加 `/v3/api-docs`。若接口文档在其他路径，请直接指定完整 URL（如 `http://localhost:9090/swagger.json`）。

## 配置

生成默认配置文件：
```bash
python main.py --init-config
```

显示当前配置：
```bash
python main.py --show-config
```

这会在 `~/.config/api-tree/config.json` 创建默认配置：
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

编辑此文件可自定义：
- `output_dir`: HTML 导出和其他文件输出的目录
- `default_url`: 未指定 URL 时使用的默认 OpenAPI 服务器地址

## 构建可执行文件

使用 PyInstaller 构建独立 `.exe`：

```bash
pip install pyinstaller
build.bat
```

输出路径：`dist/api-tree.exe`

## 效果展示

![Screenshot](/readme/img/1.png)

![Screenshot](/readme/img/2.png)

![Screenshot](/readme/img/3.png)

![Screenshot](/readme/img/4.png)
