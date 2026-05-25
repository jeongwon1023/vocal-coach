"""페이지 이동 — 버튼 네비 · session_state."""

from __future__ import annotations

import streamlit as st

PAGES = ("홈", "마이 페이지", "피드백")
PAGE_LABELS = {"홈": "홈", "마이 페이지": "마이", "피드백": "피드백"}
_LEGACY = {"분석": "마이 페이지"}


def init_nav() -> None:
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "홈"
    legacy = st.session_state.nav_page
    if legacy in _LEGACY:
        st.session_state.nav_page = _LEGACY[legacy]
    if st.session_state.nav_page not in PAGES:
        st.session_state.nav_page = "홈"


def go_to(page: str) -> None:
    if page in _LEGACY:
        page = _LEGACY[page]
    if page not in PAGES:
        return
    st.session_state.nav_page = page
    st.rerun()


def current_page() -> str:
    page = st.session_state.get("nav_page", "홈")
    if page in _LEGACY:
        return _LEGACY[page]
    return page if page in PAGES else "홈"
