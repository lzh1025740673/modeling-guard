"""Build a deterministic source ZIP using explicit public-content roots."""

import hashlib
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modeling_guard import __version__

ROOT_FILES = {"README.md", "README.zh-CN.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
              "CHANGELOG.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml", ".gitignore", ".gitattributes",
              "RUN_DEMO.cmd", "RUN_DEMO.ps1"}
DIRECTORIES = ("modeling_guard", "tests", "docs", "scripts", ".github", "extras/codex-student-pack")
EXTENSIONS = {".py", ".md", ".json", ".csv", ".toml", ".yml", ".yaml", ".ps1", ".cmd", ".txt", ".svg", ".html"}


def public_files():
    selected = [ROOT / name for name in ROOT_FILES]
    for name in DIRECTORIES:
        for path in (ROOT / name).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            if any(p in ("__pycache__", ".git", ".venv", ".modeling_guard") for p in path.parts):
                continue
            if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
                raise RuntimeError("Linked content is not distributable: " + path.name)
            selected.append(path)
    return sorted(selected, key=lambda p: p.relative_to(ROOT).as_posix())


def build():
    prefix = "modeling-guard-" + __version__
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / (prefix + ".zip")
    selected = public_files()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in selected:
            name = prefix + "/" + path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, path.read_bytes())
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / (archive.name + ".sha256")).write_text(sha + "  " + archive.name + "\n", encoding="ascii")
    print(f"Built {archive.name}: {len(selected)} files, {archive.stat().st_size} bytes\nSHA256 {sha}")
    return archive


if __name__ == "__main__":
    build()
