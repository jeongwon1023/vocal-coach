"""채팅 스레드 · 스트리밍 중 자동 스크롤."""

from __future__ import annotations

import streamlit.components.v1 as components

_THREAD_SELECTOR = ".st-key-vc_dm_thread"


def scroll_chat_to_bottom(*, selector: str = _THREAD_SELECTOR) -> None:
    """채팅 스레드 하단으로 즉시 스크롤."""
    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            function getThread() {{
                return doc.querySelector("{selector}");
            }}
            function scrollThread() {{
                const thread = getThread();
                if (!thread) return;
                thread.scrollTop = thread.scrollHeight;
            }}
            scrollThread();
            requestAnimationFrame(scrollThread);
            setTimeout(scrollThread, 80);
            setTimeout(scrollThread, 250);
            setTimeout(scrollThread, 600);
        }})();
        </script>
        """,
        height=0,
    )


def install_chat_auto_scroll(*, selector: str = _THREAD_SELECTOR) -> None:
    """MutationObserver + 주기적 스크롤 — 스트리밍 타이핑 중 하단 추적."""
    components.html(
        f"""
        <script>
        (function () {{
            const win = window.parent;
            const doc = win.document;
            if (win.__vcCoachScrollReady) return;
            win.__vcCoachScrollReady = true;

            const SEL = "{selector}";

            function getThread() {{
                return doc.querySelector(SEL);
            }}

            function scrollThread() {{
                const thread = getThread();
                if (!thread) return;
                thread.scrollTop = thread.scrollHeight;
            }}

            function bindThread(thread) {{
                if (!thread || thread.dataset.vcScrollBound === "1") return;
                thread.dataset.vcScrollBound = "1";
                scrollThread();
                new MutationObserver(function () {{
                    scrollThread();
                }}).observe(thread, {{
                    childList: true,
                    subtree: true,
                    characterData: true,
                }});
            }}

            function scan() {{
                bindThread(getThread());
                scrollThread();
            }}

            scan();
            new MutationObserver(scan).observe(doc.body, {{
                childList: true,
                subtree: true,
            }});
            win.__vcCoachScrollTimer = win.setInterval(scrollThread, 350);
        }})();
        </script>
        """,
        height=0,
    )
