"""채팅 스레드 · 입력창 자동 스크롤."""

from __future__ import annotations

import streamlit.components.v1 as components


def scroll_chat_to_bottom(*, selector: str = ".st-key-vc_dm_thread") -> None:
    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            function scrollThread() {{
                const thread = doc.querySelector("{selector}");
                if (!thread) return;
                const blocks = thread.querySelectorAll('[data-testid="stVerticalBlock"]');
                const scrollHost = blocks.length ? blocks[blocks.length - 1] : thread;
                scrollHost.scrollTop = scrollHost.scrollHeight;
                const msgs = thread.querySelectorAll('[data-testid="stChatMessage"]');
                const last = msgs.length ? msgs[msgs.length - 1] : null;
                if (last) {{
                    last.scrollIntoView({{ block: "end", behavior: "smooth" }});
                }}
            }}
            scrollThread();
            setTimeout(scrollThread, 60);
            setTimeout(scrollThread, 200);
            setTimeout(scrollThread, 450);
        }})();
        </script>
        """,
        height=0,
    )
