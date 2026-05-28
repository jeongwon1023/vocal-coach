"""분석 세션 캐시 — 마이 페이지에서 결과 다시 보기."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / ".cache" / "sessions"


def _user_dir(user_id: str) -> Path:
    d = CACHE_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_key(session: dict[str, Any], record_path: str | Path | None) -> str:
    if record_path:
        return Path(record_path).stem
    report = session.get("report")
    overall = getattr(report, "overall_score", 0) if report else 0
    return f"adhoc_{overall:.0f}_{id(session)}"


def save_session_cache(user_id: str, session: dict[str, Any], record_path: str | Path | None = None) -> Path:
    """분석 직후 전체 세션 저장 (DM·상세 리포트 재표시용)."""
    from analysis import CurriculumReport

    report: CurriculumReport = session["report"]
    payload = {
        "full_record": session.get("full_record") or {},
        "record_path": str(session.get("record_path") or record_path or ""),
        "compare_text": session.get("compare_text", ""),
        "gpt_text": session.get("gpt_text", ""),
        "gpt_error": session.get("gpt_error"),
        "plot_path": str(session.get("plot_path") or ""),
        "plot_error": session.get("plot_error"),
        "heatmap_path": str(session.get("heatmap_path") or ""),
        "heatmap_error": session.get("heatmap_error"),
        "clip_paths": [str(p) for p in session.get("clip_paths") or []],
        "note_clip_paths": session.get("note_clip_paths") or [],
        "note_clip_error": session.get("note_clip_error"),
        "audio_path": str(session.get("audio_path") or ""),
        "chart_path": str(session.get("chart_path") or "") if session.get("chart_path") else "",
        "overall_score": report.overall_score,
        "reference_source": report.reference_source,
        "mr_likely": report.mr_likely,
        "mr_message": report.mr_message,
        "stage_summaries": [
            {
                "stage": s.stage,
                "title": s.title,
                "score": s.score,
                "summary": s.summary,
            }
            for s in report.stages
        ],
    }
    key = _session_key(session, record_path or session.get("record_path"))
    path = _user_dir(user_id) / f"{key}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session_cache(user_id: str, record_stem: str) -> dict[str, Any] | None:
    path = _user_dir(user_id) / f"{record_stem}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return rebuild_session_from_cache(data)


def rebuild_session_from_cache(data: dict[str, Any]) -> dict[str, Any]:
    from analysis import CurriculumReport, StageResult

    stages = [
        StageResult(
            stage=int(s["stage"]),
            title=s.get("title", ""),
            score=float(s.get("score", 0)),
            summary=s.get("summary", ""),
            coaching_blocks=[],
            details={},
        )
        for s in data.get("stage_summaries", [])
    ]
    report = CurriculumReport(
        audio_path=Path(""),
        duration_sec=0.0,
        pitch_deviation_segments=[],
        stable_regions=[],
        breath_mismatch_segments=[],
        timbre_issue_segments=[],
        stages=stages,
        overall_score=float(data.get("overall_score", 0)),
        coaching_text="",
        reference_source=data.get("reference_source", ""),
        mr_likely=bool(data.get("mr_likely", False)),
        mr_message=data.get("mr_message", ""),
    )
    plot_path = data.get("plot_path") or None
    heatmap_path = data.get("heatmap_path") or None
    chart_path = data.get("chart_path") or None
    return {
        "report": report,
        "full_record": data.get("full_record") or {},
        "record_path": data.get("record_path"),
        "compare_text": data.get("compare_text", ""),
        "gpt_text": data.get("gpt_text", ""),
        "gpt_error": data.get("gpt_error"),
        "plot_path": plot_path if plot_path and Path(plot_path).exists() else None,
        "plot_error": data.get("plot_error"),
        "heatmap_path": heatmap_path if heatmap_path and Path(heatmap_path).exists() else None,
        "heatmap_error": data.get("heatmap_error"),
        "clip_paths": [p for p in (data.get("clip_paths") or []) if Path(p).exists()],
        "note_clip_paths": [
            c
            for c in (data.get("note_clip_paths") or [])
            if Path(c.get("path", "")).exists()
        ],
        "note_clip_error": data.get("note_clip_error"),
        "audio_path": (
            data.get("audio_path")
            if data.get("audio_path") and Path(data["audio_path"]).exists()
            else None
        ),
        "chart_path": chart_path if chart_path and Path(chart_path).exists() else None,
    }


def rebuild_session_from_record(record: dict[str, Any], record_path: str | Path | None = None) -> dict[str, Any]:
    """저장된 JSON 기록 → 세션 (캐시 없을 때 요약 보기)."""
    from analysis import CurriculumReport, StageResult

    stage_scores = record.get("stage_scores") or {}
    stage_details = record.get("stage_details") or {}
    stages: list[StageResult] = []
    for i in (1, 2, 3, 4):
        score = float(stage_scores.get(i) or stage_scores.get(str(i)) or 0)
        detail = stage_details.get(str(i)) or stage_details.get(i) or {}
        summary = detail.get("summary") or ""
        title = detail.get("title") or f"Stage {i}"
        stages.append(
            StageResult(
                stage=i,
                title=title,
                score=score,
                summary=summary,
                coaching_blocks=[],
                details=detail if isinstance(detail, dict) else {},
            )
        )

    report = CurriculumReport(
        audio_path=Path(""),
        duration_sec=0.0,
        pitch_deviation_segments=[],
        stable_regions=[],
        breath_mismatch_segments=[],
        timbre_issue_segments=[],
        stages=stages,
        overall_score=float(record.get("overall_score") or 0),
        coaching_text="",
        reference_source=record.get("reference_source", ""),
        mr_likely=bool(record.get("mr_likely", False)),
        mr_message=record.get("mr_message", ""),
    )
    return {
        "report": report,
        "full_record": record,
        "record_path": str(record_path) if record_path else record.get("record_path"),
        "compare_text": "",
        "gpt_text": "",
        "gpt_error": None,
        "plot_path": None,
        "plot_error": None,
        "clip_paths": [],
        "chart_path": None,
    }
