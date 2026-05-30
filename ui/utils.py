"""UI 공통 유틸 — 방탄 HTML 렌더."""

from __future__ import annotations

import textwrap

import streamlit as st


def render_safe_html(html_str: str) -> None:
    """
    HTML 문자열을 Streamlit에 안전하게 렌더.

    - textwrap.dedent + strip 으로 파이썬 들여쓰기 제거 (코드블록/HTML 노출 방지)
    - unsafe_allow_html=True 로 실제 DOM 렌더
    """
    clean_html = textwrap.dedent(html_str).strip()
    if not clean_html:
        return
    st.markdown(clean_html, unsafe_allow_html=True)
