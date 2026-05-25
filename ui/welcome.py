"""First-time onboarding — feature grid."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown(
        """
        <div class="vc-feature-grid">
            <div class="vc-feature">
                <div class="vc-feature-icon">🎵</div>
                <h3>음정 분석</h3>
                <p>가이드 멜로디와 비교해 틀린 구간을 초 단위로 표시합니다.</p>
            </div>
            <div class="vc-feature">
                <div class="vc-feature-icon">⏱️</div>
                <h3>박자 · 리듬</h3>
                <p>소리 내는 타이밍 패턴을 분석해 박자 안정성을 점수화합니다.</p>
            </div>
            <div class="vc-feature">
                <div class="vc-feature-icon">🎬</div>
                <h3>유튜브 가이드</h3>
                <p>곡 제목만 입력하면 MR·가이드 멜로디로 <b>원곡 비교 레슨</b>을 받을 수 있어요.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    from ui.help_guide import render_youtube_guide_inline

    render_youtube_guide_inline()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="tip-box">
            <b>녹음 팁</b><br>
            MR은 이어폰으로 듣고, 마이크에는 <b>목소리만</b> 녹음하세요.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="vc-info-box">
            <b>빠른 분석</b> — 약 30초~1분<br>
            <b>정밀 분석</b> — 논문 지표 · 전체 곡 · 2~3분<br>
            <b>유튜브/MR</b> — 보컬 자동 추출 · 믹스 대응
            </div>
            """,
            unsafe_allow_html=True,
        )
