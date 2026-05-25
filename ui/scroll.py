"""페이지 스크롤 — 분석 시작 시 상단으로."""

from __future__ import annotations

import streamlit.components.v1 as components


def scroll_analyze_panel(*, anchor_id: str = "vc-analyzing-anchor") -> None:
    """분석 배너를 상단으로 — 스크롤 내려가 있어도 올림."""
    scroll_to_top(anchor_id=anchor_id)


def scroll_to_top(*, anchor_id: str = "vc-analyzing-anchor") -> None:
    """분석 배너·상단으로 스크롤 (iframe·모바일 대응)."""
    components.html(
        f"""
        <script>
        (function() {{
            const w = window.parent;
            const doc = w.document;
            function doScroll() {{
                const anchor = doc.getElementById("{anchor_id}");
                const main = doc.querySelector("section.main")
                    || doc.querySelector('[data-testid="stMain"]')
                    || doc.querySelector('[data-testid="stAppViewContainer"]');
                if (main) main.scrollTop = 0;
                doc.documentElement.scrollTop = 0;
                doc.body.scrollTop = 0;
                w.scrollTo(0, 0);
                if (anchor) {{
                    anchor.scrollIntoView({{ behavior: "smooth", block: "start" }});
                }} else if (main) {{
                    main.scrollTo({{ top: 0, behavior: "smooth" }});
                }} else {{
                    w.scrollTo({{ top: 0, behavior: "smooth" }});
                }}
            }}
            doScroll();
            setTimeout(doScroll, 120);
            setTimeout(doScroll, 400);
        }})();
        </script>
        """,
        height=0,
    )


def scroll_to_anchor(anchor_id: str = "vc-analyzing-anchor") -> None:
    scroll_to_top(anchor_id=anchor_id)
