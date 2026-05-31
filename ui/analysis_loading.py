"""Moises 스타일 분석 로딩 — st.status + 꿀팁."""

from __future__ import annotations

import random

import streamlit as st

VOCAL_TIPS: list[str] = [
    "💡 Vocal Coach 꿀팁: 턱을 살짝 당기고 부르면 고음이 더 잘 올라가요!",
    "💡 복식호흡 — 4초 들이마시고 8초 내쉬기, 하루 5분만 해도 효과 있어요.",
    "💡 박자가 밀리면 MR 70% 속도 + 메트로놈으로 발끝 탭해보세요.",
    "💡 Vocal MBTI 분석 중… 당신만의 보컬 타입을 찾고 있어요!",
    "💡 고음역대 피치 추출 중… 잠깐만, 선생님이 귀 기울이고 있어요 🎤",
    "💡 작게, 정확하게, 같은 구간만 — 음정 점수가 가장 빨리 올라가요.",
    "💡 녹음은 조용한 방 + 이어폰 없이 스피커로 MR 들으며 부르면 좋아요.",
]

STAGE_LABELS: list[tuple[float, str]] = [
    (0.05, "오디오 불러오는 중… 🎵"),
    (0.12, "보컬·MR 분리 중… 🎧"),
    (0.30, "고음역대 피치 추출 중… 🎤"),
    (0.50, "리듬감·박자 분석 중… 🥁"),
    (0.65, "호흡·음색 측정 중… 🫁"),
    (0.78, "AI 코치 리포트 작성 중… 📝"),
    (0.92, "결과 저장 중… 💾"),
    (1.0, "거의 다 됐어요! ✨"),
]


def label_for_progress(pct: float, fallback: str = "") -> str:
    pct = min(max(pct, 0.0), 1.0)
    label = fallback or "AI 보컬 코치가 분석을 시작합니다…"
    for threshold, text in STAGE_LABELS:
        if pct <= threshold + 0.02:
            label = text
            break
    if pct >= 0.95:
        label = STAGE_LABELS[-1][1]
    return label


def pick_tip(*, seed: int | None = None) -> str:
    if seed is not None:
        random.seed(seed)
    return random.choice(VOCAL_TIPS)


def render_analysis_status_block(
    pct: float,
    message: str,
    *,
    eta_label: str = "",
    mode_label: str = "빠른 분석",
) -> None:
    """Moises-style st.status + tip."""
    pct_i = min(max(int(pct * 100), 0), 100)
    label = label_for_progress(pct, message)
    tip_seed = int(st.session_state.get("analysis_tip_seed") or 0)
    if "analysis_tip_seed" not in st.session_state:
        st.session_state.analysis_tip_seed = random.randint(0, 99999)
        tip_seed = st.session_state.analysis_tip_seed
    tip = pick_tip(seed=tip_seed + int(pct * 10))

    with st.status(f"🎤 {label}", expanded=True):
        st.progress(pct_i / 100, text=f"{pct_i}% · {mode_label}")
        if eta_label:
            st.caption(f"⏱ {eta_label}")
        st.markdown(f"**{message or label}**")
        st.info(tip)
