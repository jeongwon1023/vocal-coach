"""채팅 스레드 스크롤 — 새 메시지·스트리밍 시에만 하단 추적 (수동 스크롤 존중)."""

from __future__ import annotations

import streamlit.components.v1 as components

_THREAD_SELECTOR = ".st-key-vc_dm_thread"

_SCROLL_BOOTSTRAP = """
(function () {
    const win = window.parent;
    const doc = win.document;
    if (win.__vcCoachScrollV2) return;
    win.__vcCoachScrollV2 = true;

    const SEL = "__SEL__";
    const THRESHOLD = 96;

    function getThread() {
        return doc.querySelector(SEL);
    }

    function nearBottom(thread) {
        return thread.scrollHeight - thread.scrollTop - thread.clientHeight <= THRESHOLD;
    }

    function scrollBottom(thread, force) {
        if (!thread) return;
        if (force || thread.dataset.vcPinned !== "0") {
            thread.scrollTop = thread.scrollHeight;
        }
    }

    function bindThread(thread) {
        if (!thread || thread.dataset.vcScrollBound === "1") return;
        thread.dataset.vcScrollBound = "1";
        thread.dataset.vcPinned = "1";

        thread.addEventListener(
            "scroll",
            function () {
                thread.dataset.vcPinned = nearBottom(thread) ? "1" : "0";
            },
            { passive: true }
        );

        scrollBottom(thread, true);

        new MutationObserver(function () {
            if (thread.dataset.vcPinned !== "0") {
                scrollBottom(thread, false);
            }
        }).observe(thread, {
            childList: true,
            subtree: true,
            characterData: true,
        });
    }

    function scan() {
        bindThread(getThread());
    }

    scan();
    new MutationObserver(scan).observe(doc.body, { childList: true, subtree: true });
})();
"""


def install_chat_auto_scroll(*, selector: str = _THREAD_SELECTOR) -> None:
    """유저가 위로 스크롤 중이면 고정 — 하단 근처일 때만 자동 추적."""
    js = _SCROLL_BOOTSTRAP.replace("__SEL__", selector)
    components.html(f"<script>{js}</script>", height=0)


def scroll_chat_to_bottom(*, selector: str = _THREAD_SELECTOR, force: bool = True) -> None:
    """새 메시지·스트리밍 완료 시 1회 하단 스크롤."""
    force_js = "true" if force else "false"
    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            const thread = doc.querySelector("{selector}");
            if (!thread) return;
            thread.dataset.vcPinned = "1";
            function go() {{ thread.scrollTop = thread.scrollHeight; }}
            if ({force_js}) {{
                go();
                requestAnimationFrame(go);
                setTimeout(go, 120);
            }}
        }})();
        </script>
        """,
        height=0
    )
