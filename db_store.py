"""
Record storage — local JSON (default) or Supabase (Phase 2).

Set SUPABASE_URL + SUPABASE_KEY in .env or Streamlit secrets to enable cloud.
Requires: pip install supabase (optional)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from progress_tracker import (
    RECORDS_DIR,
    build_full_record,
    default_record_path,
    list_records as list_local_records,
    load_record as load_local_record,
    save_record as save_local_record,
)


def _supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"))


def _get_client():
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("pip install supabase") from exc
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def mirror_analysis_record(data: dict[str, Any], *, user_id: str) -> str | None:
    """로컬 저장 후 Supabase에 미러 (설정된 경우만)."""
    if not _supabase_configured():
        return None
    try:
        client = _get_client()
        row = {
            "user_id": user_id,
            "song_title": data.get("song_title"),
            "user_recording": data.get("user_recording"),
            "overall_score": data.get("overall_score"),
            "stage_scores": data.get("stage_scores"),
            "payload": data,
        }
        resp = client.table("analysis_records").insert(row).execute()
        if resp.data:
            return str(resp.data[0].get("id"))
    except Exception:
        return None
    return None


def save_analysis_record(
    data: dict[str, Any],
    *,
    user_id: str | None = None,
    path: Path | None = None,
) -> Path | str:
    """Save record locally; Supabase는 mirror_analysis_record 사용."""
    return save_local_record(data, path or default_record_path(user_id))


def list_analysis_records(limit: int = 20, *, user_id: str | None = None) -> list[dict[str, Any]]:
    """List records as dicts with id + payload fields."""
    if _supabase_configured() and user_id:
        client = _get_client()
        resp = (
            client.table("analysis_records")
            .select("*")
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        out = []
        for row in resp.data or []:
            payload = row.get("payload") or {}
            payload["_storage_id"] = row.get("id")
            payload["_source"] = "supabase"
            out.append(payload)
        return out

    result = []
    for p in list_local_records(limit=limit):
        try:
            r = load_local_record(p)
            r["_storage_id"] = p.name
            r["_source"] = "local"
            result.append(r)
        except Exception:
            continue
    return result


def storage_mode() -> str:
    return "supabase" if _supabase_configured() else "local"
