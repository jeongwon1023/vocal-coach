"""브라우저 마이크 실시간 녹음 (Streamlit audio_input)."""

from __future__ import annotations

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def render_live_recorder(
    *,
    disabled: bool = False,
    key: str = "analysis_live_recorder",
) -> UploadedFile | None:
    """마이크 녹음 — 상단 히어로 배너 + 녹음 위젯."""
    st.markdown(
        """
        <div class="vc-record-hero">
            <span class="vc-record-hero-badge">추천 · 가장 빠른 방법</span>
            <p class="vc-record-hero-title">🎙️ 실시간 녹음</p>
            <p class="vc-record-hero-lead">
                버튼 한 번으로 지금 바로 부르고, 정지하면 <b>1분 안에</b> 분석해 드려요
            </p>
            <div class="vc-record-steps">
                <span class="vc-record-step">① 녹음</span>
                <span class="vc-record-step-arrow">→</span>
                <span class="vc-record-step">② 들어보기</span>
                <span class="vc-record-step-arrow">→</span>
                <span class="vc-record-step">③ 분석 시작</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<p class="vc-record-panel-label">아래 보라색 버튼을 눌러 녹음하세요</p>',
            unsafe_allow_html=True,
        )
        recorded = st.audio_input(
            "🎙️ 마이크 녹음 (눌러 시작 · 다시 눌러 정지)",
            sample_rate=44100,
            label_visibility="visible",
            key=key,
            disabled=disabled,
            help="마이크 권한을 허용해 주세요. MR은 이어폰으로 듣고 목소리만 녹음하면 더 정확해요.",
        )

    if recorded is not None:
        st.success("✓ 녹음 완료! 미리듣기로 확인한 뒤, 맨 아래 **분석 시작** 버튼을 눌러 주세요.")
    else:
        st.info("🎧 **팁:** MR은 이어폰으로 듣고, 마이크에는 **내 목소리만** 녹음해 주세요.")

    return recorded


def render_file_upload_fallback(*, disabled: bool = False) -> tuple:
    """파일 업로드 · 샘플 (접이식). Returns (uploaded, use_sample)."""
    uploaded = None
    use_sample = False

    with st.expander("📁 녹음 파일로 올리기 (MP3 · WAV · M4A)", expanded=False):
        st.caption("핸드폰에 저장된 녹음 파일이 있으면 여기서 선택하세요.")

        uploaded = st.file_uploader(
            "녹음 파일 선택",
            type=["mp3", "wav", "m4a", "flac", "ogg"],
            label_visibility="visible",
            key="analysis_uploader",
            disabled=disabled,
        )

        use_sample = st.toggle(
            "샘플(sample.mp3)으로 테스트",
            value=False,
            key="use_sample_check",
            disabled=disabled,
        )

        if uploaded is not None and not disabled:
            ext = uploaded.name.rsplit(".", 1)[-1].lower()
            st.audio(uploaded.getvalue(), format=f"audio/{ext}")

    return uploaded, use_sample
