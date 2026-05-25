"""
분석 작업 큐 — 비동기 처리 (로컬 스레드 / Celery 확장 가능).

Streamlit·API에서 긴 곡 분석 시 UI 블로킹 없이
「분석 중…」 상태를 표시하고 완료 후 결과를 반환합니다.

로컬: ThreadPoolExecutor + JSON 상태 파일
배포: USE_CELERY=1 + REDIS_URL 환경변수 시 Celery 워커 사용 (선택)
"""

from __future__ import annotations

import json
import os
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

PROJECT_DIR = Path(__file__).resolve().parent
QUEUE_DIR = PROJECT_DIR / ".cache" / "queue"
RESULTS_DIR = QUEUE_DIR / "results"

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vocal-analysis")
_lock = threading.Lock()


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class AnalysisJob:
    job_id: str
    status: JobStatus
    progress: float = 0.0
    message: str = "대기 중…"
    created_at: str = ""
    updated_at: str = ""
    error: str | None = None
    result_path: str | None = None
    audio_path: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, JobStatus) else self.status
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisJob:
        data = dict(data)
        data["status"] = JobStatus(data["status"])
        return cls(**data)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _job_path(job_id: str) -> Path:
    return QUEUE_DIR / f"{job_id}.json"


def _save_job(job: AnalysisJob) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    job.updated_at = _now_iso()
    _job_path(job.job_id).write_text(
        json.dumps(job.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_job(job_id: str) -> AnalysisJob | None:
    path = _job_path(job_id)
    if not path.exists():
        return None
    try:
        return AnalysisJob.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def cancel_job(job_id: str) -> bool:
    """분석 작업 취소 (UI에서 무시 — 백그라운드 스레드는 계속될 수 있음)."""
    job = get_job(job_id)
    if not job:
        return False
    if job.status in (JobStatus.DONE, JobStatus.FAILED):
        return False
    job.status = JobStatus.FAILED
    job.error = "사용자가 취소했습니다."
    job.message = "취소됨"
    job.progress = 0.0
    _save_job(job)
    with _lock:
        _SESSION_CACHE.pop(job_id, None)
    return True


def load_job_result(job_id: str) -> dict[str, Any] | None:
    job = get_job(job_id)
    if not job or job.status != JobStatus.DONE or not job.result_path:
        return None
    path = Path(job.result_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _run_analysis_worker(job_id: str, audio_path: Path, options: dict[str, Any]) -> None:
    job = get_job(job_id)
    if not job:
        return

    def on_progress(pct: float, msg: str) -> None:
        j = get_job(job_id)
        if j:
            j.progress = round(float(pct) * 100, 1)
            j.message = msg
            j.status = JobStatus.RUNNING
            _save_job(j)

    try:
        from analysis import run_full_session

        job.status = JobStatus.RUNNING
        job.message = "분석 시작…"
        _save_job(job)

        session = run_full_session(
            audio_path,
            song_title=options.get("song_title"),
            use_youtube=options.get("use_youtube", False),
            use_gpt=options.get("use_gpt", False),
            save_record=options.get("save_record", True),
            compare=options.get("compare", True),
            export_clips=options.get("export_clips", False),
            growth_chart=options.get("growth_chart", False),
            save_plot=PROJECT_DIR / "pitch_result.png",
            fast_mode=options.get("fast_mode", True),
            style_preset=options.get("style_preset"),
            user_id=options.get("user_id"),
            on_progress=on_progress,
        )

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        result_path = RESULTS_DIR / f"{job_id}.json"

        # CurriculumReport는 JSON 직렬화 불가 → full_record + 메타 저장
        serializable = {
            "full_record": session.get("full_record"),
            "record_path": str(session["record_path"]) if session.get("record_path") else None,
            "compare_text": session.get("compare_text", ""),
            "gpt_text": session.get("gpt_text", ""),
            "gpt_error": session.get("gpt_error"),
            "plot_path": str(session.get("plot_path", "")),
            "plot_error": session.get("plot_error"),
            "clip_paths": [str(p) for p in session.get("clip_paths", [])],
            "overall_score": session["report"].overall_score,
            "reference_source": session["report"].reference_source,
            "mr_likely": session["report"].mr_likely,
            "mr_message": session["report"].mr_message,
            "stage_summaries": [
                {"stage": s.stage, "title": s.title, "score": s.score, "summary": s.summary}
                for s in session["report"].stages
            ],
        }
        result_path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 세션 객체는 메모리 캐시 (같 프로세스 Streamlit용)
        with _lock:
            _SESSION_CACHE[job_id] = session

        job.status = JobStatus.DONE
        job.progress = 100.0
        job.message = "분석 완료"
        job.result_path = str(result_path)
        _save_job(job)

    except Exception as exc:
        job = get_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.message = "분석 실패"
            _save_job(job)
        traceback.print_exc()


_SESSION_CACHE: dict[str, dict[str, Any]] = {}


def get_session_from_cache(job_id: str) -> dict[str, Any] | None:
    with _lock:
        return _SESSION_CACHE.get(job_id)


def load_session_for_job(job_id: str) -> dict[str, Any] | None:
    """메모리 캐시 → 디스크 결과 순으로 세션 복원."""
    cached = get_session_from_cache(job_id)
    if cached:
        return cached

    data = load_job_result(job_id)
    if not data:
        return None

    from analysis import CurriculumReport, StageResult

    stages = [
        StageResult(
            stage=int(s["stage"]),
            title=s["title"],
            score=float(s["score"]),
            summary=s.get("summary", ""),
            coaching_blocks=[],
            details={},
        )
        for s in data.get("stage_summaries", [])
    ]
    report = CurriculumReport(
        audio_path=Path(data.get("audio_path") or ""),
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
    return {
        "report": report,
        "full_record": data.get("full_record") or {},
        "record_path": data.get("record_path"),
        "compare_text": data.get("compare_text", ""),
        "gpt_text": data.get("gpt_text", ""),
        "gpt_error": data.get("gpt_error"),
        "plot_path": data.get("plot_path") or "",
        "plot_error": data.get("plot_error"),
        "clip_paths": data.get("clip_paths") or [],
        "chart_path": data.get("chart_path"),
    }


def submit_analysis(
    audio_path: Path,
    *,
    song_title: str | None = None,
    use_youtube: bool = False,
    use_gpt: bool = False,
    save_record: bool = True,
    compare: bool = True,
    export_clips: bool = False,
    growth_chart: bool = False,
    fast_mode: bool = True,
    style_preset: str | None = None,
    user_id: str | None = None,
) -> str:
    """
    분석 작업 제출. job_id 반환.
    Celery 사용 시 USE_CELERY=1 환경변수.
    """
    if os.environ.get("USE_CELERY") == "1":
        return _submit_celery(
            audio_path,
            song_title=song_title,
            use_youtube=use_youtube,
            use_gpt=use_gpt,
            save_record=save_record,
            compare=compare,
            fast_mode=fast_mode,
            style_preset=style_preset,
        )

    job_id = uuid.uuid4().hex
    options = {
        "song_title": song_title,
        "use_youtube": use_youtube,
        "use_gpt": use_gpt,
        "save_record": save_record,
        "compare": compare,
        "export_clips": export_clips,
        "growth_chart": growth_chart,
        "fast_mode": fast_mode,
        "style_preset": style_preset,
        "user_id": user_id,
    }
    job = AnalysisJob(
        job_id=job_id,
        status=JobStatus.QUEUED,
        progress=0.0,
        message="큐에 등록됨…",
        created_at=_now_iso(),
        updated_at=_now_iso(),
        audio_path=str(audio_path),
        options=options,
    )
    _save_job(job)
    _executor.submit(_run_analysis_worker, job_id, Path(audio_path), options)
    return job_id


def _submit_celery(audio_path: Path, **options: Any) -> str:
    """Celery + Redis 배포용 (선택)."""
    try:
        from celery_tasks import analyze_audio_task  # type: ignore

        job_id = uuid.uuid4().hex
        job = AnalysisJob(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=_now_iso(),
            updated_at=_now_iso(),
            audio_path=str(audio_path),
            options=options,
        )
        _save_job(job)
        analyze_audio_task.delay(job_id, str(audio_path), options)
        return job_id
    except ImportError:
        options.pop("audio_path", None)
        return submit_analysis(audio_path, **options)


def list_recent_jobs(limit: int = 10) -> list[AnalysisJob]:
    if not QUEUE_DIR.exists():
        return []
    files = sorted(QUEUE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    jobs: list[AnalysisJob] = []
    for p in files[:limit]:
        if p.parent.name == "results":
            continue
        j = get_job(p.stem)
        if j:
            jobs.append(j)
    return jobs
