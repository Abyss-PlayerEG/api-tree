# Update 命令实现计划

## 概述

为 `api-tree` CLI 添加 `update` 和 `update --check` 子命令，支持从 GitHub Releases 自动检查和更新。

---

## 版本格式

当前版本格式为 `yy.mm.dd.hhmm`（如 `25.06.20.1430`），比较时按数字逐段比较。

---

## 版本准入限制

**只有正式版本（release version）才允许使用 `update` 和 `update --check` 命令。**

判定规则：
- 版本号匹配 `yy.mm.dd.hhmm` 格式（正则 `^\d{2}\.\d{2}\.\d{2}\.\d{4}$`）→ **正式版本**，允许更新
- 其他（`DEV`、`1.0.0`、空值、自定义前缀等）→ **非正式版本**，拒绝更新

拒绝时输出：
```
Current version is not within the supported update range.
```

实现位置：`updater.py` 中的 `is_release_version() -> bool` 函数，在 `check_update()` 和 `perform_update()` 入口处校验。正常打印后 `return`，不报错退出。

---

## `__tag__` 标识系统

在 `_version.py` 中新增 `__tag__` 变量，标识当前构建的平台和类型。

### 标签值

| `__tag__` | 含义 |
|-----------|------|
| `python-script` | 单文件 `.py` |
| `macos-zip` | macOS zip 分发 |
| `win64-zip` | Windows zip 分发（同一二进制也用于 exe 安装包） |

> Windows 的 zip 和 exe 安装包使用同一二进制，`__tag__` 统一为 `win64-zip`。
> 运行时通过检测 `uninstall.exe` 区分是 zip 解压还是安装包安装。

### `_version.py` 生成格式

```python
__version__ = "26.06.01.1100"
__tag__ = "macos-zip"
```

### 改动文件

1. **`src/api_tree/tools/merge_src.py`**：
   - 添加 `--tag` CLI 参数（默认 `python-script`）
   - 写入 `_version.py` 时包含 `__tag__`
   - 合并输出的单文件 `.py` 中嵌入 `__tag__`

2. **`src/api_tree/__init__.py`**：
   - 导入 `__tag__`，回退为 `"dev"`

3. **`script/mac-build.sh`**：
   - 生成单文件 `.py` 后，重新生成 `_version.py`（`--tag macos-zip`）再执行 PyInstaller

4. **`script/win-build.bat`**：
   - 生成 `_version.py`（`--tag win64-zip`）后执行 PyInstaller

### 与 `detect_install_type()` 的关系

`__tag__` 提供分发信息，`detect_install_type()` 结合运行时检测：
- `__tag__ == "python-script"` → `"py"`
- `__tag__ == "macos-zip"` → `"macos"`
- `__tag__ == "win64-zip"` + 检查 `uninstall.exe` → `"win64-setup"` 或 `"win64"`

---

## 命令设计

### `api-tree update --check`

- 查询 GitHub Releases API 获取最新版本
- 与当前内置版本对比
- 输出：
  - 有更新：显示当前版本 → 最新版本，提示运行 `api-tree update`
  - 已是最新：提示已是最新版本
  - 网络错误：提示检查网络连接

### `api-tree update`

- 执行与 `--check` 相同的版本检查
- 如果有更新：
  1. 检测当前安装类型（单文件 py / macOS zip / Windows zip / Linux zip）
  2. 从 release assets 中匹配对应资产
  3. 下载到临时目录
  4. 按安装类型执行替换策略
  5. 清理临时文件
  6. 提示更新完成
- 如果已是最新：提示无需更新

---

## 需要修改的文件

### 1. `src/api_tree/app/updater.py`（新建）

核心更新逻辑模块：

```
函数：
- is_release_version() -> bool
    检查当前版本是否为正式版本（匹配 yy.mm.dd.hhmm 格式）
    DEV / 自定义版本 / 空值均返回 False

- get_current_version() -> str
    从 __version__ 获取当前版本

- fetch_latest_release() -> dict | None
    请求 https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest
    返回 {tag_name, name, prerelease, assets: [{name, browser_download_url}]}
    网络错误返回 None
    注意：tag_name 格式为 "V26.06.01.1100"，需去掉 "V" 前缀

- parse_version(v: str) -> tuple[int, ...]
    将 "V26.06.01.1100" 或 "26.06.01.1100" 解析为 (26, 6, 1, 1100)
    自动去掉 "V" 前缀后按 "." 分割转 int

- compare_versions(current: str, latest: str) -> int
    -1 = current 更旧, 0 = 相同, 1 = current 更新

- detect_install_type() -> str
    检测当前安装类型：py / macos / win64 / win64-setup / linux
    - __tag__ == "py" → "py"
    - __tag__ == "macos" → "macos"
    - __tag__ == "win64" + 安装目录有 uninstall.exe → "win64-setup"
    - __tag__ == "win64" + 无 uninstall.exe → "win64"
    - __tag__ == "linux" → "linux"
    - __tag__ == "dev" → 不应到达（已被 is_release_version 拦截）

- find_asset(assets: list, install_type: str) -> dict | None
    从 release assets 中匹配对应安装类型的资产
    install_type 由 detect_install_type() 返回
    匹配规则：
      - "py"           → 找 "api-tree-{version}.py"
      - "macos"        → 找 "api-tree-{version}-macos.zip"
      - "win64"        → 找 "api-tree-{version}-win64.zip"
      - "win64-setup"  → 找 "api-tree-setup-{version}-win64.exe"
      - "linux"        → 找 "api-tree-{version}-linux.zip"
    跳过 SKILL.md

- download_and_install(url: str, install_type: str, version: str) -> None
    根据 install_type 执行不同替换策略：
    - "py": 下载 .py → 覆盖当前文件
    - "macos"/"linux": 下载 zip → 清空旧目录 → 解压 → 设执行权限
    - "win64": 下载 zip → 清空旧目录 → 解压
    - "win64-setup": 下载 .exe 安装器 → 运行弹出安装窗口 → 用户手动完成安装
    通用流程：下载到临时目录 → 替换 → 清理临时文件

- check_update() -> tuple[str, str] | None
    返回 (current_version, latest_version) 或 None（已是最新/网络错误）

- perform_update() -> None
    完整更新流程入口
```

### 2. `src/api_tree/app/args.py`（修改）

在 `Args` dataclass 添加字段：
```python
update: bool = False       # 执行更新
update_check: bool = False # 仅检查更新
```

在 `parse_args()` 添加解析逻辑：
```python
elif argv[i] == "update":
    args.update = True
    i += 1
    # 检查后续是否有 --check
    if i < len(argv) and argv[i] == "--check":
        args.update_check = True
        i += 1
```

注意：需要处理 `update --check` 作为子命令的解析，不是 `--check` 作为独立 flag。

### 3. `src/api_tree/app/core.py`（修改）

在 `run()` 函数开头添加 update 处理：
```python
if args.update:
    from .updater import is_release_version, check_update, perform_update
    if not is_release_version():
        print("Current version is not within the supported update range.")
        return
    if args.update_check:
        result = check_update()
        if result:
            current, latest = result
            print(f"New version available: {current} → {latest}")
            print("Run 'api-tree update' to install.")
        else:
            print("Already up to date.")
    else:
        perform_update()
    return
```

### 4. `src/api_tree/main.py`（修改）

更新模块顶部的 Usage 文档字符串，添加：
```
    api-tree update                # Update to latest version
    api-tree update --check        # Check for updates (no install)
```

### 5. `src/api_tree/installer/macOS/install.sh`（不修改）

原地替换二进制，symlink 指向不变，无需修改安装脚本。

---

## GitHub Release 资产命名约定

实际构建脚本产出格式（基于 API 返回）：
- macOS zip: `api-tree-{version}-macos.zip`
- Windows zip: `api-tree-{version}-win64.zip`（含 `_internal/` + `api-tree.exe` + 卸载程序）
- Windows 安装包: `api-tree-setup-{version}-win64.exe`
- Linux zip: `api-tree-{version}-linux.zip`
- 单文件 py: `api-tree-{version}.py`
- 文档（跳过）: `SKILL.md`

注意：
- `tag_name` 格式为 `V26.06.01.1100`（带 V 前缀）
- asset 文件名中的版本可能与 tag 不同（如 tag 1100 vs asset 1148/1150）
- `find_asset()` 按 `-{platform}.zip` 后缀或 `.py` 后缀匹配，不依赖版本号

---

## 平台检测逻辑

```python
from api_tree import __tag__

def detect_install_type() -> str:
    """根据 __tag__ 和运行时检测确定安装类型"""
    if __tag__ == "py":
        return "py"
    if __tag__ == "macos":
        return "macos"
    if __tag__ == "win64":
        # 检查是否有卸载程序（安装包安装的标志）
        from pathlib import Path
        import os
        install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "api-tree"
        if (install_dir / "uninstall.exe").exists():
            return "win64-setup"
        return "win64"
    if __tag__ == "linux":
        return "linux"
    return "unknown"
```

---

## 二进制替换策略

### 单文件 .py（`install_type == "py"`）
- 当前文件路径：`sys.argv[0]` 或 `Path(__file__).resolve()`
- 替换方式：
  1. 下载最新 `.py` 到临时目录（文件名如 `api-tree-26.06.20.0212.py`）
  2. 用下载文件覆盖当前脚本路径（保留用户自定义的文件名和位置）
  3. 设置执行权限（如有需要）
  4. 清理临时文件
- 无需 sudo，权限通常足够

### macOS / Linux zip（`install_type in ("macos", "linux")`）
- 当前二进制路径：`sys.executable` 或 `shutil.which("api-tree")`
- PyInstaller 打包的二进制在 `sys.executable`
- zip 内容：二进制文件 + `_internal/`（如有）+ `install.sh`/`uninstall.sh`
- 替换方式：
  1. 删除旧安装目录内容（避免残留多余文件如 sh 脚本）
  2. 解压 zip 到安装目录
  3. 设置执行权限
- macOS 安装目录通常为 `/usr/local/bin/api-tree/`（onedir 模式）
- 可能需要 sudo（提示用户）

### Windows zip（`install_type == "win64"`）
- 安装目录：`%LOCALAPPDATA%\api-tree\`
- zip 内容：`_internal/` + `api-tree.exe` + 卸载程序（+ `install.bat`/`uninstall.bat`）
- 替换方式：
  1. 删除旧安装目录内容（避免残留多余文件如 bat 脚本）
  2. 解压 zip 到安装目录
- 保留 `config.json`（在 `~\.config\api-tree\`，不在安装目录中）
- 如果文件被占用，提示用户关闭后重试

### Windows 安装包（`install_type == "win64-setup"`）
- 安装目录：`%LOCALAPPDATA%\api-tree\`
- 检测方式：安装目录下存在 `uninstall.exe` 或注册表有卸载项
- 替换方式：
  1. 下载 `api-tree-setup-{version}-win64.exe` 到临时目录
  2. 运行安装包，弹出安装窗口，由用户手动完成安装
  3. 提示用户安装完成后清理临时文件（或由安装器自行处理）
- 安装器会自动处理 PATH、注册表、卸载项等

---

## 网络请求

使用 Python 标准库 `urllib.request`（项目 dependencies 为空，不引入第三方库）：

```python
import urllib.request
import json

url = "https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest"
req = urllib.request.Request(url, headers={"User-Agent": "api-tree"})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode())
```

---

## 错误处理

| 场景 | 处理 |
|------|------|
| 非正式版本 | `Current version is not within the supported update range.` |
| 无网络 | 提示 "无法连接到 GitHub，请检查网络" |
| API 限流 | 提示 "GitHub API 请求过多，请稍后重试" |
| 无对应平台资产 | 提示 "未找到适用于当前安装类型的更新包" |
| 权限不足（macOS/Linux） | 提示 "需要管理员权限，请使用 sudo 运行" |
| 文件被占用（Windows） | 提示 "文件被占用，请关闭 api-tree 后重试" |
| 下载失败 | 提示具体错误，清理临时文件 |
| 解压失败 | 提示 "更新包损坏"，清理临时文件 |

---

## 实现顺序

1. 修改 `merge_src.py` — 添加 `--tag` 参数，生成含 `__tag__` 的 `_version.py` 和单文件
2. 修改 `__init__.py` — 导入 `__tag__`
3. 修改 `mac-build.sh` — PyInstaller 前重新生成 `_version.py`（`--tag macos`）
4. 修改 `win-build.bat` — PyInstaller 前生成 `_version.py`（`--tag win64`）
5. 创建 `updater.py` — 核心更新逻辑（含版本准入 + `detect_install_type()`）
6. 修改 `args.py` — 添加参数解析
7. 修改 `core.py` — 添加路由
8. 修改 `main.py` — 更新帮助文档
9. 测试 `update --check` 流程
10. 测试 `update` 完整流程（可 mock 下载）

---

## 注意事项

- 不引入第三方依赖，仅用标准库
- GitHub API 未认证请求限制为 60次/小时，足够使用
- 版本号为日期格式，比较时逐段数字比较
- 更新时保留配置文件（`~/.config/api-tree/config.json`）
- 单文件版（.py）和包版（PyInstaller onedir）都需要支持更新
- 只有正式版本（yy.mm.dd.hhmm 格式）才允许更新，DEV 等开发版本拒绝
- Windows zip 包含 `_internal/` + `api-tree.exe` + 卸载程序，需先清空旧目录再解压
- Windows 安装包下载后直接运行，弹出安装窗口由用户手动完成
