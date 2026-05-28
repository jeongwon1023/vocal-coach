"""베타 서비스 UI · 배너."""

from __future__ import annotations

import streamlit as st

BETA_VERSION = "0.9.0-beta"
BETA_SHARE_URL = "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/"


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


def render_beta_invite_card() -> None:
    """베타 초대 — 링크 공유 CTA."""
    st.markdown(
        f"""
        <div class="vc-beta-invite">
            <p class="vc-beta-invite-title">🎤 베타 테스터 모집</p>
            <p class="vc-beta-invite-body">
                친구에게 Vocal Coach AI를 소개해 주세요.<br>
                MR 녹음 vs 보컬-only 비교 피드백이 특히 도움이 됩니다.
            </p>
            <p class="vc-beta-invite-url">{BETA_SHARE_URL}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(BETA_SHARE_URL, language=None)
