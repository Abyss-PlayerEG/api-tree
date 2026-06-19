# API Tree 自动更新功能设计

## 概述

api-tree 检测新版本并从 GitHub Releases 下载更新，替换当前可执行文件。

## 命令

```bash
api-tree update              # 检查并更新
api-tree update --check      # 只检查，不更新
```

## 实际 Release 结构

基于 GitHub API 返回的 `releases/latest`：

```
tag_name: "V26.06.01.1100"      ← 版本号格式：V{yy.mm.dd.hhmm}

assets:
├── api-tree-26.06.01.1148-macos.zip           ← macOS 可执行文件
├── api-tree-26.06.01.1150-win64.zip           ← Windows 便携版
├── api-tree-26.06.01.1150.py                  ← 单文件 Python 版
├── api-tree-setup-26.06.01.1150-win64.exe     ← Windows 安装版
└── SKILL.md                                    ← 忽略
```

### 版本号解析

格式：`V{yy}.{mm}.{dd}.{hhmm}`

```python
def parse_version(v: str) -> tuple[int, ...]:
    """V26.06.01.1100 → (26, 6, 1, 1100)"""
    clean = v.lstrip("Vv").lstrip("v")
    return tuple(int(x) for x in clean.split("."))
```

### 平台匹配规则

| 平台 | 匹配关键词 | 排除关键词 |
|------|-----------|-----------|
| macOS | `macos` | `setup` |
| Windows | `win64` + `setup` (安装版) 或 `win64` (便携版) | - |
| Linux | `linux` | `setup` |

## 流程

```
api-tree update
│
├─ 1. 读取当前版本（打包时写入的 _version）
│
├─ 2. 请求 GitHub Releases API
│     GET https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest
│
├─ 3. 对比版本
│     ├─ 已是最新 → 提示 "Already up to date"
│     └─ 有新版本 → 提示 "New version: V26.06.20.1200 (current: V26.06.01.1100)"
│
├─ 4. 检测当前平台，选择 asset
│     ├─ macOS   → api-tree-*-macos.zip
│     ├─ Windows → api-tree-*-win64.zip（便携版）
│     └─ Linux   → api-tree-*-linux.zip
│
├─ 5. 下载到临时目录（显示进度条）
│
├─ 6. 解压
│
├─ 7. SHA256 校验（asset.digest 字段）
│
├─ 8. 替换当前可执行文件
│     ├─ macOS/Linux: 替换 + chmod +x
│     └─ Windows: 写 .bat 延迟替换脚本，提示重启
│
└─ 9. 提示 "Updated to V26.06.20.1200"
```

## 文件结构

```
src/api_tree/app/updater.py    # 更新逻辑
```

## 模块设计

### updater.py

```python
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

GITHUB_API = "https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest"


def get_current_version() -> str:
    """获取当前版本"""
    try:
        from api_tree._version import __version__
        return __version__
    except ImportError:
        return "DEV"


def parse_version(v: str) -> tuple[int, ...]:
    """V26.06.01.1100 → (26, 6, 1, 1100)"""
    clean = v.lstrip("Vv")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def fetch_latest_release() -> dict:
    """从 GitHub 获取最新 release 信息"""
    req = urllib.request.Request(GITHUB_API, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "api-tree",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def get_download_asset(release: dict) -> dict | None:
    """根据当前平台选择对应的下载资源"""
    system = platform.system().lower()
    assets = release.get("assets", [])

    for asset in assets:
        name = asset["name"].lower()

        if system == "darwin" and "macos" in name and name.endswith(".zip"):
            return asset

        elif system == "windows" and "win64" in name and name.endswith(".zip") and "setup" not in name:
            return asset

        elif system == "linux" and "linux" in name and name.endswith(".zip"):
            return asset

    return None


def verify_hash(filepath: str, expected_sha256: str) -> bool:
    """校验文件 SHA256"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_sha256


def get_current_exe_path() -> Path | None:
    """获取当前可执行文件路径，非打包环境返回 None"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable)
    return None


def check_update() -> tuple[str, str] | None:
    """
    检查是否有新版本

    Returns:
        (当前版本, 最新版本) 如果有更新，否则 None
    """
    current = get_current_version()
    release = fetch_latest_release()
    latest = release.get("tag_name", "")

    if not latest:
        return None

    if parse_version(latest) <= parse_version(current):
        return None

    return current, latest


def do_update() -> bool:
    """
    执行更新

    Returns:
        True 更新成功，False 更新失败
    """
    current = get_current_version()

    try:
        release = fetch_latest_release()
    except Exception as e:
        print(f"Error: Failed to check for updates: {e}")
        return False

    latest = release.get("tag_name", "")

    if parse_version(latest) <= parse_version(current):
        print("Already up to date.")
        return False

    print(f"New version: {latest} (current: {current})")

    asset = get_download_asset(release)
    if not asset:
        print("Error: No download found for your platform.")
        return False

    download_url = asset["browser_download_url"]
    expected_hash = asset.get("digest", "").replace("sha256:", "")

    print(f"Downloading {asset['name']}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, asset["name"])

        # 下载
        try:
            urllib.request.urlretrieve(download_url, zip_path)
        except Exception as e:
            print(f"Error: Download failed: {e}")
            return False

        # 校验 hash
        if expected_hash and not verify_hash(zip_path, expected_hash):
            print("Error: SHA256 verification failed.")
            return False

        # 解压
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
        except zipfile.BadZipFile:
            print("Error: Invalid zip file.")
            return False

        # 找到可执行文件
        exe_name = "api-tree.exe" if platform.system() == "Windows" else "api-tree"
        extracted = None
        for root, _, files in os.walk(tmpdir):
            if exe_name in files:
                extracted = os.path.join(root, exe_name)
                break

        if not extracted:
            print("Error: Executable not found in archive.")
            return False

        # 替换
        current_exe = get_current_exe_path()
        if current_exe is None:
            print("Running from source. Cannot self-update.")
            print(f"Download manually: {download_url}")
            return False

        backup = current_exe.with_suffix(".bak")
        shutil.copy2(current_exe, backup)

        try:
            shutil.copy2(extracted, current_exe)
            os.chmod(current_exe, 0o755)
            backup.unlink(missing_ok=True)
            print(f"Updated to {latest}")
            return True
        except Exception as e:
            shutil.copy2(backup, current_exe)
            backup.unlink(missing_ok=True)
            print(f"Update failed: {e}")
            return False
```

## 集成到 CLI

在 `args.py` 中添加 `update` 命令：

```python
elif argv[i] == "update":
    args.update = True
    i += 1
elif argv[i] == "--check" and args.update:
    args.update_check_only = True
    i += 1
```

在 `core.py` 中处理：

```python
if args.update:
    from .updater import check_update, do_update
    if args.update_check_only:
        result = check_update()
        if result:
            print(f"New version: {result[1]} (current: {result[0]})")
        else:
            print("Already up to date.")
    else:
        do_update()
    return
```

## 注意事项

| 问题 | 方案 |
|------|------|
| 非打包环境（从源码运行） | 提示用户 `git pull` |
| Windows 替换自身 | 用 .bat 脚本延迟替换 |
| 下载失败 | 回滚到备份 |
| 权限不足 | 提示 `sudo` 或手动替换 |
| 网络问题 | 提示手动下载链接 |

## 开发计划

- [ ] 创建 `updater.py` 模块
- [ ] 添加 `update` 和 `update --check` 命令
- [ ] macOS 测试
- [ ] Windows 测试
- [ ] 更新 README
