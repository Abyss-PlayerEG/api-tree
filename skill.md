---
name: api-tree
description: 使用 api-tree CLI 工具查看和搜索 OpenAPI/Swagger 接口的终端树状图。当用户需要查看 API 接口结构、路由树、搜索特定 API 路径/端点，或提到 "api-tree"、"接口树"、"API 树"、"路由列表"、"swagger 接口"、"openapi 接口"、"查看接口"、"API 端点"、"接口结构"、"show api routes" 时使用。
---

# api-tree

在终端中以彩色树状图展示 OpenAPI 接口结构，支持搜索和过滤。

## 命令

| 命令 | 说明 |
|------|------|
| `api-tree` | 默认连接 `http://localhost:8080`，自动追加 `/v3/api-docs` |
| `api-tree <url>` | 连接指定 OpenAPI 文档地址 |
| `api-tree <file.json>` | 读取本地 OpenAPI JSON 文件 |
| `api-tree <url> -s <keyword>` | 搜索含关键词的路径/方法/摘要 |
| `api-tree -h` | 查看帮助 |

## 参数

- **位置参数**: OpenAPI 文档的 URL 或本地 JSON 文件路径。若 URL 不含具体路径（以 `/` 结尾或无路径），自动追加 `/v3/api-docs`。
- **`-s <keyword>`**: 搜索过滤（不区分大小写），匹配路径、摘要或 HTTP 方法。
- **`-h` / `--help`**: 打印帮助信息。

## 输出颜色

| 方法 | 颜色 |
|------|------|
| GET | 绿色 |
| POST | 蓝色 |
| PUT | 黄色 |
| DELETE | 红色 |
| PATCH | 品红色 |

## 示例

输入: "帮我看看 192.168.1.100:3000 的接口"
动作: `api-tree http://192.168.1.100:3000`

输入: "搜索 auth 相关的接口"
动作: `api-tree -s auth` 或 `api-tree <url> -s auth`

输入: "查看本地 openapi.json"
动作: `api-tree /path/to/openapi.json`
