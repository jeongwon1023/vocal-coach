"""상단 네비 — 홈 · 마이 · 로그인 (피드백은 베타 배너)."""

from __future__ import annotations

import streamlit as st

from ui.navigation import NAV_PAGES, PAGE_ICONS, PAGE_LABELS, current_page, go_to, init_nav


def render_navbar() -> str:
    from ui import auth

    init_nav()
    current = current_page()

    st.markdown('<div class="vc-navbar-marker"></div>', unsafe_allow_html=True)

    c_brand, c_nav, c_auth = st.columns([2.2, 3.8, 2.5], vertical_alignment="center")

    with c_brand:
        if st.button(
            "🎤 Vocal Coach",
            key="nav_brand_home",
            help="Vocal Coach AI · 홈",
            type="tertiary",
            use_container_width=True,
        ):
            go_to("홈")

    with c_nav:
        st.markdown('<div class="vc-nav-track">', unsafe_allow_html=True)
        nav_cols = st.columns(len(NAV_PAGES))
        for col, page in zip(nav_cols, NAV_PAGES):
            icon = PAGE_ICONS.get(page, "")
            label = PAGE_LABELS.get(page, page)
            with col:
                active = page == current
                if st.button(
                    f"{icon} {label}",
                    key=f"nav_btn_{page}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    if page != current:
                        st.session_state.nav_page = page
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c_auth:
        auth.render_topbar_auth()

    st.markdown('<div class="vc-header-divider"></div>', unsafe_allow_html=True)
    return current_page()
