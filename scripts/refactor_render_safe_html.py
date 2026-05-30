#!/usr/bin/env python3
"""st.markdown(..., unsafe_allow_html=True) -> render_safe_html(...) 일괄 교체."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

SKIP = {"utils.py", "html_render.py"}
IMPORT = "from ui.utils import render_safe_html\n"

MARKDOWN_UNSAFE = re.compile(
    r"st\.markdown\(\s*(.*?)\s*,\s*(?:\n\s*)?unsafe_allow_html\s*=\s*True\s*\)",
    re.DOTALL,
)


def _insert_import(content: str) -> str:
    if "from ui.utils import render_safe_html" in content:
        return content
    lines = content.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import streamlit") or line.startswith("from ui.") or line.startswith("from __future__"):
            insert_at = i + 1
    lines.insert(insert_at, IMPORT)
    return "".join(lines)


def refactor_file(path: Path) -> int:
    if path.name in SKIP:
        return 0
    text = path.read_text(encoding="utf-8")
    if "unsafe_allow_html=True" not in text:
        return 0
    new_text, count = MARKDOWN_UNSAFE.subn(r"render_safe_html(\1)", text)
    if count == 0:
        return 0
    new_text = new_text.replace("from ui.html_render import render_html\n", IMPORT)
    new_text = new_text.replace("render_html(", "render_safe_html(")
    new_text = _insert_import(new_text)
    path.write_text(new_text, encoding="utf-8")
    return count


def main() -> None:
    total = 0
    for path in sorted(UI_DIR.rglob("*.py")):
        n = refactor_file(path)
        if n:
            print(f"{path.relative_to(ROOT)}: {n}")
            total += n
    print(f"Total replacements: {total}")


if __name__ == "__main__":
    main()
