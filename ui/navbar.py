"""상단 네비 — 브랜드 + ☰ 메뉴 (홈·마이·계정·피드백)."""

from __future__ import annotations

import streamlit as st

from ui.navigation import NAV_PAGES, PAGE_ICONS, PAGE_LABELS, current_page, go_to, init_nav


def _nav_page_button(page: str, *, key: str) -> None:
    icon = PAGE_ICONS.get(page, "")
    label = PAGE_LABELS.get(page, page)
    active = page == current_page()
    if st.button(
        f"{icon} {label}",
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        if page != current_page():
            st.session_state.nav_page = page
            st.rerun()


def render_navbar() -> str:
    from ui import auth

    init_nav()

    st.markdown('<div class="vc-navbar-marker"></div>', unsafe_allow_html=True)

    c_brand, c_auth, c_menu = st.columns([4.2, 1.8, 1], vertical_alignment="center")

    with c_brand:
        if st.button(
            "🎤 Vocal Coach",
            key="nav_brand_home",
            help="Vocal Coach AI · 홈",
            type="tertiary",
            use_container_width=True,
        ):
            go_to("홈")

    with c_auth:
        auth.render_topbar_auth()

    with c_menu:
        with st.popover("☰", use_container_width=True, help="메뉴", key="nav_menu"):
            st.markdown(
                '<p class="vc-nav-menu-title">메뉴</p>',
                unsafe_allow_html=True,
            )
            for page in NAV_PAGES:
                _nav_page_button(page, key=f"nav_menu_btn_{page}")

            st.divider()
            auth.render_menu_auth(key_prefix="nav_menu_auth")

            if st.button("💬 피드백", key="nav_menu_feedback", use_container_width=True):
                go_to("피드백")

    st.markdown('<div class="vc-header-divider"></div>', unsafe_allow_html=True)
    return current_page()
