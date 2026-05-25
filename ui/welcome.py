"""First-time onboarding — feature grid."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown(
        """
        <p class="vc-welcome-lead">Vocal Coach AI가 이렇게 도와드려요</p>
        <div class="vc-feature-grid">
            <div class="vc-feature-card">
                <span class="vc-feature-icon">🎵</span>
                <div>
                    <p class="vc-feature-title">음정</p>
                    <p class="vc-feature-desc">가이드 멜로디와 비교해, 틀린 구간을 초 단위로 짚어 드려요.</p>
                </div>
            </div>
            <div class="vc-feature-card">
                <span class="vc-feature-icon">⏱️</span>
                <div>
                    <p class="vc-feature-title">박자 · 리듬</p>
                    <p class="vc-feature-desc">박이 밀리는 구간을 찾아, 연습할 타이밍을 알려 드려요.</p>
                </div>
            </div>
            <div class="vc-feature-card">
                <span class="vc-feature-icon">🎬</span>
                <div>
                    <p class="vc-feature-title">유튜브 가이드</p>
                    <p class="vc-feature-desc">곡 제목만 입력하면 MR·가이드 보컬과 내 목소리를 비교해요.</p>
                </div>
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
            <div class="vc-tip-soft">
                <p class="vc-tip-soft-title">🎧 녹음 팁</p>
                <p class="vc-tip-soft-body">MR은 이어폰으로 듣고, 마이크에는 <b>목소리만</b> 녹음하면 분석이 더 정확해요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="vc-tip-soft">
                <p class="vc-tip-soft-title">⚡ 분석 시간</p>
                <p class="vc-tip-soft-body">빠른 분석 약 1분 · 정밀 분석 2~3분 · 결과는 DM 코치로 바로 확인</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
