"""
보컬 선생님 관점 분석 — 강점·다이내믹·프레이즈 연결·비브라토.

유튜브·학원 강의에서 공통으로 듣는 항목을 기술적으로 보완합니다.
- Ken Tamplin: 강점 먼저, 다이내믹, twang/표현
- Ramsey Voice: 호흡·비브라토 자연스러움
- Dr Dan: 공기·공명·pitch nuance
"""

from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np
from scipy.ndimage import median_filter


def _block(result: str, cause: str, solution: str):
    from analysis import CoachingBlock

    return CoachingBlock(result=result, cause=cause, solution=solution)


@dataclass
class TeacherAssessment:
    strengths: list[str] = field(default_factory=list)
    dynamics_score: float = 0.0
    phrase_legato_score: float = 0.0
    praise_line: str = ""
    extra_blocks: list = field(default_factory=list)


def _detect_strengths(
    *,
    s1_score: float,
    s2_score: float,
    s3_score: float,
    melody_match_pct: float,
    sustained_ratio: float,
    interval_match: float,
    research: object | None,
    dtw_result: object | None,
    is_pro_like: bool,
    rubato_detected: bool,
) -> list[str]:
    strengths: list[str] = []

    if melody_match_pct >= 75 or s1_score >= 72:
        strengths.append("음정이 가이드 멜로디를 잘 따라가고 있어요")
    if interval_match >= 70:
        strengths.append("음과 음 사이 **간격(멜로디 흐름)** 이 자연스러워요")
    if sustained_ratio >= 0.35:
        strengths.append("롱톤을 길게 안정적으로 붙이는 힘이 있어요")
    if s2_score >= 70:
        strengths.append("박자·리듬감이 안정적이에요")
    if rubato_detected:
        strengths.append("루바토로 감정선을 살리는 **표현력**이 느껴져요")
    if is_pro_like:
        strengths.append("배음이 풍부해서 **공명·음색**이 좋아요")
    if s3_score >= 70:
        strengths.append("호흡 지지가 비교적 안정적이에요")

    if research is not None:
        vib = getattr(research, "vibrato", None)
        if vib and getattr(vib, "quality", "") == "normal":
            rate = getattr(vib, "rate_hz", 0) or 0
            strengths.append(f"비브라토가 자연스러워요 (약 {rate:.1f}Hz)")
        tier = getattr(research, "pitch_tier", "")
        if tier == "pro" and melody_match_pct >= 60:
            strengths.append("훈련된 가수에 가까운 음정 안정도예요")
        hnr = getattr(research, "hnr_db", None)
        if hnr is not None and hnr >= 15:
            strengths.append("목소리가 비교적 깨끗하게(공기 적게) 나와요")
        sf = getattr(research, "singer_formant_ratio", None)
        if sf is not None and sf >= 0.12:
            strengths.append("고음역 **싱어즈 포먼트**가 살아 있어요")

    if dtw_result is not None:
        musical = getattr(dtw_result, "musical_accuracy_percent", 0) or 0
        if musical >= 75:
            strengths.append("원곡 가이드와 **음악적으로** 잘 맞춰 불렀어요")

    # 중복·유사 제거 (앞 4개만)
    seen: set[str] = set()
    unique: list[str] = []
    for s in strengths:
        key = s[:12]
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique[:4]


def analyze_dynamics(rms_voiced: np.ndarray) -> tuple[float, str | None]:
    """
    다이내믹(음량 변화) — Ken Tamplin 'Dynamics' 항목.
    너무 평평하면 단조, 너무 요동치면 호흡 불안.
    """
    if rms_voiced.size < 15:
        return 50.0, None

    cv = float(np.std(rms_voiced) / (np.mean(rms_voiced) + 1e-6))
    if 0.22 <= cv <= 0.52:
        score = min(95.0, 72.0 + cv * 45.0)
        note = "곡 전체에서 크고 작게(다이내믹) 변화를 잘 살렸어요"
    elif cv < 0.18:
        score = max(45.0, 55.0 + cv * 80.0)
        note = "한결같은 음량이라 감정선이 조금 평평하게 느껴질 수 있어요"
    else:
        score = max(40.0, 68.0 - (cv - 0.52) * 40.0)
        note = "음량 변화가 커서 호흡·힘 조절 연습이 도움돼요"

    return round(score, 1), note


def analyze_phrase_legato(
    f0: np.ndarray,
    times: np.ndarray,
    rms: np.ndarray,
    sr: int,
    hop_length: int,
) -> tuple[float, str | None]:
    """
    프레이즈 연결(레가토) — 문장 중간 끊김 vs 자연스러운 호흡.
    """
    voiced = np.isfinite(f0) & (f0 > 0)
    if np.sum(voiced) < 30:
        return 50.0, None

    # 무성 구간 0.25~1.2초 = 프레이즈 내 끊김 후보
    unvoiced_runs: list[float] = []
    in_gap = False
    gap_start = 0.0
    for i, v in enumerate(voiced):
        t = float(times[i]) if i < len(times) else 0.0
        if not v and not in_gap:
            in_gap = True
            gap_start = t
        elif v and in_gap:
            in_gap = False
            dur = t - gap_start
            if 0.25 <= dur <= 1.2:
                unvoiced_runs.append(dur)

    n_voiced_frames = int(np.sum(voiced))
    break_ratio = len(unvoiced_runs) / max(1, n_voiced_frames / 50)

    if break_ratio <= 0.8:
        score = min(92.0, 78.0 + (1.0 - break_ratio) * 12.0)
        note = "한 문장을 끊기지 않고 이어 부르는 **연결(레가토)** 이 좋아요"
    elif break_ratio <= 2.0:
        score = 62.0
        note = "가끔 문장 중간에 숨·끊김이 있어요 — 호흡 계획을 세워보면 좋아요"
    else:
        score = max(40.0, 55.0 - break_ratio * 3.0)
        note = "프레이즈마다 끊김이 많아요 — ‘쉬는 박’과 ‘끊기는 박’을 구분해 연습해요"

    return round(score, 1), note


def vibrato_coaching_block(research: object | None):
    """비브라토 품질 — Singéo/Ramsey: 자연 vs 억지."""
    if research is None:
        return None
    vib = getattr(research, "vibrato", None)
    if not vib or getattr(vib, "quality", "none") in ("none", "weak"):
        return None

    q = vib.quality
    rate = getattr(vib, "rate_hz", 0) or 0
    extent = getattr(vib, "extent_cents", 0) or 0

    if q == "normal":
        return _block(
            result=f"비브라토가 자연스럽게 나와요 (약 {rate:.1f}Hz, 폭 {extent:.0f}센트).",
            cause="긴장을 풀고 호흡 지지가 있을 때 나오는 **건강한 비브라토**예요.",
            solution="이 상태를 유지하세요. 고음으로 갈 때 턱·목 힘만 빼면 됩니다.",
        )
    if q == "wobble":
        return _block(
            result="롱톤에서 비브라토가 **너무 느리게** 흔들려요 (wobble).",
            cause=f"비브라토 속도 {rate:.1f}Hz — 보통 4.5~6.5Hz가 자연스러워요. 목·턱 긴장이 원인일 수 있어요.",
            solution="'쉬—' 5초 내뱉기 5세트 → 턱·어깨 힘 빼고 '아—' 롱톤 10번. 빠르게 흔들려고 하지 마세요.",
        )
    if q == "bleat":
        return _block(
            result="비브라토가 **너무 빠르게** 떨려요 (양털소리/비트).",
            cause=f"속도 {rate:.1f}Hz — 성대·목에 힘이 들어가면 이렇게 나와요.",
            solution="속도 0.75배 MR로 천천히 부르기 · 복식호흡 후 부드러운 '오—' 롱톤 8번.",
        )
    return None


def build_teacher_assessment(
    *,
    stages: list,
    pitch: object,
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    times: np.ndarray,
    y_harm: np.ndarray | None,
    dtw_result: object | None,
    is_pro_like: bool,
) -> TeacherAssessment:
    from teacher_voice import lesson_opening

    s1, s2, s3 = stages[0], stages[1], stages[2]
    rubato = bool(
        dtw_result and getattr(dtw_result, "rubato_detected", False)
    )
    interval = getattr(pitch, "interval_match_ratio", 0.0) or 0.0
    research = getattr(pitch, "research", None)

    strengths = _detect_strengths(
        s1_score=s1.score,
        s2_score=s2.score,
        s3_score=s3.score,
        melody_match_pct=getattr(pitch, "melody_match_ratio", 0) * 100,
        sustained_ratio=getattr(pitch, "sustained_ratio", 0),
        interval_match=interval,
        research=research,
        dtw_result=dtw_result,
        is_pro_like=is_pro_like,
        rubato_detected=rubato,
    )

    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    rms = librosa.feature.rms(y=y_harm, hop_length=hop_length)[0]
    rms = median_filter(rms, size=5)
    n = min(len(rms), len(f0))
    voiced = np.isfinite(f0[:n]) & (f0[:n] > 0)
    rms_v = rms[:n][voiced]

    dyn_score, dyn_note = analyze_dynamics(rms_v)
    legato_score, legato_note = analyze_phrase_legato(f0, times, rms[:n], sr, hop_length)

    extra: list = []
    vib_block = vibrato_coaching_block(research)
    if vib_block:
        extra.append(vib_block)

    if dyn_note and dyn_score >= 72:
        extra.append(
            _block(
                result=dyn_note,
                cause="좋은 가수는 한 곡 안에서도 크고 작게(다이내믹) 표현해요.",
                solution="이 감각 유지하세요. 감정 큰 구간만 살짝 키우고, 마무리는 부드럽게.",
            )
        )
    elif dyn_note and dyn_score < 60:
        extra.append(
            _block(
                result=dyn_note,
                cause="음량이 거의 일정하면 감정 전달이 단조로울 수 있어요.",
                solution="2마디씩 나눠 ‘작게 시작 → 절정에서 키우기 → 마지막 한 박 작게’ 5번 반복.",
            )
        )

    if legato_note and legato_score < 65:
        extra.append(
            _block(
                result=legato_note,
                cause="문장 중간 끊김은 호흡 계획·성대 closure와 연결돼요.",
                solution="가사 한 줄을 ‘한 번에 쭉’ 부르기 연습 · 숨은 **쉬는 박**에만.",
            )
        )

    overall_hint = (s1.score + s2.score + s3.score) / 3
    praise = lesson_opening(strengths, overall_hint)

    return TeacherAssessment(
        strengths=strengths,
        dynamics_score=dyn_score,
        phrase_legato_score=legato_score,
        praise_line=praise,
        extra_blocks=extra,
    )
