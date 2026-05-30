"""하위 호환 — render_safe_html 별칭."""

from __future__ import annotations

from ui.utils import render_safe_html

render_html = render_safe_html

__all__ = ["render_html", "render_safe_html"]
