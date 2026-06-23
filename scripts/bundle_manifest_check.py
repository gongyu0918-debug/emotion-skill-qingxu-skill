#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
IGNORE_FILE = ROOT / ".clawhubignore"
MANIFEST_ITEM_RE = re.compile(r"^\s*-\s+`([^`]+)`\s*$")


def to_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_ignore_patterns() -> list[str]:
    return [
        line.strip()
        for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def ignored(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if path == prefix or path.startswith(f"{prefix}/"):
                return True
        elif path == pattern:
            return True
    return False


def actual_bundle_files() -> list[str]:
    patterns = read_ignore_patterns()
    files: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = to_posix(path)
        parts = rel.split("/")
        if any(part.startswith(".") for part in parts):
            continue
        if "__pycache__" in parts or path.suffix == ".pyc":
            continue
        if ignored(rel, patterns):
            continue
        files.append(rel)
    return sorted(files)


def documented_bundle_files() -> list[str]:
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    inside = False
    files: list[str] = []
    for line in lines:
        if line.strip() == "ClawHub publish now ships the Markdown-first skill bundle:":
            inside = True
            continue
        if inside and line.startswith("The GitHub repository keeps"):
            break
        if inside:
            match = MANIFEST_ITEM_RE.match(line)
            if match:
                files.append(match.group(1))
    return sorted(files)


def check_manifest() -> dict[str, Any]:
    actual = actual_bundle_files()
    documented = documented_bundle_files()
    return {
        "ok": actual == documented,
        "actual_count": len(actual),
        "documented_count": len(documented),
        "missing_from_docs": sorted(set(actual) - set(documented)),
        "missing_from_bundle": sorted(set(documented) - set(actual)),
        "actual": actual,
        "documented": documented,
    }


def main() -> int:
    result = check_manifest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
