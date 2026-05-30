"""보컬 5축 레이더 스탯 — 음정·박자·호흡·발성·표현력."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from analysis import CurriculumReport


def build_vocal_radar_scores(
    report: "CurriculumReport",
    full_record: dict[str, Any] | None = None,
) -> dict[str, float]:
    """5축 보컬 밸런스 점수 (0~100).

    - 음정 / 박자 / 호흡: Stage 1~3 점수
    - 발성: 음색·성대 닫힘·HNR 기반 (Stage 3 details)
    - 표현력: 다이내믹·레가토·루바토 (Stage 4 / DTW)
    """
    full_record = full_record or {}
    stages = {s.stage: s for s in report.stages}
    s1 = stages.get(1)
    s2 = stages.get(2)
    s3 = stages.get(3)
    s4 = stages.get(4)

    pitch = float(s1.score if s1 else full_record.get("stage_scores", {}).get(1, 70))
    rhythm = float(s2.score if s2 else full_record.get("stage_scores", {}).get(2, 70))
    breath = float(s3.score if s3 else full_record.get("stage_scores", {}).get(3, 70))

    d3 = (s3.details if s3 else {}) or {}
    timbre = d3.get("timbre_score")
    hnr = d3.get("hnr_db")
    vocal_prod = breath
    if timbre is not None:
        vocal_prod = float(timbre) * 0.55 + breath * 0.45
    elif hnr is not None:
        vocal_prod = min(100.0, max(40.0, float(hnr) * 4.5))

    expression = 68.0
    if s4:
        d4 = s4.details or {}
        dyn = float(d4.get("dynamics_score") or 0)
        leg = float(d4.get("phrase_legato_score") or 0)
        if dyn > 0 or leg > 0:
            parts = [x for x in (dyn, leg) if x > 0]
            expression = sum(parts) / len(parts)
    dtw = report.dtw_result
    if dtw is not None:
        rubato = float(getattr(dtw, "rubato_score", 0) or 0)
        if rubato > 0:
            expression = max(expression, rubato * 0.85 + expression * 0.15)

    return {
        "음정": round(min(100.0, max(0.0, pitch)), 1),
        "박자": round(min(100.0, max(0.0, rhythm)), 1),
        "호흡": round(min(100.0, max(0.0, breath)), 1),
        "발성": round(min(100.0, max(0.0, vocal_prod)), 1),
        "표현력": round(min(100.0, max(0.0, expression)), 1),
    }


def radar_insight_text(scores: dict[str, float]) -> str:
    """레이더 차트 아래 한 줄 코치 멘트."""
    if not scores:
        return "분석 결과를 바탕으로 오늘 연습 포인트를 잡아 볼게요."
    best = max(scores, key=scores.get)
    worst = min(scores, key=scores.get)
    best_v = scores[best]
    worst_v = scores[worst]
    if best_v >= 75 and worst_v < 60:
        return f"안정적인 {best}! {worst}만 다듬으면 한층 더 완성도 있게 들릴 거예요."
    if best_v >= 80:
        return f"{best}이(가) 특히 돋보여요. {worst} 쪽을 가볍게 보완해 볼까요?"
    return f"지금은 {worst}부터 함께 잡아보면 체감 실력이 빠르게 올라갈 거예요."
