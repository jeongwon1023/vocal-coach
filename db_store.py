"""Record storage — local JSON (guest) or Supabase (logged-in)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from progress_tracker import (
    default_record_path,
    list_records as list_local_records,
    load_record as load_local_record,
    save_record as save_local_record,
)


def _secret_or_env(name: str) -> str | None:
    try:
        import streamlit as st

        if name in st.secrets:
            value = str(st.secrets[name]).strip().strip('"').strip("'")
            if value:
                return value
    except Exception:
        pass
    value = os.environ.get(name, "").strip().strip('"').strip("'")
    return value or None


def supabase_configured() -> bool:
    return bool(_secret_or_env("SUPABASE_URL") and _secret_or_env("SUPABASE_KEY"))


def _get_client():
    try:
        from gotrue._sync.storage import SyncMemoryStorage
        from ui.supabase_client import create_supabase_client
    except ImportError as exc:
        raise RuntimeError("pip install supabase") from exc
    url = _secret_or_env("SUPABASE_URL")
    key = _secret_or_env("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY required")
    return create_supabase_client(url, key, storage=SyncMemoryStorage())


def is_cloud_user(user_id: str | None) -> bool:
    """로그인 유저 — anon_* 게스트는 로컬만."""
    return bool(user_id and not str(user_id).startswith("anon_") and supabase_configured())


def _save_to_supabase(data: dict[str, Any], *, user_id: str) -> str | None:
    client = _get_client()
    recorded_at = data.get("recorded_at")
    row = {
        "user_id": user_id,
        "song_title": data.get("song_title"),
        "user_recording": data.get("user_recording"),
        "overall_score": data.get("overall_score"),
        "stage_scores": data.get("stage_scores"),
        "payload": data,
    }
    if recorded_at:
        row["recorded_at"] = recorded_at
    resp = client.table("analysis_records").insert(row).execute()
    if resp.data:
        return str(resp.data[0].get("id"))
    return None


def mirror_analysis_record(data: dict[str, Any], *, user_id: str) -> str | None:
    """로컬 저장 후 Supabase 미러 (게스트·레거시)."""
    if not supabase_configured():
        return None
    try:
        return _save_to_supabase(data, user_id=user_id)
    except Exception:
        return None


def save_analysis_record(
    data: dict[str, Any],
    *,
    user_id: str | None = None,
    path: Path | None = None,
) -> Path:
    """로그인 유저 → Supabase만 · 게스트 → 로컬 JSON."""
    if is_cloud_user(user_id):
        data = {**data, "user_id": user_id}
        cloud_id = _save_to_supabase(data, user_id=user_id or "")
        if cloud_id:
            data["_cloud_id"] = cloud_id
        return default_record_path(user_id)

    return save_local_record(data, path or default_record_path(user_id), user_id=user_id)


def list_analysis_records(limit: int = 20, *, user_id: str | None = None) -> list[dict[str, Any]]:
    """Supabase 우선 + 로컬 fallback."""
    if supabase_configured() and user_id:
        try:
            client = _get_client()
            resp = (
                client.table("analysis_records")
                .select("*")
                .eq("user_id", user_id)
                .order("recorded_at", desc=True)
                .limit(limit)
                .execute()
            )
            out: list[dict[str, Any]] = []
            for row in resp.data or []:
                payload = row.get("payload") or {}
                merged = {**payload}
                merged.setdefault("recorded_at", row.get("recorded_at"))
                merged.setdefault("overall_score", row.get("overall_score"))
                merged["_storage_id"] = row.get("id")
                merged["_source"] = "supabase"
                out.append(merged)
            if out:
                return out
        except Exception:
            pass

    result: list[dict[str, Any]] = []
    for p in list_local_records(limit=limit, user_id=user_id):
        try:
            r = load_local_record(p)
            r["_storage_id"] = p.name
            r["_local_path"] = str(p)
            r["_source"] = "local"
            result.append(r)
        except Exception:
            continue
    return result


def cloud_record_count(user_id: str) -> int | None:
    if not supabase_configured() or not user_id:
        return None
    try:
        client = _get_client()
        resp = (
            client.table("analysis_records")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        return int(resp.count or 0)
    except Exception:
        return None


def storage_mode() -> str:
    return "supabase" if supabase_configured() else "local"
