# API Tree CLI

> ⬆️ [English](../README.md) | [简体中文](SimplifiedChinese.md)

一個輕量級 CLI 工具，將 OpenAPI (Swagger) 規範渲染為美觀的終端樹狀圖。支援本機檔案和遠端伺服器，具備關鍵字搜尋、LLM 最佳化輸出和 RAG 知識庫匯出功能。

## 特性

- **零依賴** — 純 Python 3 標準庫，無需安裝第三方套件。
- **多源支援** — 讀取本機 JSON 檔案或遠端 OpenAPI 伺服器。
- **智慧搜尋** — `-s` 參數按路徑、方法或摘要過濾介面。
- **色彩高亮** — 不同 HTTP 方法使用不同顏色：

  | 方法 | 顏色 |
  |------|------|
  | GET | 綠色 |
  | POST | 藍色 |
  | PUT | 黃色 |
  | DELETE | 紅色 |
  | PATCH | 紫色 |

- **HTML 匯出** — `--html` 匯出帶 Catppuccin 淺色/深色主題切換的 HTML 檔案。
- **Agent 輸出** — `--agent-output` 生成 LLM 友好格式，適用於 AI 輔助開發。
- **RAG 匯出** — `--rag-output` 生成結構化切片，適用於向量資料庫和檢索系統。
- **智慧路徑合併** — 自動摺疊單子節點路徑段，輸出更簡潔。
- **Springdoc 相容** — 自動在裸 URL 後附加 `/v3/api-docs`。

## 安裝

### 獨立可執行檔案

從 [GitHub Releases](https://github.com/Abyss-PlayerEG/api-tree/releases) 下載，無需 Python 環境。

### 從原始碼建構

```bash
git clone https://github.com/Abyss-PlayerEG/api-tree.git
cd api-tree
uv sync
uv run api-tree
```

### 未來計劃

- [ ] `pip install api-tree`
- [ ] `pipx install api-tree`
- [ ] `brew install api-tree`
- [ ] `winget install api-tree`

## 快速開始

```bash
# 連接本機伺服器（預設 localhost:8080）
api-tree

# 指定伺服器
api-tree http://localhost:9090

# 讀取本機檔案
api-tree ./openapi.json
```

## 用法

### 基礎

```bash
api-tree                              # 預設連接 localhost:8080
api-tree http://localhost:9090        # 指定伺服器
api-tree /path/to/openapi.json        # 本機檔案
api-tree -s auth                      # 搜尋含 "auth" 的介面
api-tree --html                       # 匯出 HTML
```

> 如果 URL 不含路徑（如 `http://localhost:9090`），工具會自動附加 `/v3/api-docs`。若介面檔案在其他路徑，請直接指定完整 URL。

### Agent 輸出（AI 輔助開發）

生成 LLM 最佳化的 API 結構表示，適用於向 AI 程式設計助手提供 API 上下文。

```bash
api-tree --agent-output markdown      # Markdown 表格
api-tree --agent-output json          # 結構化 JSON
api-tree --agent-output curl          # 可直接使用的 curl 命令
```

**使用場景：**
- 將 API 結構餵給 ChatGPT/Claude 生成程式碼
- 批次生成 curl 命令用於介面測試
- 為 AI 結對程式設計建立 API 參考文件

### RAG 知識庫匯出

為向量資料庫和 RAG 檢索系統生成結構化切片。

```bash
api-tree --rag-output jsonl           # 每行一個 JSON 物件（向量庫匯入用）
api-tree --rag-output json            # 完整 JSON 結構
api-tree --rag-chunk-size 20          # 每個切片的介面數（預設：10）
```

**使用場景：**
- 建構可搜尋的 API 知識庫
- 為 RAG 系統注入介面上下文
- 向嵌入模型管道餵結構化資料

### 設定

```bash
api-tree --init-config                # 產生 ~/.config/api-tree/config.json
api-tree --show-config                # 檢視目前設定
```

設定檔：
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

## 效果展示

![終端樹狀圖](/readme/img/1.png)

![搜尋過濾](/readme/img/2.png)

![HTML 匯出](/readme/img/3.png)

![色彩高亮](/readme/img/4.png)
