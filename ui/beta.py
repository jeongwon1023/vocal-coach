"""베타 서비스 UI · 배너."""

from __future__ import annotations

import streamlit as st

BETA_VERSION = "0.9.0-beta"


def render_beta_banner() -> None:
    st.markdown(
        f"""
        <div class="vc-beta-banner">
            <span class="vc-beta-tag">BETA {BETA_VERSION}</span>
            <span class="vc-beta-text">베타 테스트 중 · 피드백은 ☰ 메뉴</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
