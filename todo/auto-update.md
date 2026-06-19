# API Tree 自动更新功能设计

## 概述

api-tree 检测新版本并从 GitHub Releases 下载更新，支持便携版和安装版两种更新方式。

## 命令

```bash
api-tree update              # 检查并更新
api-tree update --check      # 只检查，不更新
```

## 版本标识文件

打包时生成 `version` 文件，与可执行文件同目录，标识安装类型：

| 文件内容 | 含义 | 更新方式 |
|---------|------|---------|
| `dev.zip` | 便携开发版 | 替换可执行文件 |
| `v.zip` | 便携正式版 | 替换可执行文件 |
| `v.exe` | 安装版 | 下载 setup.exe 静默运行 |

### 生成时机

```bash
# mac-build.sh（便携版）
echo "v.zip" > dist/api-tree/version

# win-build.bat（便携版打包后）
echo "v.zip" > dist/api-tree/version

# win-build.bat（Inno Setup 安装版打包时）
echo "v.exe" > dist/api-tree/version

# 开发环境
echo "dev.zip" > src/api-tree/version
```

## 实际 Release 结构

```
tag_name: "V26.06.01.1100"

assets:
├── api-tree-26.06.01.1148-macos.zip           ← macOS
├── api-tree-26.06.01.1150-win64.zip           ← Windows 便携版
├── api-tree-26.06.01.1150.py                  ← 单文件 Python 版
├── api-tree-setup-26.06.01.1150-win64.exe     ← Windows 安装版
└── SKILL.md
```

## 更新流程

```
api-tree update
│
├─ 1. 读取当前版本（_version）
├─ 2. 读取安装类型（version 文件）
│
├─ 3. 请求 GitHub Releases API
│
├─ 4. 对比版本
│     ├─ 已是最新 → "Already up to date"
│     └─ 有新版本 → "New version: V26.06.20.1200"
│
├─ 5. 根据安装类型选择更新方式
│     │
│     ├─ 便携版（dev.zip / v.zip）
│     │   ├─ 下载对应平台 zip
│     │   ├─ SHA256 校验
│     │   ├─ 解压
│     │   ├─ 替换可执行文件
│     │   └─ "Updated to V26.06.20.1200"
│     │
│     └─ 安装版（v.exe）
│         ├─ 下载 setup.exe
│         ├─ SHA256 校验
│         ├─ 静默运行：setup.exe /VERYSILENT /NORESTART
│         └─ "Updated to V26.06.20.1200, please restart"
│
└─ 6. 完成
```

## 平台匹配

| 平台 | 便携版 asset | 安装版 asset |
|------|------------|------------|
| macOS | `*-macos.zip` | 无 |
| Windows | `*-win64.zip`（排除 setup） | `*-setup-*-win64.exe` |
| Linux | `*-linux.zip` | 无 |

## 模块设计

### updater.py

```python
import hashlib
import json
import os
import platform
import shutil
import subprocess
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


def get_install_type() -> str:
    """
    读取安装类型

    Returns:
        "dev.zip" / "v.zip" / "v.exe" / "unknown"
    """
    exe_path = get_current_exe_path()
    if exe_path is None:
        return "dev.zip"

    version_file = exe_path.parent / "version"
    if version_file.exists():
        return version_file.read_text().strip()

    return "unknown"


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


def get_download_asset(release: dict, install_type: str) -> dict | None:
    """
    根据平台和安装类型选择下载资源

    Args:
        release: GitHub release 数据
        install_type: "dev.zip" / "v.zip" / "v.exe"
    """
    system = platform.system().lower()
    assets = release.get("assets", [])
    is_installer = install_type.endswith(".exe")

    for asset in assets:
        name = asset["name"].lower()

        if system == "darwin":
            if "macos" in name and name.endswith(".zip"):
                return asset

        elif system == "windows":
            if is_installer:
                if "setup" in name and "win64" in name and name.endswith(".exe"):
                    return asset
            else:
                if "win64" in name and name.endswith(".zip") and "setup" not in name:
                    return asset

        elif system == "linux":
            if "linux" in name and name.endswith(".zip"):
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


def _update_portable(asset: dict, expected_hash: str) -> bool:
    """便携版更新：下载 zip → 替换可执行文件"""
    download_url = asset["browser_download_url"]
    print(f"Downloading {asset['name']}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, asset["name"])

        try:
            urllib.request.urlretrieve(download_url, zip_path)
        except Exception as e:
            print(f"Error: Download failed: {e}")
            return False

        if expected_hash and not verify_hash(zip_path, expected_hash):
            print("Error: SHA256 verification failed.")
            return False

        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
        except zipfile.BadZipFile:
            print("Error: Invalid zip file.")
            return False

        exe_name = "api-tree.exe" if platform.system() == "Windows" else "api-tree"
        extracted = None
        for root, _, files in os.walk(tmpdir):
            if exe_name in files:
                extracted = os.path.join(root, exe_name)
                break

        if not extracted:
            print("Error: Executable not found in archive.")
            return False

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
            return True
        except Exception as e:
            shutil.copy2(backup, current_exe)
            backup.unlink(missing_ok=True)
            print(f"Update failed: {e}")
            return False


def _update_installer(asset: dict, expected_hash: str) -> bool:
    """安装版更新：下载 setup.exe → 静默运行"""
    download_url = asset["browser_download_url"]
    print(f"Downloading {asset['name']}...")

    with tempfile.TemporaryDirectory() as tmpdir:
        exe_path = os.path.join(tmpdir, asset["name"])

        try:
            urllib.request.urlretrieve(download_url, exe_path)
        except Exception as e:
            print(f"Error: Download failed: {e}")
            return False

        if expected_hash and not verify_hash(exe_path, expected_hash):
            print("Error: SHA256 verification failed.")
            return False

        print("Running installer...")
        try:
            subprocess.run([exe_path, "/VERYSILENT", "/NORESTART"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installer failed: {e}")
            return False


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

    install_type = get_install_type()
    asset = get_download_asset(release, install_type)

    if not asset:
        print("Error: No download found for your platform.")
        return False

    expected_hash = asset.get("digest", "").replace("sha256:", "")

    if install_type.endswith(".exe"):
        success = _update_installer(asset, expected_hash)
    else:
        success = _update_portable(asset, expected_hash)

    if success:
        print(f"Updated to {latest}")
        if install_type.endswith(".exe"):
            print("Please restart api-tree.")

    return success
```

## 集成到 CLI

### args.py 添加参数

```python
elif argv[i] == "update":
    args.update = True
    i += 1
elif argv[i] == "--check" and args.update:
    args.update_check_only = True
    i += 1
```

### core.py 添加处理

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

## 构建脚本修改

### mac-build.sh

```bash
# 打包后生成 version 文件
echo "v.zip" > dist/api-tree/version
```

### win-build.bat

```bash
REM 便携版打包后
echo v.zip > dist\api-tree\version

REM Inno Setup 安装版打包时
echo v.exe > dist\api-tree\version
```

## 注意事项

| 问题 | 方案 |
|------|------|
| 非打包环境（源码运行） | 提示 `git pull` |
| Windows 安装版文件锁定 | setup.exe /VERYSILENT 自动处理 |
| 下载失败 | 回滚到备份 |
| 权限不足 | 提示手动替换 |
| hash 校验失败 | 中止更新，保留旧版本 |
| macOS 无安装版 | 只支持便携版更新 |

## 开发计划

- [ ] 创建 `updater.py` 模块
- [ ] 添加 `update` 和 `update --check` 命令
- [ ] 修改构建脚本生成 `version` 文件
- [ ] macOS 测试
- [ ] Windows 便携版测试
- [ ] Windows 安装版测试
- [ ] 更新 README
