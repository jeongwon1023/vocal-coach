"""주간 연습 요약 — 마이 페이지 카드용."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from progress_tracker import load_record, user_records_dir


def _parse_record_time(record: dict) -> datetime | None:
    ts = record.get("recorded_at") or ""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone()
    except Exception:
        return None


def _load_records_chronological(user_id: str | None = None) -> list[dict]:
    d = user_records_dir(user_id)
    if not d.exists():
        return []
    files = sorted(d.glob("record_*.json"), key=lambda p: p.stat().st_mtime)
    records: list[dict] = []
    for path in files:
        try:
            records.append(load_record(path))
        except Exception:
            continue
    return records


def _avg_score(records: list[dict]) -> float | None:
    scores = [float(r.get("overall_score") or 0) for r in records if r.get("overall_score") is not None]
    if not scores:
        return None
    return sum(scores) / len(scores)


def _stage_avg(records: list[dict], stage: int) -> float | None:
    vals: list[float] = []
    for r in records:
        scores = r.get("stage_scores") or {}
        v = scores.get(stage) or scores.get(str(stage))
        if v is not None:
            vals.append(float(v))
    if not vals:
        return None
    return sum(vals) / len(vals)


def _top_song(records: list[dict]) -> str | None:
    counts: dict[str, int] = {}
    for r in records:
        song = (r.get("song_title") or "").strip()
        if not song:
            continue
        counts[song] = counts.get(song, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def compute_weekly_summary(user_id: str | None = None, *, days: int = 7) -> dict[str, Any]:
    """최근 N일 vs 이전 N일 비교 요약."""
    records = _load_records_chronological(user_id)
    now = datetime.now().astimezone()
    this_start = now - timedelta(days=days)
    prev_start = now - timedelta(days=days * 2)

    this_week: list[dict] = []
    prev_week: list[dict] = []
    for r in records:
        dt = _parse_record_time(r)
        if dt is None:
            continue
        if dt >= this_start:
            this_week.append(r)
        elif dt >= prev_start:
            prev_week.append(r)

    this_avg = _avg_score(this_week)
    prev_avg = _avg_score(prev_week)
    delta = None
    if this_avg is not None and prev_avg is not None:
        delta = this_avg - prev_avg

    best_this = max(
        (float(r.get("overall_score") or 0) for r in this_week),
        default=None,
    )
    top_song = _top_song(this_week)

    stage_deltas: dict[str, float] = {}
    for stage, label in ((1, "음정"), (2, "박자"), (3, "호흡")):
        cur = _stage_avg(this_week, stage)
        prev = _stage_avg(prev_week, stage)
        if cur is not None and prev is not None:
            stage_deltas[label] = cur - prev

    best_stage = None
    if stage_deltas:
        label, d = max(stage_deltas.items(), key=lambda x: x[1])
        if d > 0.5:
            best_stage = label

    message = _build_message(len(this_week), delta, best_stage)

    return {
        "days": days,
        "count": len(this_week),
        "prev_count": len(prev_week),
        "total_records": len(records),
        "avg_score": this_avg,
        "prev_avg_score": prev_avg,
        "delta": delta,
        "best_score": best_this,
        "top_song": top_song,
        "best_stage": best_stage,
        "stage_deltas": stage_deltas,
        "message": message,
        "has_data": len(this_week) > 0,
    }


def _build_message(count: int, delta: float | None, best_stage: str | None) -> str:
    if count == 0:
        return "이번 주 아직 분석이 없어요. 오늘 한 번 녹음해 보세요!"
    if delta is not None and delta >= 3:
        return f"이번 주 평균이 {delta:+.0f}pt 올랐어요. 페이스 유지!"
    if delta is not None and delta <= -3:
        return "이번 주는 컨디션·녹음 환경을 점검해 보세요. MR 없이 다시 도전!"
    if best_stage:
        return f"{best_stage} 영역이 가장 많이 성장했어요. 같은 연습을 이어가 보세요."
    if count >= 3:
        return "꾸준히 연습 중이에요. 같은 곡으로 비교 분석하면 더 정확해요."
    return "좋은 시작이에요. 이번 주 2~3회 더 분석하면 추세가 보여요."
