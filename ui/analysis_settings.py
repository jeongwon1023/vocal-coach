"""분석 페이지 설정 UI — 다이얼로그 / 공통 위젯."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ui import styles
from ui.runtime_env import default_use_queue
from ui.utils import render_safe_html


def _render_popular_song_picker() -> None:
    from song_hints import all_song_hints, filter_song_hints, format_song_label, unique_genres

    total = len(all_song_hints())
    page_size = 48
    with st.expander(f"🎵 인기곡 빠른 선택 ({total}곡)", expanded=False):
        filter_q = st.text_input(
            "🔍 곡 검색",
            key="song_picker_q",
            placeholder="가수 · 곡명 · 별칭"
        )
        genres = ["전체", *unique_genres()]
        genre = st.selectbox("장르", genres, key="song_picker_genre")
        all_filtered = filter_song_hints(filter_q, genre=genre, limit=500)
        page = int(st.session_state.get("song_picker_page", 0))
        max_page = max(0, (len(all_filtered) - 1) // page_size)
        page = min(page, max_page)
        hints = all_filtered[page * page_size : (page + 1) * page_size]
        st.caption(f"{len(all_filtered)}곡 · 페이지 {page + 1}/{max_page + 1} · DB {total}곡")
        if not hints:
            st.caption("검색 결과가 없어요.")
            return
        nav_l, nav_r = st.columns(2)
        with nav_l:
            if page > 0 and st.button("← 이전", key="song_picker_prev", use_container_width=True):
                st.session_state["song_picker_page"] = page - 1
                st.rerun()
        with nav_r:
            if page < max_page and st.button("다음 →", key="song_picker_next", use_container_width=True):
                st.session_state["song_picker_page"] = page + 1
                st.rerun()
        cols = st.columns(3)
        for i, hint in enumerate(hints):
            if cols[i % 3].button(
                format_song_label(hint),
                key=f"pick_{hint.artist}_{hint.title}_{page}",
                use_container_width=True
            ):
                st.session_state["song_title"] = f"{hint.artist} {hint.title}"
                st.rerun()


def _render_midi_reference_upload() -> None:
    uploaded = st.file_uploader(
        "MIDI 악보 (선택)",
        type=["mid", "midi"],
        key="midi_reference_upload",
        help="유튜브 가이드 대신 MIDI 멜로디를 기준으로 분석합니다."
    )
    cache_dir = Path(__file__).resolve().parent.parent / ".cache" / "midi"
    if uploaded is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        dest = cache_dir / uploaded.name
        dest.write_bytes(uploaded.getvalue())
        st.session_state["midi_reference_path"] = str(dest)
        st.caption(f"✓ MIDI 적용: {uploaded.name}")
    elif not st.session_state.get("midi_reference_path"):
        st.session_state.pop("midi_reference_path", None)


def render_analysis_settings(*, simple: bool = True) -> None:
    from style_presets import PRESETS
    from ui.help_guide import render_song_title_help

    if "fast_mode" not in st.session_state:
        st.session_state.fast_mode = True

    render_safe_html('<p class="vc-sidebar-title">🎤 버튼 하나로 1분 분석</p>')
    render_song_title_help()
    st.text_input(
        "곡 제목 (선택)",
        key="song_title",
        placeholder="예: 아이유 밤편지 — 비워도 OK",
    )
    if simple:
        st.caption("기본 **빠른 분석** · 약 1분 · 대부분의 녹음에 충분해요.")
        with st.expander("⚙️ 고급 설정 (정밀·유튜브·GPT)", expanded=False):
            _render_advanced_settings(PRESETS)
        return
    _render_advanced_settings(PRESETS)


def _render_advanced_settings(PRESETS: dict) -> None:
    from ui.help_guide import render_youtube_guide_sidebar

    styles.sidebar_label("분석 모드")
    st.checkbox("빠른 분석 (권장)", key="fast_mode", value=True)
    st.caption("정밀 분석은 Cloud에서 2~3분+ 걸릴 수 있어요.")
    _render_popular_song_picker()
    st.checkbox("유튜브 가이드 사용", key="use_youtube", value=False)
    render_youtube_guide_sidebar()
    _render_midi_reference_upload()
    st.selectbox(
        "가창 스타일",
        options=list(PRESETS.keys()),
        format_func=lambda k: PRESETS[k].label,
        key="style_preset",
    )
    st.checkbox("GPT 코칭", key="use_gpt", value=False)
    st.checkbox("기록 저장", key="save_record", value=True)
    st.checkbox("문제 구간 클립", key="export_clips", value=False)


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
        help="정밀 분석 · 유튜브 · GPT 등"
    ):
        open_analysis_settings_dialog()


def render_analysis_settings_expander(*, expanded: bool = False) -> None:
    """인라인 분석 설정 — 기본 접힘 (원클릭 분석 UX)."""
    with st.expander("⚙️ 곡 제목 · 고급 설정", expanded=expanded):
        render_analysis_settings(simple=True)
