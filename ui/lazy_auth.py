"""Duolingo 스타일 Lazy Auth — 선 체험 · 결과 잠금."""

from __future__ import annotations

import uuid

import streamlit as st

from ui.utils import render_safe_html


def is_premium_unlocked() -> bool:
    """로그인(카카오·체험·Google) 완료 시 전체 결과 해제."""
    from ui.auth import is_logged_in

    return is_logged_in()


def ensure_anonymous_analysis_id() -> str:
    """비로그인 분석용 임시 ID."""
    if "anon_analysis_id" not in st.session_state:
        st.session_state.anon_analysis_id = f"anon_{uuid.uuid4().hex[:10]}"
    return st.session_state.anon_analysis_id


def resolve_analysis_user_id() -> str | None:
    from ui.auth import current_user_id, is_logged_in

    if is_logged_in():
        return current_user_id()
    return ensure_anonymous_analysis_id()


def mark_analysis_completed() -> None:
    st.session_state["analysis_completed_guest"] = True


def should_show_premium_lock() -> bool:
    return bool(st.session_state.get("analysis_completed_guest")) and not is_premium_unlocked()


@st.dialog("🔒 내 보컬 분석 리포트를 평생 소장하려면?", width="small")
def _unlock_results_dialog() -> None:
    from ui.auth import (
        _render_kakao_login_button,
        _render_supabase_kakao_styles,
        kakao_login_available,
        start_demo,
    )

    st.markdown(
        "지금까지의 **음정·박자·Vocal MBTI**는 확인하셨어요.\n\n"
        "**AI 상세 코칭 · 성장 그래프 · 기록 저장**은 로그인 후 이용할 수 있습니다."
    )
    if kakao_login_available():
        _render_supabase_kakao_styles()
        _render_kakao_login_button(key="unlock_dialog_kakao")
    st.caption("또는")
    if st.button("✦ 체험 계정으로 전체 보기 (3초)", use_container_width=True, type="primary"):
        start_demo()
        st.session_state.pop("analysis_completed_guest", None)
        st.rerun()


def open_unlock_dialog() -> None:
    _unlock_results_dialog()


def render_premium_lock_cta() -> None:
    """Tinder-style blur 위 CTA."""
    render_safe_html(
        """
        <div class="vc-premium-lock-card">
            <p class="vc-premium-lock-emoji">🔒</p>
            <p class="vc-premium-lock-title">AI 상세 코칭 &amp; 성장 그래프</p>
            <p class="vc-premium-lock-sub">로그인하면 전체 리포트와 DM 코치를 바로 이용할 수 있어요</p>
        </div>
        """
    )
    if st.button(
        "3초 만에 전체 결과 보기",
        type="primary",
        use_container_width=True,
        key="btn_unlock_premium",
    ):
        open_unlock_dialog()


def render_blurred_preview() -> None:
    """블러 처리된 프리뷰 (실제 콘텐츠 대신)."""
    render_safe_html(
        """
        <div class="vc-blur-preview" aria-hidden="true">
            <p>🎤 AI 코치: 고음 구간에서 목을 쥐어짜고 있어요! 턱을 당기고...</p>
            <p>📈 성장 그래프 · 주간 요약 · 맞춤 10분 루틴</p>
            <p>🎹 노트 히트맵 · 구간별 드릴다운 · PDF 리포트</p>
        </div>
        """
    )
