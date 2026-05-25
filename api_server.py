"""
모바일·외부 클라이언트용 REST API (FastAPI)

실행:
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    또는 run_api.bat

엔드포인트:
    POST /analyze           — 동기 분석 (즉시 JSON)
    POST /analyze/async     — 비동기 분석 (job_id 반환)
    GET  /jobs/{job_id}     — 작업 상태·결과
    POST /feedback          — 점수 일치 피드백
    GET  /records           — 저장된 기록 목록
    GET  /records/{name}    — 기록 상세
    GET  /health            — 상태 확인
"""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from analysis import run_full_session  # noqa: E402
from analysis_queue import JobStatus, get_job, load_job_result, submit_analysis  # noqa: E402
from progress_tracker import list_records, load_record  # noqa: E402

UPLOAD_DIR = PROJECT_DIR / ".cache" / "api_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Vocal Coach API",
    description="보컬 코칭 분석 API — 모바일 앱(Expo) 연동용",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeOptions(BaseModel):
    song_title: str | None = None
    use_gpt: bool = False
    save_record: bool = True
    compare: bool = True
    export_clips: bool = False
    style_preset: str = "auto"
    fast_mode: bool = True


class FeedbackBody(BaseModel):
    agrees: bool
    record_id: str | None = None
    overall_score: float | None = None
    song_title: str | None = None
    style_preset: str | None = None
    comment: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="1.1.0")


@app.get("/records")
def get_records(limit: int = 20) -> list[dict[str, Any]]:
    result = []
    for p in list_records(limit=limit):
        try:
            r = load_record(p)
            result.append({
                "id": p.name,
                "recorded_at": r.get("recorded_at"),
                "song_title": r.get("song_title"),
                "overall_score": r.get("overall_score"),
                "stage_scores": r.get("stage_scores"),
            })
        except Exception:
            continue
    return result


@app.get("/records/{record_id}")
def get_record(record_id: str) -> dict[str, Any]:
    path = PROJECT_DIR / "records" / record_id
    if not path.exists() or not record_id.startswith("record_"):
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return load_record(path)


@app.post("/feedback")
def post_feedback(body: FeedbackBody) -> dict[str, Any]:
    from feedback_store import save_feedback

    path = save_feedback(
        agrees=body.agrees,
        record_id=body.record_id,
        overall_score=body.overall_score,
        song_title=body.song_title,
        style_preset=body.style_preset,
        comment=body.comment,
    )
    return {"ok": True, "path": str(path)}


def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    from audio_normalize import ensure_normalized

    return ensure_normalized(dest)


@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    song_title: str | None = None,
    use_gpt: bool = False,
    save_record: bool = True,
    compare: bool = True,
    style_preset: str = "auto",
    fast_mode: bool = True,
) -> dict[str, Any]:
    dest = _save_upload(file)
    try:
        session = run_full_session(
            dest,
            song_title=song_title,
            use_gpt=use_gpt,
            save_record=save_record,
            compare=compare,
            export_clips=False,
            growth_chart=save_record,
            save_plot=PROJECT_DIR / "pitch_result.png",
            style_preset=style_preset,
            fast_mode=fast_mode,
        )
        report = session["report"]
        return {
            "ok": True,
            "overall_score": report.overall_score,
            "stage_scores": session["full_record"].get("stage_scores"),
            "style_preset": report.style_preset_id,
            "reference_source": report.reference_source,
            "mr_likely": report.mr_likely,
            "mr_message": report.mr_message,
            "record": session["full_record"],
            "record_path": str(session["record_path"]) if session.get("record_path") else None,
            "compare_text": session.get("compare_text", ""),
            "gpt_text": session.get("gpt_text", ""),
            "gpt_error": session.get("gpt_error"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze/async")
async def analyze_async(
    file: UploadFile = File(...),
    song_title: str | None = None,
    use_gpt: bool = False,
    save_record: bool = True,
    style_preset: str = "auto",
    fast_mode: bool = True,
) -> dict[str, Any]:
    dest = _save_upload(file)
    job_id = submit_analysis(
        dest,
        song_title=song_title,
        use_gpt=use_gpt,
        save_record=save_record,
        compare=True,
        style_preset=style_preset,
        fast_mode=fast_mode,
    )
    return {"ok": True, "job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    out: dict[str, Any] = {
        "job_id": job.job_id,
        "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
        "progress": job.progress,
        "message": job.message,
        "error": job.error,
    }
    if job.status == JobStatus.DONE:
        result = load_job_result(job_id)
        if result:
            out["result"] = result
    return out


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
