"""SaaS 대시보드 — 상단 GNB (PayLink 스타일)."""

from __future__ import annotations

import html

import streamlit as st

from ui.auth import current_user, is_logged_in, logout, open_login_dialog
from ui.utils import render_safe_html


def render_dashboard_gnb() -> None:
    """최상단 GNB — 서비스명(좌) · 프로필+로그아웃(우)만."""
    render_safe_html('<div class="vc-dash-gnb-marker" aria-hidden="true"></div>')

    left, right = st.columns([2.2, 1.8], gap="small", vertical_alignment="center")

    with left:
        st.markdown("### 🎤 Vocal Coach AI")

    with right:
        user = current_user()
        if user and is_logged_in():
            name = html.escape(str(user.get("name") or "보컬러"))
            avatar = user.get("avatar_url")
            prof_col, logout_col = st.columns([1.4, 1], gap="small", vertical_alignment="center")
            with prof_col:
                if avatar:
                    st.image(str(avatar), width=36)
                st.markdown(f"**{name}**")
            with logout_col:
                if st.button("로그아웃", key="dash_gnb_logout", type="secondary", use_container_width=True):
                    logout()
        else:
            if st.button("로그인", key="dash_gnb_login", type="primary", use_container_width=True):
                open_login_dialog(key_prefix="dash_gnb_login_dialog")

    render_safe_html('<div class="vc-dash-gnb-divider"></div>')
