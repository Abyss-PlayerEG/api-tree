**API Tree CLI**

一个轻量级的命令行工具，用于从 OpenAPI (Swagger) 规范生成美观的终端树状图。支持从本地文件、远程服务器读取数据，并具备搜索过滤功能。

**✨ 特性**
* **零依赖**：仅使用 Python 3 标准库，无需安装任何第三方包。
* **多源支持**：支持读取本地 JSON 文件或远程 OpenAPI 服务器（默认端口 :8080）。
* **智能搜索**：通过 `-s` 参数快速过滤包含特定关键词的接口。
* **色彩高亮**：不同 HTTP 方法（GET, POST, PUT, DELETE 等）使用不同颜色区分。
* **结构清晰**：自动合并单路径节点，显示接口摘要信息。

**🚀 快速开始**

**1. 准备工作**
确保你的系统已安装 Python 3。

**2. 运行脚本**
直接运行脚本，默认连接 `http://localhost:8080`：
`python api-tree.py`

**3. 常用命令**
* **连接指定地址**：`python api-tree.py http://localhost:9090`
* **读取本地文件**：`python api-tree.py /path/to/openapi.json`
* **搜索特定接口**：`python api-tree.py -s auth`
* **查看帮助**：`python api-tree.py -h`

**🛠️ 使用说明**
该工具会自动尝试在提供的 URL 后附加 `/v3/api-docs` 路径（常见于 Springdoc OpenAPI）。如果接口文档位于根路径或其他路径，建议直接指定完整 URL。

**输出示例**：
```
API 接口URL树状图 (15 个接口)
└── /users (2 个接口)
    ├── /users/list     GET      获取用户列表
    └── /users/create   POST     创建新用户
```

**效果展示**

![效果展示](/img/1.png)

![效果展示](/img/2.png)

**📝 开源许可**
本项目基于 MIT 许可证。
