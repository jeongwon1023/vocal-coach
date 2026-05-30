#!/usr/bin/env python3
"""st.markdown(HTML...) -> render_safe_html(...) — unsafe_allow_html 누락 일괄 수정."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPORT = "from ui.utils import render_safe_html\n"
HTML_TAG = re.compile(r"<\s*[a-zA-Z/!]")
HTML_FUNCS = frozenset(
    {
        "landing_scroll_script",
        "format_coach_rich_html",
        "youtube_guide_help_md",
        "teacher_philosophy_md",
    }
)


def _find_call_end(text: str, paren_start: int) -> int:
    depth = 1
    i = paren_start
    in_string: str | None = None
    escape = False
    while i < len(text) and depth > 0:
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif in_string in ('"""', "'''") and text[i : i + 3] == in_string:
                in_string = None
                i += 3
                continue
            elif in_string in ('"', "'") and c == in_string:
                in_string = None
            i += 1
            continue
        if text[i : i + 3] in ('"""', "'''"):
            in_string = text[i : i + 3]
            i += 3
            continue
        if c in ('"', "'"):
            in_string = c
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    return i


def _needs_safe_html(arg: str) -> bool:
    arg = arg.strip()
    if not arg:
        return False
    if HTML_TAG.search(arg):
        return True
    for fn in HTML_FUNCS:
        if re.search(rf"\b{fn}\s*\(", arg):
            return True
    if re.fullmatch(r"html_out", arg):
        return True
    return False


def _ensure_import(text: str) -> str:
    if "from ui.utils import render_safe_html" in text:
        return text
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import streamlit") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, IMPORT)
    return "".join(lines)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "st.markdown" not in text:
        return False

    out: list[str] = []
    i = 0
    changed = False
    while i < len(text):
        m = re.search(r"\bst\.markdown\s*\(", text[i:])
        if not m:
            out.append(text[i:])
            break
        start = i + m.start()
        out.append(text[i:start])
        paren_start = i + m.end()
        end = _find_call_end(text, paren_start)
        arg = text[paren_start : end - 1]
        if _needs_safe_html(arg):
            out.append("render_safe_html(" + arg + ")")
            changed = True
        else:
            out.append(text[start:end])
        i = end

    if not changed:
        return False

    new_text = "".join(out)
    new_text = _ensure_import(new_text)
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    targets = list((ROOT / "ui").glob("*.py"))
    targets += [ROOT / "app.py"]
    fixed = []
    for path in sorted(targets):
        if process_file(path):
            fixed.append(path.relative_to(ROOT))
    print(f"Fixed {len(fixed)} files:")
    for p in fixed:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
