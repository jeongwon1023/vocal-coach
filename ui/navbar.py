"""상단 네비게이션 — 클릭 가능한 브랜드 · 세그먼트 · 로그인."""

from __future__ import annotations

import streamlit as st

from ui.navigation import PAGES, current_page, go_to, init_nav


def render_navbar() -> str:
    """상단 바 렌더. 현재 페이지 반환."""
    from ui import auth

    init_nav()
    current = current_page()

    st.markdown('<div class="vc-nav-anchor"></div>', unsafe_allow_html=True)

    c_brand, c_nav, c_auth = st.columns([2.3, 4.8, 2.3], vertical_alignment="center")

    with c_brand:
        if st.button(
            "🎤 VOCAL COACH AI",
            key="nav_brand_home",
            help="홈으로 이동",
            type="tertiary",
            use_container_width=True,
        ):
            go_to("홈")

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
