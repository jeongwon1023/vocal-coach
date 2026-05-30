"""도움말 패널 — 유튜브 가이드·곡 제목 안내."""

from __future__ import annotations

import streamlit as st

from teacher_voice import teacher_philosophy_md, youtube_guide_help_md
from ui.utils import render_safe_html


def render_song_title_help() -> None:
    """곡 제목 입력 — 왜 쓰는지, 어떻게 쓰는지 (사이드바)."""
    render_safe_html(
        """
        <div class="vc-guide-box">
            <p class="vc-guide-title">🎵 곡 제목은 왜 입력하나요?</p>
            <p class="vc-guide-body">
            원곡 MR·가이드 보컬과 <b>비교 레슨</b>을 하려면 어떤 곡인지 알아야 해요.
            선생님이 수업 전에 MR을 틀어 주는 것과 같습니다.
            </p>
            <p class="vc-guide-steps"><b>사용법</b></p>
            <ol class="vc-guide-list">
                <li>곡 제목 입력 <span class="vc-guide-ex">예: 아이유 밤편지</span></li>
                <li>아래 <b>「유튜브 가이드」</b> 켜기</li>
                <li>녹음 업로드 후 분석 시작</li>
            </ol>
            <p class="vc-guide-note">💡 가이드 없이도 분석 가능 · 커버·원곡 비교할 때만 켜세요</p>
        </div>
        """
    )


def render_youtube_guide_sidebar() -> None:
    """사이드바 — 상세 유튜브 가이드."""
    with st.expander("📖 유튜브 가이드 자세히 보기", expanded=False):
        render_safe_html(youtube_guide_help_md())


def render_youtube_guide_inline() -> None:
    """대시보드 업로드 영역 아래."""
    with st.expander("💡 유튜브 가이드 · 선생님은 이렇게 들어요", expanded=False):
        render_safe_html(youtube_guide_help_md())
        st.divider()
        render_safe_html(teacher_philosophy_md())


def render_compact_tip() -> None:
    st.caption(
        "유튜브 가이드 = 원곡 MR·가이드 멜로디로 **비교 레슨**. "
        "곡 제목 입력 후 켜 주세요."
    )
