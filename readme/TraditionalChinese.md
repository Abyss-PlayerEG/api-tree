# API Tree CLI

> ⬆️ [English](../README.md) | [简体中文](SimplifiedChinese.md)

一個輕量級的命令列工具，用於從 OpenAPI (Swagger) 規範生成美觀的終端樹狀圖。支援從本機檔案、遠端伺服器讀取資料，並具備搜尋過濾功能。

## 特性

- **零依賴** — 僅使用 Python 3 標準庫，無需安裝任何第三方套件。
- **多源支援** — 支援讀取本機 JSON 檔案或遠端 OpenAPI 伺服器（預設連接埠 `:8080`）。
- **智慧搜尋** — 透過 `-s` 參數快速過濾包含特定關鍵字的路徑、方法或摘要。
- **色彩高亮** — 不同 HTTP 方法使用不同顏色區分：

  | 方法 | 顏色 |
  |------|------|
  | GET | 綠色 |
  | POST | 藍色 |
  | PUT | 黃色 |
  | DELETE | 紅色 |
  | PATCH | 紫色 |

- **HTML 圖像匯出** — 使用 `--html` 參數將樹狀圖匯出為帶樣式的 HTML 檔案，內建 Catppuccin 淺色/深色主題切換。輸出目錄可設定。

- **Agent 最佳化輸出** — 使用 `--agent-output` 參數生成 LLM 友好格式（markdown/json/curl），專為 AI 代理和自動化工作流程最佳化。

- **RAG 知識庫輸出** — 使用 `--rag-output` 參數生成結構化切片（jsonl/json），適用於向量資料庫和 RAG 檢索系統。

- **智慧路徑合併** — 自動合併單子節點路徑段，輸出更簡潔。
- **Springdoc 相容** — 自動在 URL 後附加 `/v3/api-docs` 路徑。

## 快速開始

### 前置要求

- Python 3.6+

### 執行

預設連接 `http://localhost:8080`：
```bash
python main.py
```

### 用法

```bash
python main.py                          # 預設連接 localhost:8080
python main.py http://localhost:9090    # 指定伺服器位址
python main.py /path/to/openapi.json    # 讀取本機 JSON 檔案
python main.py -s auth                  # 搜尋含 "auth" 的介面
python main.py --html                   # 同時匯出 HTML
python main.py --agent-output markdown  # LLM 最佳化輸出（markdown/json/curl）
python main.py --rag-output jsonl       # RAG 知識庫輸出（jsonl/json）
python main.py --rag-chunk-size 20      # RAG 切片大小（預設：10）
python main.py --init-config            # 產生預設設定檔
python main.py --show-config            # 顯示目前設定
python main.py -h                       # 檢視說明
```

> 如果 URL 不含路徑（如 `http://localhost:9090`），工具會自動附加 `/v3/api-docs`。若介面檔案在其他路徑，請直接指定完整 URL（如 `http://localhost:9090/swagger.json`）。

## 設定

產生預設設定檔：
```bash
python main.py --init-config
```

顯示目前設定：
```bash
python main.py --show-config
```

這會在 `~/.config/api-tree/config.json` 建立預設設定：
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

編輯此檔案可自訂：
- `output_dir`: HTML 匯出和其他檔案輸出的目錄
- `default_url`: 未指定 URL 時使用的預設 OpenAPI 伺服器位址

## 建構可執行檔案

使用 PyInstaller 建構獨立 `.exe`：

```bash
pip install pyinstaller
build.bat
```

輸出路徑：`dist/api-tree.exe`

## 效果展示

![Screenshot](/readme/img/1.png)

![Screenshot](/readme/img/2.png)

![Screenshot](/readme/img/3.png)

![Screenshot](/readme/img/4.png)
