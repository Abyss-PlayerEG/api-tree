
**API Tree CLI**
> 📖 [中文文档](readme/Chinese.md)

A lightweight command-line tool that renders beautiful terminal tree diagrams from OpenAPI (Swagger) specifications. It reads data from local files or remote servers and supports keyword-based search and filtering.

**✨ Features**
* **Zero Dependencies** — Uses only the Python 3 standard library. No third-party packages required.
* **Multi-Source** — Reads local JSON files or fetches from a remote OpenAPI server (default port :8080).
* **Smart Search** — Use the `-s` flag to quickly filter endpoints that contain a specific keyword.
* **Color-Coded Methods** — Different HTTP methods (GET, POST, PUT, DELETE, etc.) are highlighted in distinct colors.
* **Clean Structure** — Automatically merges single-segment path nodes and displays endpoint summaries.

**🚀 Quick Start**

**1. Prerequisites**
Make sure Python 3 is installed on your system.

**2. Run the Script**
Run the script directly to connect to `http://localhost:8080` by default:
`python api-tree.py`

**3. Common Commands**
* **Connect to a specific server** — `python api-tree.py http://localhost:9090`
* **Read a local file** — `python api-tree.py /path/to/openapi.json`
* **Search for specific endpoints** — `python api-tree.py -s auth`
* **Show help** — `python api-tree.py -h`

**🛠️ Usage Notes**
The tool automatically appends `/v3/api-docs` to the provided URL (common with Springdoc OpenAPI). If your API documentation is served at the root path or a different path, specify the full URL directly.

**Output Example**
```
API Endpoint Tree (15 endpoints)
└── /users (2 endpoints)
    ├── /users/list     GET      Get user list
    └── /users/create   POST     Create a new user
```

**Screenshots**

![Screenshot](/img/1.png)

![Screenshot](/img/2.png)