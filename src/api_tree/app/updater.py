import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

GITHUB_API = "https://api.github.com/repos/Abyss-PlayerEG/api-tree/releases/latest"
VERSION_RE = re.compile(r"^\d{2}\.\d{2}\.\d{2}\.\d{4}$")


def _get_version_and_tag() -> tuple[str, str]:
    try:
        from api_tree import __tag__, __version__
        return str(__version__), str(__tag__)
    except ImportError:
        try:
            from api_tree._version import __tag__, __version__
            return str(__version__), str(__tag__)
        except ImportError:
            import sys
            mod = sys.modules.get("__main__")
            if mod:
                v = getattr(mod, "__version__", "DEV")
                t = getattr(mod, "__tag__", "dev")
                return str(v), str(t)
            return "DEV", "dev"


def is_release_version() -> bool:
    version, _ = _get_version_and_tag()
    return bool(VERSION_RE.match(version))


def get_current_version() -> str:
    version, _ = _get_version_and_tag()
    return version


def parse_version(v: str) -> tuple[int, ...]:
    v = v.lstrip("Vv")
    return tuple(int(x) for x in v.split("."))


def compare_versions(current: str, latest: str) -> int:
    c = parse_version(current)
    l = parse_version(latest)
    if c < l:
        return -1
    if c > l:
        return 1
    return 0


def detect_install_type() -> str:
    _, tag = _get_version_and_tag()
    if tag == "python-script":
        return "py"
    if tag == "macos-zip":
        return "macos"
    if tag == "win64-zip":
        install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "api-tree"
        if (install_dir / "uninstall.exe").exists():
            return "win64-setup"
        return "win64"
    return "unknown"


def fetch_latest_release() -> dict[str, object] | None:
    req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "api-tree"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data: dict[str, object] = json.loads(resp.read().decode())
            return data
    except Exception:
        return None


def find_asset(assets: list[dict], install_type: str) -> dict | None:
    suffix_map = {
        "py": ".py",
        "macos": "-macos.zip",
        "win64": "-win64.zip",
        "win64-setup": "-win64.exe",
    }
    suffix = suffix_map.get(install_type)
    if not suffix:
        return None
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(suffix) and "SKILL" not in name:
            return asset
    return None


def _get_install_dir() -> Path:
    exe = Path(sys.executable).resolve()
    if exe.suffix == ".exe" and exe.parent.name == "api-tree":
        return exe.parent
    if sys.platform == "darwin":
        candidate = Path("/usr/local/bin/api-tree")
        if candidate.exists():
            return candidate
    if exe.stem == "api-tree":
        return exe.parent
    return exe.parent


def _download(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "api-tree"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def _replace_py(asset_url: str) -> bool:
    current = Path(sys.argv[0]).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp) / "update.py"
        if not _download(asset_url, tmp_file):
            return False
        shutil.copy2(tmp_file, current)
    return True


def _replace_zip(asset_url: str) -> bool:
    install_dir = _get_install_dir()
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "update.zip"
        if not _download(asset_url, zip_path):
            return False
        extract_dir = Path(tmp) / "extract"
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            print("Update package is corrupted.")
            return False
        top_items = list(extract_dir.iterdir())
        source = top_items[0] if len(top_items) == 1 and top_items[0].is_dir() else extract_dir
        for item in install_dir.iterdir():
            if item.name == "config.json":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        for item in source.iterdir():
            dest = install_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
            if sys.platform != "win32" and item.name in ("api-tree", "install.sh", "uninstall.sh"):
                dest.chmod(0o755)
    return True


def _replace_win64_setup(asset_url: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        exe_path = Path(tmp) / "update-setup.exe"
        if not _download(asset_url, exe_path):
            return False
        print(f"Launching installer: {exe_path}")
        if sys.platform == "win32":
            os.startfile(str(exe_path))
        else:
            subprocess.Popen([str(exe_path)])
    return True


def check_update() -> tuple[str, str] | None:
    release = fetch_latest_release()
    if not release:
        return None
    tag = str(release.get("tag_name", ""))
    latest = tag.lstrip("Vv")
    current_version, _ = _get_version_and_tag()
    if compare_versions(current_version, latest) < 0:
        return (current_version, latest)
    return None


def perform_update() -> None:
    release = fetch_latest_release()
    if not release:
        print("Failed to check for updates. Please check your network connection.")
        return
    tag = str(release.get("tag_name", ""))
    latest = tag.lstrip("Vv")
    current_version, _ = _get_version_and_tag()
    if compare_versions(current_version, latest) >= 0:
        print("Already up to date.")
        return
    print(f"New version available: {current_version} -> {latest}")
    install_type = detect_install_type()
    raw_assets = release.get("assets", [])
    assets = raw_assets if isinstance(raw_assets, list) else []
    asset = find_asset(assets, install_type)
    if not asset:
        print(f"No update package found for install type '{install_type}'.")
        return
    url = str(asset.get("browser_download_url", ""))
    name = str(asset.get("name", ""))
    print(f"Downloading {name}...")
    ok = False
    if install_type == "py":
        ok = _replace_py(url)
    elif install_type in ("macos", "win64"):
        ok = _replace_zip(url)
    elif install_type == "win64-setup":
        ok = _replace_win64_setup(url)
    if ok:
        print("Update complete.")
    else:
        print("Update failed.")
