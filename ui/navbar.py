"""상단 네비게이션 — Yousician/Moises 스타일 글래스 헤더."""

from __future__ import annotations

import streamlit as st

from ui.navigation import PAGES, current_page, init_nav


def render_navbar() -> str:
    """상단 바 렌더. 현재 페이지 반환."""
    from ui import auth

    init_nav()
    current = current_page()

    st.markdown(
        """
        <div class="vc-header-shell">
            <div class="vc-header-glow"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_brand, c_nav, c_auth = st.columns([2.4, 4.2, 2.4], vertical_alignment="center")

    with c_brand:
        st.markdown(
            """
            <div class="vc-header-brand">
                <span class="vc-header-logo">🎤</span>
                <div class="vc-header-titles">
                    <span class="vc-header-name">VOCAL COACH AI</span>
                    <span class="vc-header-tag">AI 보컬 레슨실</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_nav:
        picked = st.segmented_control(
            "페이지",
            options=list(PAGES),
            key="nav_segment",
            label_visibility="collapsed",
            width="stretch",
        )
        if picked and picked != current:
            st.session_state.nav_page = picked
            st.rerun()

    with c_auth:
        auth.render_topbar_auth()

    st.markdown('<div class="vc-header-divider"></div>', unsafe_allow_html=True)

    return current_page()
