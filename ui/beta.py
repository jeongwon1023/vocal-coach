"""베타 서비스 UI · 배너."""

from __future__ import annotations

import streamlit as st

BETA_VERSION = "0.9.0-beta"


def render_beta_banner() -> None:
    st.markdown(
        f"""
        <div class="vc-beta-banner">
            <span class="vc-beta-tag">BETA {BETA_VERSION}</span>
            <span class="vc-beta-text">베타 테스트 중 · 피드백 환영 · 일부 기능은 개선 중이에요</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_beta_footer() -> None:
    with st.expander("ℹ️ 베타 안내 · 이용약관 요약"):
        st.markdown(
            """
            **Vocal Coach AI 베타**
            - 분석 결과는 **참고용**이며 전문 의료·법률 자문이 아닙니다.
            - 녹음·분석 데이터는 서비스 제공 목적으로만 사용됩니다.
            - 버그·불편 사항은 우측 상단 메뉴 또는 개발자에게 알려 주세요.
            - 베타 기간 동안 **체험 계정**으로 모든 기능을 써볼 수 있습니다.
            """
        )
