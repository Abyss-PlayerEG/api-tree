# API Tree CLI

> ⬆️ [English](../README.md)

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

- **HTML 图像导出** — 使用 `--html` 参数将树状图导出为带样式的 HTML 文件，内置 Catppuccin 浅色/暗色主题切换。输出至系统下载目录。

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
python main.py --html                   # 同时导出 HTML 至 ~/Downloads/
python main.py -h                       # 查看帮助
```

> 如果 URL 不含路径（如 `http://localhost:9090`），工具会自动追加 `/v3/api-docs`。若接口文档在其他路径，请直接指定完整 URL（如 `http://localhost:9090/swagger.json`）。

## 构建可执行文件

使用 PyInstaller 构建独立 `.exe`：

```bash
pip install pyinstaller
build.bat
```

输出路径：`dist/api-tree.exe`

## 效果展示

![Screenshot](/img/1.png)

![Screenshot](/img/2.png)

![Screenshot](/img/3.png)

![Screenshot](/img/4.png)
