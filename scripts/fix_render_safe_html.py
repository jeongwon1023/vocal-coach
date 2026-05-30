#!/usr/bin/env python3
"""깨진 unsafe_allow_html 잔여 + st.markdown 일괄 정리."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"
SKIP = {"utils.py"}
IMPORT = "from ui.utils import render_safe_html\n"

ORPHAN_UNSAFE = re.compile(r"^\s*unsafe_allow_html\s*=\s*True,?\s*\n", re.MULTILINE)
MARKDOWN_UNSAFE = re.compile(
    r"st\.markdown\(\s*(.*?)\s*,\s*(?:\n\s*)?unsafe_allow_html\s*=\s*True\s*,?\s*\)",
    re.DOTALL,
)
MARKDOWN_PLAIN = re.compile(
    r"st\.markdown\(\s*(.*?)\s*\)(?!\s*#)",
    re.DOTALL,
)


def _needs_import(content: str) -> bool:
    return "render_safe_html(" in content and "from ui.utils import render_safe_html" not in content


def _insert_import(content: str) -> str:
    if not _needs_import(content):
        return content
    lines = content.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith(("import ", "from __future__", "from ui.")):
            insert_at = i + 1
    lines.insert(insert_at, IMPORT)
    return "".join(lines)


def _fix_file(path: Path) -> None:
    if path.name in SKIP:
        return
    text = path.read_text(encoding="utf-8")
    original = text

    text = text.replace("from ui.html_render import render_html\n", "")
    text = text.replace("render_html(", "render_safe_html(")

    # 1) orphaned unsafe lines after partial refactor
    text = ORPHAN_UNSAFE.sub("", text)

    # 2) st.markdown(..., unsafe_allow_html=True)
    text, _ = MARKDOWN_UNSAFE.subn(r"render_safe_html(\1)", text)

    # 3) trailing comma before ) on render_safe_html multiline
    text = re.sub(r",\s*\n(\s*)\)", r"\n\1)", text)

    text = _insert_import(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"fixed: {path.relative_to(ROOT)}")


def main() -> None:
    for path in sorted(UI_DIR.rglob("*.py")):
        _fix_file(path)

    remaining = []
    for path in UI_DIR.rglob("*.py"):
        if path.name == "utils.py":
            continue
        t = path.read_text(encoding="utf-8")
        if "unsafe_allow_html=True" in t:
            remaining.append(str(path.relative_to(ROOT)))
    if remaining:
        print("Still has unsafe_allow_html:", remaining)
    else:
        print("All ui files clean (except utils.py).")


if __name__ == "__main__":
    main()
