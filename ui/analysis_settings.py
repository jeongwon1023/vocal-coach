"""분석 페이지 설정 UI — 다이얼로그 / 공통 위젯."""

from __future__ import annotations

import streamlit as st

from ui import styles
from ui.runtime_env import default_use_queue


def render_analysis_settings() -> None:
    from style_presets import PRESETS
    from ui.help_guide import render_song_title_help, render_youtube_guide_sidebar

    st.markdown(
        '<p class="vc-sidebar-title">옵션</p>',
        unsafe_allow_html=True,
    )
    styles.sidebar_label("분석 모드")
    st.checkbox(
        "빠른 분석 (권장)",
        key="fast_mode",
        value=True,
        help=(
            "빠른: 16kHz·2분·약 1분. "
            "정밀(체크 해제): 22kHz·전체·강화 보컬 분리·노트 단위 채점·jitter/HNR (2~3분). "
            "로컬에서 CREPE/Demucs는 requirements-precision.txt 참고."
        ),
    )
    st.divider()
    styles.sidebar_label("유튜브 가이드")
    render_song_title_help()
    st.text_input(
        "곡 제목",
        key="song_title",
        placeholder="예: 아이유 밤편지, NewJeans Ditto",
    )
    st.checkbox(
        "유튜브 가이드 사용",
        key="use_youtube",
        value=False,
        help="켜면 곡 제목으로 MR·가이드 멜로디를 찾아 원곡과 비교합니다.",
    )
    render_youtube_guide_sidebar()
    st.divider()
    styles.sidebar_label("기타 옵션")
    st.selectbox(
        "가창 스타일",
        options=list(PRESETS.keys()),
        format_func=lambda k: PRESETS[k].label,
        key="style_preset",
    )
    st.checkbox("GPT 코칭", key="use_gpt", value=False)
    st.checkbox("기록 저장", key="save_record", value=True)
    st.checkbox("이전 기록 비교", key="compare", value=True)
    st.divider()
    styles.sidebar_label("고급")
    st.checkbox("문제 구간 클립", key="export_clips", value=False)
    st.checkbox("성장 그래프", key="growth_chart", value=False)
    st.checkbox("백그라운드 분석 큐", key="use_queue", value=default_use_queue())
    st.divider()
    st.markdown(
        "<div class='tip-box' style='font-size:0.82rem;'>"
        "🎧 MR은 이어폰 · 마이크엔 목소리만</div>",
        unsafe_allow_html=True,
    )


@st.dialog("⚙️ 분석 설정", width="large")
def open_analysis_settings_dialog() -> None:
    st.caption("빠른/정밀 · 유튜브 · GPT 등")
    render_analysis_settings()
    if st.button("완료", type="primary", use_container_width=True, key="btn_settings_done"):
        st.rerun()


def render_settings_open_button(*, key: str = "btn_open_analysis_settings") -> None:
    if st.button(
        "⚙️ 분석 설정",
        key=key,
        use_container_width=True,
        help="정밀 분석 · 유튜브 · GPT 등",
    ):
        open_analysis_settings_dialog()


def render_analysis_settings_expander(*, expanded: bool = True) -> None:
    """인라인 분석 설정 — 기본 펼침."""
    with st.expander("⚙️ 분석 설정", expanded=expanded):
        render_analysis_settings()
