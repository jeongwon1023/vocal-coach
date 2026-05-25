"""
Celery 워커 태스크 (선택 — USE_CELERY=1 + Redis).

로컬 개발: analysis_queue.py 스레드 큐 사용 (기본).
배포: celery -A celery_tasks worker --loglevel=info
"""

from __future__ import annotations

import os

try:
    from celery import Celery
except ImportError:
    Celery = None  # type: ignore

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

if Celery is not None:
    app = Celery("vocal_coach", broker=REDIS_URL, backend=REDIS_URL)

    @app.task(name="analyze_audio")
    def analyze_audio_task(job_id: str, audio_path: str, options: dict) -> None:
        from pathlib import Path

        from analysis_queue import _run_analysis_worker

        _run_analysis_worker(job_id, Path(audio_path), options)
else:
    app = None
