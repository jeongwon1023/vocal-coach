"""상단 네비 — 고정 헤더 · 로고 · 로그인 · ☰ 메뉴."""

from __future__ import annotations

import streamlit as st

from ui.utils import render_safe_html
from ui.navigation import NAV_PAGES, PAGE_ICONS, PAGE_LABELS, current_page, go_to, init_nav


def _nav_page_button(page: str, *, key: str) -> None:
    icon = PAGE_ICONS.get(page, "")
    label = PAGE_LABELS.get(page, page)
    active = page == current_page()
    if st.button(
        f"{icon} {label}",
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary"
    ):
        if page != current_page():
            st.session_state.nav_page = page
            st.rerun()


def render_navbar() -> str:
    from ui import auth

    init_nav()

    render_safe_html(
        """\
<div class="vc-navbar-marker"></div>
<div class="vc-mobile-header-bar" aria-hidden="true">
<span class="vc-mobile-header-logo">🎤 Vocal Coach</span>
</div>"""
    )

    c_brand, c_auth, c_menu = st.columns([2.4, 2.6, 0.55], gap="small", vertical_alignment="center")

    with c_brand:
        if st.button(
            "🎤 Vocal Coach",
            key="nav_brand_home",
            help="Vocal Coach AI · 홈",
            type="tertiary",
            use_container_width=False
        ):
            go_to("홈")

    with c_auth:
        auth.render_topbar_auth()

    with c_menu:
        with st.popover("☰", use_container_width=False, help="메뉴", key="nav_menu"):
            render_safe_html('<p class="vc-nav-menu-title">메뉴</p>'
            )
            for page in NAV_PAGES:
                _nav_page_button(page, key=f"nav_menu_btn_{page}")

            st.divider()
            auth.render_menu_auth(key_prefix="nav_menu_auth")

            if st.button("💬 피드백", key="nav_menu_feedback", use_container_width=True):
                go_to("피드백")

    st.markdown('<div class="vc-header-divider"></div>')
    return current_page()
