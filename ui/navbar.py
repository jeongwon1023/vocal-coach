"""상단 네비 — 버튼 방식 (모바일 클릭 안정)."""

from __future__ import annotations

import streamlit as st

from ui.navigation import PAGES, PAGE_LABELS, current_page, go_to, init_nav


def render_navbar() -> str:
    from ui import auth

    init_nav()
    current = current_page()

    st.markdown('<div class="vc-navbar-marker"></div>', unsafe_allow_html=True)

    c_brand, c_nav, c_auth = st.columns([2.2, 5.0, 2.2], vertical_alignment="center")

    with c_brand:
        if st.button(
            "🎤 VOCAL COACH AI",
            key="nav_brand_home",
            help="홈으로",
            type="tertiary",
            use_container_width=True,
        ):
            go_to("홈")

    with c_nav:
        nav_cols = st.columns(len(PAGES))
        for col, page in zip(nav_cols, PAGES):
            label = PAGE_LABELS.get(page, page)
            with col:
                active = page == current
                if st.button(
                    label,
                    key=f"nav_btn_{page}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    if page != current:
                        st.session_state.nav_page = page
                        st.rerun()

    with c_auth:
        auth.render_topbar_auth()

    st.markdown('<div class="vc-header-divider"></div>', unsafe_allow_html=True)
    return current_page()
