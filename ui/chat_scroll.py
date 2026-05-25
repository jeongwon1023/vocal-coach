"""채팅 스레드 · 입력창 자동 스크롤."""

from __future__ import annotations

import streamlit.components.v1 as components


def scroll_chat_to_bottom(*, selector: str = ".st-key-vc_dm_thread") -> None:
    components.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            function scrollThread() {{
                const el = doc.querySelector("{selector}");
                if (el) el.scrollTop = el.scrollHeight;
                const panel = doc.querySelector(".st-key-vc_dm_panel");
                if (panel) panel.scrollIntoView({{ block: "end", behavior: "smooth" }});
            }}
            scrollThread();
            setTimeout(scrollThread, 80);
            setTimeout(scrollThread, 250);
        }})();
        </script>
        """,
        height=0,
    )
