"""분석 결과 — 잘한 점 · 집중 연습 3가지 (구체적 문장)."""

from __future__ import annotations

import re
from typing import Any

from coaching_vocab import STAGE_NAMES, cent_to_words, time_range


def _seg_times(seg: Any) -> tuple[float, float]:
    """PitchSegment 객체 또는 (start, end) 튜플."""
    if isinstance(seg, (tuple, list)) and len(seg) >= 2:
        return float(seg[0]), float(seg[1])
    return float(getattr(seg, "start_sec", 0)), float(getattr(seg, "end_sec", 0))


def _strip_md(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text or "").strip()


def build_strength_items(session: dict[str, Any]) -> list[dict[str, str]]:
    """오늘 잘한 점 3가지 — 굵은 한 줄 + 자세한 설명."""
    report = session["report"]
    stages = {s.stage: s for s in report.stages}
    s1, s2, s3 = stages.get(1), stages.get(2), stages.get(3)
    s4 = stages.get(4)
    items: list[dict[str, str]] = []

    if s1:
        mm = s1.details.get("melody_match_ratio")
        if mm is not None:
            pct = float(mm) * 100
            if pct >= 55:
                items.append(
                    {
                        "headline": f"가이드 멜로디와 {pct:.0f}% 맞춰 불렀어요",
                        "detail": (
                            f"음정 점수 {s1.score:.0f}점. 원곡 흐름을 따라가는 구간이 많아요. "
                            f"특히 멜로디 라인을 크게 벗어나지 않고 안정적으로 이어갔습니다."
                        ),
                    }
                )
        stable = s1.details.get("stable_pct")
        if stable is not None and float(stable) >= 50 and len(items) < 3:
            items.append(
                {
                    "headline": f"음정이 흔들리지 않은 구간이 {float(stable):.0f}%예요",
                    "detail": (
                        "한 음을 붙일 때 목소리가 크게 요동치지 않았어요. "
                        "이런 안정감은 고음·롱톤 연습할 때 큰 자산이 됩니다."
                    ),
                }
            )

    if s2 and s2.score >= 60 and len(items) < 3:
        cv = s2.details.get("rhythm_cv")
        cv_txt = f" (리듬 변동 {float(cv):.2f})" if cv is not None else ""
        items.append(
            {
                "headline": f"박자·리듬 {s2.score:.0f}점 — 곡이 크게 밀리지 않았어요",
                "detail": (
                    f"박자감이 전체적으로 유지됐어요{cv_txt}. "
                    "MR과 함께 불렀을 때 흔들리지 않는 구간이 많으면 청자도 편하게 들을 수 있어요."
                ),
            }
        )

    if s3 and s3.score >= 60 and len(items) < 3:
        items.append(
            {
                "headline": f"호흡·음색 {s3.score:.0f}점 — 소리가 비교적 또렷해요",
                "detail": (
                    "호흡이 끊기거나 목소리가 갑자기 작아지는 구간이 많지 않았어요. "
                    "톤이 안정적이면 감정 전달도 자연스럽게 느껴집니다."
                ),
            }
        )

    teacher = (s4.details.get("teacher_strengths") if s4 else None) or []
    for raw in teacher:
        if len(items) >= 3:
            break
        headline = _strip_md(raw)
        if any(headline[:10] in i["headline"] for i in items):
            continue
        items.append({"headline": headline, "detail": _detail_for_strength(headline, session)})

    if not items:
        overall = report.overall_score
        items.append(
            {
                "headline": "오늘도 연습하러 와 줘서 고마워요",
                "detail": (
                    f"종합 {overall:.0f}점으로 시작했어요. "
                    "매번 녹음·분석하면 점수가 쌓이면서 실력 변화를 숫자로 확인할 수 있어요."
                ),
            }
        )

    return items[:3]


def _detail_for_strength(headline: str, session: dict[str, Any]) -> str:
    report = session["report"]
    if "멜로디" in headline or "음정" in headline:
        segs = report.stable_regions[:1]
        if segs:
            t0, t1 = _seg_times(segs[0])
            return (
                f"예를 들어 {time_range(t0, t1)} 구간처럼 "
                f"음정이 안정적으로 유지된 부분이 눈에 띄었어요."
            )
        return "틀린 구간보다 맞춘 구간이 더 많아요. 이 감각을 유지하는 게 중요해요."
    if "박자" in headline or "리듬" in headline:
        return "박이 밀리지 않고 MR과 잘 맞는 구간이 있어요. 노래가 '흔들리지 않는' 느낌을 줍니다."
    if "호흡" in headline:
        return "프레이즈 중간에 숨이 끊기거나 소리가 갑자기 약해지지 않았어요. 호흡 지지가 받쳐 주고 있어요."
    if "롱톤" in headline:
        return "길게 붙인 음에서 목소리가 버티는 힘이 보여요. 고음·마무리 음에서 특히 도움이 됩니다."
    if "비브라토" in headline:
        return "비브라토가 자연스럽게 걸려서 감정 표현이 살아 있어요. 억지로 흔들지 않아도 좋아요."
    return "선생님이 들었을 때 인상적인 부분이에요. 이 강점을 의식하면서 연습하면 자신감도 올라갑니다."


def build_focus_items(session: dict[str, Any]) -> list[dict[str, str]]:
    """먼저 잡을 연습 3가지 — 구체적 행동 중심."""
    full = session.get("full_record") or {}
    actions = full.get("priority_actions") or []
    if actions:
        out: list[dict[str, str]] = []
        for act in actions[:3]:
            if not isinstance(act, dict):
                continue
            title = act.get("title") or act.get("action") or "연습 포인트"
            rx = act.get("prescription") or ""
            practice = (act.get("practice") or "").replace("**", "")
            reason = act.get("reason") or ""
            detail_parts = [p for p in (rx, practice, reason) if p]
            out.append(
                {
                    "headline": _strip_md(str(title)),
                    "detail": " ".join(detail_parts[:2]) if detail_parts else "오늘 이 부분만 짧게 반복해 보세요.",
                    "priority": act.get("priority", len(out) + 1),
                }
            )
        if out:
            return out

    report = session["report"]
    stages = report.stages[:3]
    items: list[dict[str, str]] = []
    sorted_stages = sorted(stages, key=lambda s: s.score)

    for i, stage in enumerate(sorted_stages[:3], 1):
        label = STAGE_NAMES.get(stage.stage, stage.title)
        headline = f"{label} {stage.score:.0f}점 — 집중 연습"
        detail = getattr(stage, "summary", None) or f"{label} 영역을 10분만 연습해도 체감이 달라져요."
        if stage.stage == 1 and report.pitch_deviation_segments:
            seg = report.pitch_deviation_segments[0]
            t0, t1 = _seg_times(seg)
            cents = getattr(seg, "max_deviation_cents", 0)
            detail = (
                f"{time_range(t0, t1)} 구간이 "
                f"{cent_to_words(float(cents))}. "
                f"이 구간만 0.5배속으로 10번 반복해 보세요."
            )
        items.append({"headline": headline, "detail": detail, "priority": i})

    while len(items) < 3:
        items.append(
            {
                "headline": "같은 곡으로 1주 후 다시 녹음하기",
                "detail": "오늘 점수를 저장해 두고, 같은 곡을 다시 불러 비교하면 성장이 보여요.",
                "priority": len(items) + 1,
            }
        )

    return items[:3]
