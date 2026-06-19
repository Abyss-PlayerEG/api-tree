# API Tree 自动更新功能设计

## 命令

```bash
api-tree update              # 检查并更新
api-tree update --check      # 只检查，不更新
```

## 核心问题

### 1. 版本号从哪来

打包时 PyInstaller 需要把版本号写死到代码里，而不是运行时读文件。

**方案**：构建脚本生成 `_version.py`，PyInstaller 打包时通过 `--hidden-import` 确保包含。

```python
# src/api_tree/app/_version.py（构建时生成，gitignore）
__version__ = "26.06.20.0200"
```

构建脚本流程：
```
1. merge_src.py 生成单文件 .py（同时生成 _version.py）
2. pyinstaller --hidden-import=api_tree.app._version 打包
3. 删除 _version.py（不提交到 git）
```

### 2. 安装类型怎么判断

用 `version` 文件 + exe 路径综合判断：

```python
def get_install_info() -> tuple[str, str]:
    """
    返回 (版本号, 安装类型)

    安装类型:
      "portable"  - 便携版（zip 解压）
      "installer" - 安装版（setup.exe 安装）
      "source"    - 源码运行
    """
    # 获取版本
    version = "DEV"
    try:
        from api_tree.app._version import __version__
        version = __version__
    except ImportError:
        pass

    # 获取安装类型
    if not getattr(sys, 'frozen', False):
        return version, "source"

    exe_dir = Path(sys.executable).parent
    version_file = exe_dir / "version"
    if version_file.exists():
        content = version_file.read_text().strip()
        if content == "installer":
            return version, "installer"

    return version, "portable"
```

`version` 文件内容：

| 内容 | 含义 | 生成时机 |
|------|------|---------|
| `portable` | 便携版 | mac-build.sh / win-build.bat 便携版打包后 |
| `installer` | 安装版 | win-build.bat Inno Setup 打包前 |
| （不存在） | 源码运行 | 不生成 |

### 3. 频道怎么判断

不搞复杂频道系统，只看 tag 前缀：

```python
def get_channel_from_version(version: str) -> str:
    if version.startswith("DEV"):
        return "dev"
    if version.startswith("BETA"):
        return "beta"
    return "stable"
```

### 4. 怎么查最新版本

```python
# 查 /releases，按频道过滤
def fetch_latest_release(channel: str) -> dict | None:
    prefix = {"stable": "V", "dev": "DEV", "beta": "BETA"}[channel]
    # GET /repos/.../releases
    # 找第一个 tag_name.startswith(prefix) 且非 draft 的 release
```

### 5. 单文件 .py 怎么更新

单文件版不支持自更新，提示用户手动下载：

```python
if install_type == "source":
    print("Source mode. Run `git pull` to update.")
    return False
```

## 完整流程

```
api-tree update
│
├─ 1. get_install_info() → (version, install_type)
│
├─ 2. get_channel_from_version(version) → channel
│
├─ 3. fetch_latest_release(channel) → release
│
├─ 4. 对比版本
│     ├─ 已是最新 → "Already up to date"
│     └─ 有新版本 → "New version: V26.06.20.1200 (current: 26.06.01.1100)"
│
├─ 5. 根据 install_type 选择更新方式
│     │
│     ├─ "source"
│     │   └─ 提示 "Run `git pull` to update"
│     │
│     ├─ "portable"
│     │   ├─ 下载对应平台 zip
│     │   ├─ SHA256 校验
│     │   ├─ 解压
│     │   ├─ 替换可执行文件
│     │   └─ "Updated. Please restart."
│     │
│     └─ "installer"
│         ├─ 下载 setup.exe
│         ├─ SHA256 校验
│         ├─ 打开安装包（os.startfile）
│         └─ "Installer opened. Follow the prompts."
│
└─ 6. 完成
```

## 平台匹配

| 平台 | 便携版 asset | 安装版 asset |
|------|------------|------------|
| macOS | `*-macos.zip` | 无 |
| Windows | `*-win64.zip`（排除 setup） | `*-setup-*-win64.exe` |
| Linux | `*-linux.zip` | 无 |

## 文件清单

### 新建

| 文件 | 说明 |
|------|------|
| `src/api_tree/app/updater.py` | 更新逻辑 |
| `src/api_tree/app/_version.py` | 构建时生成，gitignore |

### 修改

| 文件 | 改动 |
|------|------|
| `src/api_tree/app/args.py` | 添加 `update` / `--check` 参数 |
| `src/api_tree/app/core.py` | 添加 update 命令处理 |
| `src/api_tree/main.py` | 帮助文本添加 update |
| `script/mac-build.sh` | 生成 _version.py + version 文件 + hidden-import |
| `script/win-build.bat` | 同上 |
| `.gitignore` | 添加 `_version.py` |

### 不动

| 文件 | 原因 |
|------|------|
| `merge_src.py` | 单文件版不支持自更新，不需要改 |
| `args.py` 的 `__install_type__` | 不需要，改用运行时判断 |
| `setup.iss` | 已经 `dist\api-tree\*` 全量打包 |

## 构建脚本改动

### mac-build.sh

```bash
# 生成 _version.py
echo "__version__ = \"$VERSION\"" > src/api_tree/app/_version.py

# PyInstaller 打包（hidden-import 确保包含 _version）
uv run pyinstaller ... --hidden-import=api_tree.app._version src/api_tree/main.py

# 写 version 文件（便携版）
echo "portable" > dist/api-tree/version

# 清理 _version.py
rm -f src/api_tree/app/_version.py
```

### win-build.bat

```bat
REM 生成 _version.py
echo __version__ = "%VERSION%" > src\api_tree\app\_version.py

REM PyInstaller 打包
uv run pyinstaller ... --hidden-import=api_tree.app._version src\api_tree\main.py

REM 便携版 version 文件
echo portable > dist\api-tree\version

REM 打包便携版 zip

REM 安装版 version 文件
echo installer > dist\api-tree\version

REM Inno Setup 打包

REM 清理
del src\api_tree\app\_version.py
```

## 注意事项

| 问题 | 方案 |
|------|------|
| PyInstaller 不打包 _version.py | `--hidden-import=api_tree.app._version` |
| 单文件 .py 版本号 | merge_src.py 替换 `__version__` |
| 单文件 .py 自更新 | 不支持，提示 git pull |
| macOS SSL 证书 | 用 `ssl.create_default_context()` + certifi 降级 |
| 下载失败 | 回滚到 .bak 备份 |
| Windows 文件锁定 | 安装版用 `os.startfile` 打开，用户自己装 |

## 开发计划

- [ ] `.gitignore` 添加 `_version.py`
- [ ] 创建 `updater.py`
- [ ] `args.py` 添加 `update` / `--check`
- [ ] `core.py` 添加 update 处理
- [ ] `main.py` 帮助文本
- [ ] `mac-build.sh` 改动
- [ ] `win-build.bat` 改动
- [ ] macOS 便携版测试
- [ ] Windows 便携版测试
- [ ] Windows 安装版测试
- [ ] 更新 README
