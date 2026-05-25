"""
보컬 코칭 표현 사전 — 유튜브·학원·커뮤니티에서 쓰는 말로 통일.

원칙:
- 영어 괄호 병기 최소화 (업계에서 한국어로 통용되는 것만: 비브라토, 믹스보이스 등)
- 숫자는 초·BPM·반복 횟수 등 행동에 바로 쓸 수 있게
- [결과][원인][해결] 구조 유지
"""

from __future__ import annotations

# ── Stage 제목 (웹·리포트 공통) ──
STAGE_TITLES = {
    1: "음정",
    2: "박자·리듬",
    3: "호흡·음색",
    4: "종합 코칭",
}

STAGE_LABELS_SHORT = {1: "음정", 2: "박자", 3: "호흡·음색"}
STAGE_NAMES = STAGE_LABELS_SHORT  # UI alias


def cent_to_words(cents: float) -> str:
    """센트 → 초보자가 감 잡을 수 있는 표현."""
    c = abs(cents)
    if c < 15:
        return "거의 맞음 (살짝 흔들림)"
    if c < 35:
        return "반음의 1/4~1/3 정도 벗어남"
    if c < 55:
        return "반음의 절반쯤 벗어남 (음정 ½칸 틀림)"
    if c < 90:
        return "거의 반음 하나 틀림"
    return "반음 이상 크게 벗어남"


def rhythm_cv_to_words(cv: float) -> str:
    if cv <= 0.28:
        return "박자가 비교적 안정적"
    if cv <= 0.45:
        return "박이 조금씩 밀리거나 당겨짐"
    if cv <= 0.65:
        return "한 박 한 박 간격이 들쭉날쭉함"
    return "박자가 자주 어긋나 리듬감이 흔들림"


def env_cv_to_words(cv: float) -> str:
    if cv <= 0.35:
        return "한 호흡으로 쭉 끌고 가는 느낌"
    if cv <= 0.48:
        return "구간마다 힘·음량이 오르내림"
    return "호흡 지지가 자주 끊기며 소리가 들쭉날쭉함"


def hf_drop_to_words(pct: float) -> str:
    if pct >= 50:
        return "소리가 탁해지거나 공기가 많이 섞인 느낌 (성대 닫힘이 약함)"
    if pct >= 30:
        return "고음 성분(밝기)이 빠져 목소리가 어두워짐"
    return "음색이 살짝 흐려짐"


def time_range(start: float, end: float) -> str:
    return f"{start:.1f}초~{end:.1f}초"


def pitch_summary(
    match_pct: float,
    sustained_pct: float,
    vibrato_pct: float,
    deviation_count: int,
    dtw_pct: float | None = None,
) -> str:
    line = (
        f"가이드 멜로디와 맞춘 비율 {match_pct:.0f}% · "
        f"롱톤(길게 붙인 음) {sustained_pct:.0f}% · "
        f"비브라토 {vibrato_pct:.0f}% · "
        f"음정 틀린 구간 {deviation_count}곳"
    )
    if dtw_pct is not None:
        line += f" · 가이드와 타이밍 맞춘 음정 {dtw_pct:.0f}%"
    return line


def rhythm_summary(attack_count: int, rhythm_cv: float) -> str:
    return (
        f"소리 뱉는 타이밍(어택) {attack_count}회 · "
        f"박 간격 들쭉날쭉 지수 {rhythm_cv:.2f} "
        f"({rhythm_cv_to_words(rhythm_cv)})"
    )


def breath_summary(env_cv: float, breath_issues: int, timbre_issues: int) -> str:
    return (
        f"호흡·음량 안정도 {env_cv:.2f} ({env_cv_to_words(env_cv)}) · "
        f"힘 빠짐/튀는 구간 {breath_issues}곳 · "
        f"음색 흐려진 구간 {timbre_issues}곳"
    )
