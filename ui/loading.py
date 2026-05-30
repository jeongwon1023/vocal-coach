"""전역 로딩 — 분석·페이지 전환 시에만 (채팅 타이핑과 분리)."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

_HIDE_LOADING_JS = """
<script>
(function () {
    const doc = window.parent.document;
    if (doc.body) doc.body.classList.remove("vc-loading");
    const el = doc.getElementById("vc-loading-banner");
    if (el) el.remove();
})();
</script>
"""


def mark_loading(*, message: str = "잠시만요…") -> None:
    st.session_state["vc_loading"] = True
    st.session_state["vc_loading_msg"] = message


def clear_loading() -> None:
    st.session_state.pop("vc_loading", None)
    st.session_state.pop("vc_loading_msg", None)
    _hide_loading_dom()


def is_loading() -> bool:
    return bool(st.session_state.get("vc_loading"))


def _hide_loading_dom() -> None:
    components.html(_HIDE_LOADING_JS, height=0)


def render_loading_overlay() -> None:
    """vc_loading 플래그가 있을 때만 하단 배너 표시."""
    if not is_loading():
        _hide_loading_dom()
        return

    msg = (st.session_state.get("vc_loading_msg") or "잠시만요…").replace("\\", "\\\\").replace("'", "\\'")
    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            if (doc.body) doc.body.classList.add("vc-loading");
            let el = doc.getElementById("vc-loading-banner");
            if (!el) {{
                el = doc.createElement("div");
                el.id = "vc-loading-banner";
                el.className = "vc-loading-banner";
                doc.body.appendChild(el);
            }}
            el.innerHTML = '<span class="vc-loading-spinner"></span><span>{msg}</span>';
        }})();
        </script>
        """,
        height=0
    )
