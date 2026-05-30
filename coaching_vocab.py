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


def format_mmss(seconds: float) -> str:
    """유저-facing 타임스탬프 — MM:SS."""
    s = max(0, int(round(seconds)))
    minutes, secs = divmod(s, 60)
    return f"{minutes:02d}:{secs:02d}"


def timestamp_at(seconds: float) -> str:
    """단일 시점 — ⏱ [01:15]"""
    return f"⏱ [{format_mmss(seconds)}]"


def time_range(start: float, end: float) -> str:
    """구간 — ⏱ [01:15]–[01:22] 구간 (오디오 재생 유도용)."""
    if abs(end - start) < 0.45:
        return f"{timestamp_at(start)} 구간"
    return f"{timestamp_at(start)}–[{format_mmss(end)}] 구간"


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
    """유저 화면용 — 내부 지수·횟수 없이 트레이너 언어로."""
    _ = attack_count  # 내부 분석용, UI에는 노출하지 않음
    if rhythm_cv <= 0.28:
        return (
            "리듬의 그루브가 안정적이에요. "
            "음을 시작하는 첫 타점(어택)도 고르게 맞추고 있습니다."
        )
    if rhythm_cv <= 0.45:
        return (
            "리듬의 그루브가 조금씩 흔들려요. "
            "음을 시작하는 첫 타점(어택)이 가끔 밀리거나 당겨집니다."
        )
    return (
        "엇박자가 자주 발생하여 리듬의 그루브가 흔들리고 있습니다. "
        "음을 시작하는 타점(어택)이 일정하지 않아요."
    )


def breath_summary(env_cv: float, breath_issues: int, timbre_issues: int) -> str:
    return (
        f"호흡 지지·음량: {env_cv_to_words(env_cv)} · "
        f"힘 빠짐/튀는 구간 {breath_issues}곳 · "
        f"음색 흐려진 구간 {timbre_issues}곳"
    )


def derive_vocal_title(stages: list) -> str:
    """4영역 점수 조합 → 보컬 MBTI 한 줄 타이틀."""
    scores: dict[int, float] = {}
    for s in stages or []:
        if hasattr(s, "stage"):
            scores[int(s.stage)] = float(getattr(s, "score", 0) or 0)
        elif isinstance(s, dict):
            scores[int(s.get("stage", 0))] = float(s.get("score", 0) or 0)

    pitch = scores.get(1, 70.0)
    rhythm = scores.get(2, 70.0)
    breath = scores.get(3, 70.0)

    strong, weak = 75.0, 58.0

    def band(v: float) -> str:
        if v >= strong:
            return "H"
        if v < weak:
            return "L"
        return "M"

    p, r, b = band(pitch), band(rhythm), band(breath)

    rules: list[tuple[bool, str]] = [
        (p == "H" and r == "L", "음정은 칼같지만 리듬감이 아쉬운 '감성 발라더'"),
        (r == "H" and p == "L", "리듬은 지배하지만 음정이 살짝 불안한 '그루브 장인'"),
        (p == "H" and b == "L", "음정은 또렷한데 호흡 지지가 아쉬운 '감성 발라더'"),
        (b == "H" and r == "L", "호흡과 음색은 탄탄한데 박자가 살짝 흔들리는 '롱톤 마스터'"),
        (r == "H" and b == "L", "박자는 좋은데 호흡·음색을 더 채울 '리듬 장인'"),
        (p == "L" and r == "H", "리듬감은 살아 있는데 음정을 다듬을 '그루브 루키'"),
        (p == "H" and r == "H" and b == "H", "음정·박자·호흡 삼박자가 탄탄한 '올라운드 보컬리스트'"),
        (p == "H" and r == "H", "음정과 리듬이 모두 안정적인 '무대 준비 완료형'"),
        (b == "H" and p == "H", "음정·호흡이 탄탄한 '감성 롱톤형'"),
        (p == "L" and r == "L", "기초를 다지는 중인 '열정 새내기'"),
        (p == "M" and r == "M" and b == "M", "골고루 성장 중인 '밸런스형 보컬리스트'"),
    ]
    for ok, title in rules:
        if ok:
            return title
    weakest = min(
        ((1, pitch), (2, rhythm), (3, breath)),
        key=lambda x: x[1],
    )[0]
    focus = STAGE_LABELS_SHORT.get(weakest, "보컬")
    return f"{focus}부터 키워 나갈 '성장형 보컬리스트'"
