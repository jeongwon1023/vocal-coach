"""페이지 이동 — 세그먼트 네비와 session_state 동기화."""

from __future__ import annotations

import streamlit as st

PAGES = ("홈", "분석", "마이 페이지", "피드백")


def init_nav() -> None:
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "홈"
    if st.session_state.nav_page not in PAGES:
        st.session_state.nav_page = "홈"
    if st.session_state.get("nav_segment") != st.session_state.nav_page:
        st.session_state.nav_segment = st.session_state.nav_page


def go_to(page: str) -> None:
    """CTA·링크에서 페이지 이동."""
    if page not in PAGES:
        return
    st.session_state.nav_page = page
    st.rerun()


def current_page() -> str:
    page = st.session_state.get("nav_page", "홈")
    return page if page in PAGES else "홈"
