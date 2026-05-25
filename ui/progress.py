"""분석 진행 — 카카오톡·인스타 친화형 스텝 표시."""

from __future__ import annotations

import streamlit as st

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
    mode_label: str = "",
) -> None:
    chips = []
    for emoji, label, threshold in STEPS:
        state = _step_state(pct, threshold)
        chips.append(
            f'<span class="vc-chip vc-chip-{state}">{emoji} {label}</span>'
        )

    pct_display = min(max(int(pct * 100), 0), 100)
    msg = message or "분석 중…"
    eta_html = f'<p class="vc-chat-eta">⏱ {eta_label}</p>' if eta_label else ""
    mode_html = (
        f'<span class="vc-chat-mode-pill">{mode_label}</span>' if mode_label else ""
    )
    st.markdown(
        f"""
        <div class="vc-chat-card">
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
        """,
        unsafe_allow_html=True,
    )


def make_callback(progress_bar, stepper_placeholder, status_placeholder):
    """Streamlit progress bar + stepper 콜백."""

    def on_progress(pct: float, msg: str, *, eta_label: str = "", mode_label: str = "") -> None:
        pct = min(max(pct, 0.0), 1.0)
        progress_bar.progress(int(pct * 100), text=msg)
        with stepper_placeholder.container():
            render_stepper(pct, msg, eta_label=eta_label, mode_label=mode_label)

    return on_progress
