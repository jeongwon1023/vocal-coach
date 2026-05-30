"""분석 진행 — 상단 고정 배너 · 단계별 hover 설명."""

from __future__ import annotations

import html

import streamlit as st
from ui.utils import render_safe_html

STEPS: list[tuple[str, str, float]] = [
    ("🎵", "오디오 불러오기", 0.05),
    ("🎧", "보컬 분리", 0.12),
    ("🎯", "음정 분석", 0.30),
    ("⏱️", "박자·리듬", 0.50),
    ("🫁", "호흡·음색", 0.65),
    ("📝", "코칭 작성", 0.78),
    ("💾", "저장", 0.92),
    ("✅", "완료", 1.0),
]

STEP_TIPS: dict[str, str] = {
    "오디오 불러오기": "녹음 파일을 읽고 길이·음질을 확인해요.",
    "보컬 분리": "MR과 보컬을 분리해 분석 준비를 해요.",
    "음정 분석": "피치(F0)를 추출해 음정이 맞는 구간을 찾아요.",
    "박자·리듬": "박자·리듬이 밀리거나 앞서는 구간을 잡아요.",
    "호흡·음색": "호흡 끊김·목소리 톤·다이내믹을 살펴봐요.",
    "코칭 작성": "선생님 코멘트와 연습 포인트를 정리해요.",
    "저장": "결과·그래프·기록을 저장해요.",
    "완료": "분석이 끝났어요! 곧 결과를 보여드릴게요.",
}


def _step_state(pct: float, threshold: float) -> str:
    if pct >= threshold:
        return "done"
    if pct >= threshold - 0.12:
        return "active"
    return "pending"


def render_stepper(
    pct: float,
    message: str = "",
    *,
    eta_label: str = "",
    mode_label: str = ""
) -> None:
    chips = []
    for emoji, label, threshold in STEPS:
        state = _step_state(pct, threshold)
        tip = html.escape(STEP_TIPS.get(label, label))
        chips.append(
            f'<span class="vc-chip vc-chip-{state} vc-chip-tip" data-tip="{tip}">'
            f"{emoji} {html.escape(label)}</span>"
        )

    pct_display = min(max(int(pct * 100), 0), 100)
    msg = html.escape(message or "분석 중…")
    eta_html = f'<p class="vc-chat-eta">⏱ {html.escape(eta_label)}</p>' if eta_label else ""
    mode_html = (
        f'<span class="vc-chat-mode-pill">{html.escape(mode_label)}</span>' if mode_label else ""
    )
    render_safe_html(
        f"""
        <div class="vc-chat-card vc-analyze-progress-card" id="vc-analyze-progress-card">
            <div class="vc-chat-avatar">🎤</div>
            <div class="vc-chat-body">
                <p class="vc-chat-name">Vocal Coach AI {mode_html}</p>
                <p class="vc-chat-msg">{msg}</p>
                {eta_html}
                <div class="vc-chat-progress">
                    <div class="vc-chat-progress-fill" style="width:{pct_display}%"></div>
                </div>
                <p class="vc-chat-pct">{pct_display}%</p>
                <div class="vc-chip-row">{"".join(chips)}</div>
            </div>
        </div>
        """
    )


def make_callback(progress_bar, stepper_placeholder, status_placeholder):
    """Streamlit progress bar + stepper 콜백."""

    def on_progress(pct: float, msg: str, *, eta_label: str = "", mode_label: str = "") -> None:
        pct = min(max(pct, 0.0), 1.0)
        progress_bar.progress(int(pct * 100), text=msg)
        with stepper_placeholder.container():
            render_stepper(pct, msg, eta_label=eta_label, mode_label=mode_label)

    return on_progress
