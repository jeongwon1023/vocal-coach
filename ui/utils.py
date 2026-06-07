"""UI 공통 유틸 — 방탄 HTML 렌더."""

from __future__ import annotations

import textwrap

import streamlit as st


def render_safe_html(html_str: str) -> None:
    """
    HTML 문자열을 Streamlit에 안전하게 렌더.

    - dedent 후 각 줄 앞 공백 제거 (Markdown 4-space → code block 방지)
    - unsafe_allow_html=True 로 실제 DOM 렌더
    """
    clean_html = textwrap.dedent(html_str).strip()
    if not clean_html:
        return
    # Markdown은 4칸 이상 들여쓴 줄을 <pre> 코드블록으로 렌더 → HTML 노출 버그
    lines = [line.strip() for line in clean_html.splitlines() if line.strip()]
    clean_html = "\n".join(lines)
    st.markdown(clean_html, unsafe_allow_html=True)
