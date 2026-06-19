# API Tree 自动更新功能设计

## 概述

api-tree 检测新版本并从 GitHub Releases 下载更新，替换当前可执行文件。

## 命令

```bash
api-tree update              # 检查并更新
api-tree update --check      # 只检查，不更新
```

## 流程

```
api-tree update
│
├─ 1. 读取当前版本（_version 或打包时写入的版本）
│
├─ 2. 请求 GitHub Releases API
│     GET https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest
│
├─ 3. 对比版本
│     ├─ 已是最新 → 提示 "Already up to date"
│     └─ 有新版本 → 提示 "New version: 1.2.0 (current: 1.1.0)"
│
├─ 4. 检测当前平台
│     ├─ macOS → 下载 *-macos.zip
│     └─ Windows → 下载 *-win64.zip
│
├─ 5. 下载到临时目录
│
├─ 6. 解压
│
├─ 7. 替换当前可执行文件
│     ├─ macOS: mv /tmp/api-tree /usr/local/bin/api-tree
│     └─ Windows: 覆盖当前 exe（需要延迟替换 bat）
│
└─ 8. 提示 "Updated to 1.2.0"
```

## 文件结构

```
src/api_tree/app/updater.py    # 更新逻辑
```

## 模块设计

### updater.py

```python
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


def fetch_latest_release() -> dict:
    """从 GitHub 获取最新 release 信息"""
    req = urllib.request.Request(GITHUB_API, headers={"Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def parse_version(v: str) -> tuple[int, ...]:
    """解析版本号为可比较的元组"""
    # 处理 "dev-26.06.20.0054" 格式
    clean = v.split("-", 1)[-1] if "-" in v else v
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def get_download_asset(release: dict) -> dict | None:
    """根据当前平台选择对应的下载资源"""
    system = platform.system().lower()
    for asset in release.get("assets", []):
        name = asset["name"].lower()
        if system == "darwin" and "macos" in name and name.endswith(".zip"):
            return asset
        elif system == "windows" and "win64" in name and name.endswith(".zip"):
            return asset
        elif system == "linux" and "linux" in name and name.endswith(".zip"):
            return asset
    return None


def get_current_exe_path() -> Path:
    """获取当前可执行文件路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包
        return Path(sys.executable)
    # 开发模式，返回 None
    return None


def check_update() -> tuple[str, str] | None:
    """
    检查是否有新版本

    Returns:
        (当前版本, 最新版本) 如果有更新，否则 None
    """
    current = get_current_version()
    release = fetch_latest_release()
    latest = release.get("tag_name", "").lstrip("v")

    if not latest:
        return None

    if parse_version(latest) <= parse_version(current):
        return None

    return current, latest


def do_update() -> bool:
    """
    执行更新：下载新版本并替换当前可执行文件

    Returns:
        True 更新成功，False 更新失败
    """
    current = get_current_version()
    release = fetch_latest_release()
    latest = release.get("tag_name", "").lstrip("v")

    if parse_version(latest) <= parse_version(current):
        print("Already up to date.")
        return False

    print(f"New version available: {latest} (current: {current})")

    asset = get_download_asset(release)
    if not asset:
        print("Error: No download found for your platform.")
        return False

    download_url = asset["browser_download_url"]
    print(f"Downloading {asset['name']}...")

    # 下载到临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, asset["name"])
        urllib.request.urlretrieve(download_url, zip_path)

        # 解压
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmpdir)

        # 找到解压后的可执行文件
        exe_name = "api-tree.exe" if platform.system() == "Windows" else "api-tree"
        extracted = os.path.join(tmpdir, exe_name)

        if not os.path.exists(extracted):
            print("Error: Executable not found in archive.")
            return False

        # 替换当前可执行文件
        current_exe = get_current_exe_path()
        if current_exe is None:
            print("Error: Cannot determine executable path (running from source?).")
            print(f"Download manually: {download_url}")
            return False

        # 备份旧版本
        backup = current_exe.with_suffix(".bak")
        shutil.copy2(current_exe, backup)

        try:
            shutil.copy2(extracted, current_exe)
            os.chmod(current_exe, 0o755)
            backup.unlink(missing_ok=True)
            print(f"Updated to {latest}")
            return True
        except Exception as e:
            # 回滚
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
