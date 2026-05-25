"""페이지 이동 — 세그먼트 네비와 session_state 동기화."""

from __future__ import annotations

import streamlit as st

PAGES = ("홈", "분석", "마이 페이지")


def init_nav() -> None:
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "홈"
    if st.session_state.get("nav_segment") != st.session_state.nav_page:
        st.session_state.nav_segment = st.session_state.nav_page


def go_to(page: str) -> None:
    """CTA·링크에서 페이지 이동.

    nav_segment는 위젯 키라 렌더 후 수정 불가 → nav_page만 바꾸고
    다음 run 시작 시 init_nav()가 세그먼트와 동기화합니다.
    """
    if page not in PAGES:
        return
    st.session_state.nav_page = page
    st.rerun()


def current_page() -> str:
    return st.session_state.get("nav_page", "홈")
