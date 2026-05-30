"""세션 상태 초기화 — dashboard/coach_chat 순환 import 방지."""

from __future__ import annotations

import streamlit as st


def clear_results_state() -> None:
    for key in (
        "last_session",
        "last_log",
        "coach_chat_fp",
        "coach_chat_messages",
        "coach_suggested_questions",
        "coach_gpt_enhanced",
        "mypage_show_result",
        "coach_pending_message",
        "coach_used_suggestions",
        "coach_scroll_tick",
        "coach_opening_stream",
        "coach_opening_inflight",
        "coach_stream_completed_id",
        "coach_stream_inflight_id",
        "coach_gpt_suggestions_done",
        "coach_chat_ready",
        "force_precision",
        "upload_mr_likely",
        "_upload_file_sig",
        "scroll_result",
        "scroll_analyze",
        "scroll_analyze_ticks"
    ):
        st.session_state.pop(key, None)


def clear_analysis_session_keys() -> None:
    for key in (
        "pending_job_id",
        "sync_audio_path",
        "analysis_started_at",
        "analysis_mode_fast",
        "analysis_use_gpt",
        "analysis_cancelled"
    ):
        st.session_state.pop(key, None)


def reset_user_session_state() -> None:
    """로그아웃 · 새 분석 — UI·결과·분석 플래그 초기화."""
    clear_results_state()
    clear_analysis_session_keys()
    from ui.loading import clear_loading

    clear_loading()
