"""분석 중 화면 — 패널 포커스 (깜빡임·잔여 어둡기 없음)."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def open_analyze_stage() -> None:
    """분석 전용 스테이지 — #vc-analyzing-anchor 가 있을 때만 CSS로 어둡게."""
    st.markdown('<div class="vc-analyze-stage" id="vc-analyzing-anchor">', unsafe_allow_html=True)


def close_analyze_stage() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def clear_analyze_stage() -> None:
    """분석 종료 후 남은 전역 어둡기·sessionStorage 정리."""
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            if (doc.body) doc.body.classList.remove("vc-analyzing");
            try { sessionStorage.removeItem("vc_analyzing"); } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )


def render_cancel_button(*, key: str = "btn_cancel_analysis") -> bool:
    return bool(
        st.button(
            "취소",
            key=key,
            type="secondary",
            use_container_width=True,
            help="분석을 중단합니다",
        )
    )
