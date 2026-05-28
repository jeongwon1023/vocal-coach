"""월간 분석 사용량 — 베타 한도."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from progress_tracker import load_record, user_records_dir

DEFAULT_MONTHLY_LIMIT = int(os.environ.get("VC_MONTHLY_ANALYSIS_LIMIT", "30"))


def _month_key(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc).astimezone()
    return dt.strftime("%Y-%m")


def count_analyses_this_month(user_id: str | None = None) -> int:
    d = user_records_dir(user_id)
    if not d.exists():
        return 0
    month = _month_key()
    count = 0
    for path in d.glob("record_*.json"):
        try:
            rec = load_record(path)
            ts = rec.get("recorded_at") or ""
            if ts[:7] == month:
                count += 1
        except Exception:
            continue
    return count


def check_analysis_allowed(user_id: str | None = None) -> tuple[bool, str, int, int]:
    """(allowed, message, used, limit)"""
    limit = DEFAULT_MONTHLY_LIMIT
    if limit <= 0:
        return True, "", 0, 0
    used = count_analyses_this_month(user_id)
    if used >= limit:
        return (
            False,
            f"이번 달 분석 한도({limit}회)에 도달했어요. 다음 달에 다시 이용해 주세요.",
            used,
            limit,
        )
    remaining = limit - used
    return True, f"이번 달 남은 분석 {remaining}회 / {limit}회", used, limit
