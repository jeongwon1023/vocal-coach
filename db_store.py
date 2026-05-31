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


def _extract_vocal_mbti(data: dict[str, Any]) -> str:
    title = data.get("vocal_title") or data.get("vocal_mbti")
    if title:
        return str(title)
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    return str(payload.get("vocal_title") or payload.get("vocal_mbti") or "")


def _extract_coaching_text(data: dict[str, Any]) -> str:
    for key in ("coaching_text", "gpt_text"):
        if data.get(key):
            return str(data[key])[:4000]
    actions = data.get("priority_actions")
    if isinstance(actions, list) and actions:
        lines = []
        for item in actions[:5]:
            if isinstance(item, dict):
                lines.append(str(item.get("title") or item.get("action") or item))
            else:
                lines.append(str(item))
        return "\n".join(lines)
    return ""


def _build_db_row(data: dict[str, Any], *, user_id: str) -> dict[str, Any]:
    vocal_mbti = _extract_vocal_mbti(data)
    coaching_text = _extract_coaching_text(data)
    payload = {
        **data,
        "user_id": user_id,
        "vocal_mbti": vocal_mbti,
        "coaching_text": coaching_text,
    }
    row: dict[str, Any] = {
        "user_id": user_id,
        "song_title": data.get("song_title"),
        "user_recording": data.get("user_recording"),
        "overall_score": data.get("overall_score"),
        "stage_scores": data.get("stage_scores"),
        "payload": payload,
    }
    recorded_at = data.get("recorded_at")
    if recorded_at:
        row["recorded_at"] = recorded_at
    return row


def _save_to_supabase(data: dict[str, Any], *, user_id: str) -> str | None:
    client = _get_client()
    row = _build_db_row(data, user_id=user_id)
    resp = client.table("analysis_records").insert(row).execute()
    if resp.data:
        return str(resp.data[0].get("id"))
    return None


def _record_exists_for_user(user_id: str, recorded_at: str | None) -> bool:
    if not recorded_at or not supabase_configured():
        return False
    try:
        client = _get_client()
        resp = (
            client.table("analysis_records")
            .select("id")
            .eq("user_id", user_id)
            .eq("recorded_at", recorded_at)
            .limit(1)
            .execute()
        )
        return bool(resp.data)
    except Exception:
        return False


def upsert_analysis_record(data: dict[str, Any], *, user_id: str) -> str | None:
    """analysis_records — recorded_at 기준 중복 방지 upsert."""
    recorded_at = data.get("recorded_at")
    if recorded_at and _record_exists_for_user(user_id, recorded_at):
        return None
    payload = {**data, "user_id": user_id}
    return _save_to_supabase(payload, user_id=user_id)


def sync_guest_records_to_user(*, anon_id: str, user_id: str) -> int:
    """게스트(anon_*) 로컬 JSON → Supabase analysis_records 동기화."""
    if not anon_id or not user_id or not str(anon_id).startswith("anon_"):
        return 0
    if not supabase_configured():
        return 0

    synced = 0
    for path in list_local_records(limit=50, user_id=anon_id):
        try:
            record = load_local_record(path)
            record = {**record, "user_id": user_id, "migrated_from": anon_id}
            if upsert_analysis_record(record, user_id=user_id):
                synced += 1
        except Exception:
            continue
    return synced


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
                merged.setdefault("vocal_mbti", payload.get("vocal_mbti") or payload.get("vocal_title"))
                merged.setdefault("coaching_text", payload.get("coaching_text") or payload.get("gpt_text"))
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
