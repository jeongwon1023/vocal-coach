"""Record storage — Supabase cloud + graceful local/JSONL fallback."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from progress_tracker import (
    PROJECT_DIR,
    default_record_path,
    list_records as list_local_records,
    load_record as load_local_record,
    save_record as save_local_record,
)

BACKUP_JSONL = PROJECT_DIR / "records" / "backup_records.jsonl"
_PRIMARY_TABLE = "analysis_records"
_FALLBACK_TABLE = "user_records"


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


def _log_db_error(
    message: str,
    *,
    exc: BaseException | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """UI 노출 없이 error_logs에만 기록."""
    try:
        from ui.error_guard import log_error

        log_error(message, source="db_store", exc=exc, extra=extra or {})
    except Exception:
        pass


def _append_backup_record(
    data: dict[str, Any],
    *,
    user_id: str,
    reason: str,
) -> None:
    """클라우드 실패 시 records/backup_records.jsonl 에 백업."""
    try:
        BACKUP_JSONL.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user_id": user_id,
            "reason": reason,
            "record": data,
        }
        with BACKUP_JSONL.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        _log_db_error("JSONL 백업 실패", exc=exc)


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


def _build_analysis_records_row(data: dict[str, Any], *, user_id: str) -> dict[str, Any]:
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


def _build_user_records_row(data: dict[str, Any], *, user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "vocal_mbti": _extract_vocal_mbti(data),
        "score_json": data.get("stage_scores") or {},
        "coaching_text": _extract_coaching_text(data),
    }


def _insert_table(client: Any, table: str, row: dict[str, Any]) -> str | None:
    resp = client.table(table).insert(row).execute()
    if resp.data:
        first = resp.data[0]
        return str(first.get("id") or first.get("user_id") or table)
    return None


def _save_to_supabase(data: dict[str, Any], *, user_id: str) -> str | None:
    """
    Supabase 저장 — analysis_records 우선, user_records fallback.
    실패 시 JSONL 백업 + None (예외를 UI로 전파하지 않음).
    """
    if not supabase_configured():
        return None

    try:
        client = _get_client()
    except Exception as exc:
        _log_db_error("Supabase 클라이언트 생성 실패", exc=exc)
        _append_backup_record(data, user_id=user_id, reason="client_init_failed")
        return None

    errors: list[str] = []

    try:
        row = _build_analysis_records_row(data, user_id=user_id)
        cloud_id = _insert_table(client, _PRIMARY_TABLE, row)
        if cloud_id:
            return cloud_id
    except Exception as exc:
        errors.append(f"{_PRIMARY_TABLE}: {exc}")
        _log_db_error(
            f"Supabase {_PRIMARY_TABLE} insert 실패",
            exc=exc,
            extra={"user_id": user_id},
        )

    try:
        ur_row = _build_user_records_row(data, user_id=user_id)
        cloud_id = _insert_table(client, _FALLBACK_TABLE, ur_row)
        if cloud_id:
            return cloud_id
    except Exception as exc:
        errors.append(f"{_FALLBACK_TABLE}: {exc}")
        _log_db_error(
            f"Supabase {_FALLBACK_TABLE} insert 실패",
            exc=exc,
            extra={"user_id": user_id, "prior_errors": errors},
        )

    _append_backup_record(
        data,
        user_id=user_id,
        reason="; ".join(errors) if errors else "cloud_insert_failed",
    )
    return None


def _record_exists_for_user(user_id: str, recorded_at: str | None) -> bool:
    if not recorded_at or not supabase_configured():
        return False
    try:
        client = _get_client()
        resp = (
            client.table(_PRIMARY_TABLE)
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
    """analysis_records — recorded_at 기준 중복 방지."""
    recorded_at = data.get("recorded_at")
    if recorded_at and _record_exists_for_user(user_id, recorded_at):
        return None
    payload = {**data, "user_id": user_id}
    return _save_to_supabase(payload, user_id=user_id)


def sync_guest_records_to_user(*, anon_id: str, user_id: str) -> int:
    """게스트 로컬 JSON → Supabase 동기화 (실패해도 크래시 없음)."""
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
        except Exception as exc:
            _log_db_error("게스트 기록 동기화 항목 실패", exc=exc, extra={"path": str(path)})
            continue
    return synced


def mirror_analysis_record(data: dict[str, Any], *, user_id: str) -> str | None:
    if not supabase_configured():
        return None
    return _save_to_supabase(data, user_id=user_id)


def save_analysis_record(
    data: dict[str, Any],
    *,
    user_id: str | None = None,
    path: Path | None = None,
) -> Path:
    """
    로그인 유저 → Supabase 우선.
    클라우드 실패 시 JSONL 백업 + 로컬 JSON (유저 화면은 정상 진행).
    """
    local_path = path or default_record_path(user_id)

    if is_cloud_user(user_id):
        payload = {**data, "user_id": user_id}
        cloud_id = _save_to_supabase(payload, user_id=user_id or "")
        if cloud_id:
            payload["_cloud_id"] = cloud_id
            try:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
            return local_path

        _log_db_error(
            "클라우드 저장 실패 — 로컬 JSON fallback",
            extra={"user_id": user_id},
        )
        return save_local_record(payload, local_path, user_id=user_id)

    return save_local_record(data, local_path, user_id=user_id)


def _merge_row_from_analysis_table(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") or {}
    merged = {**payload} if isinstance(payload, dict) else {}
    merged.setdefault("recorded_at", row.get("recorded_at") or row.get("created_at"))
    merged.setdefault("overall_score", row.get("overall_score"))
    merged.setdefault("vocal_mbti", payload.get("vocal_mbti") or payload.get("vocal_title"))
    merged.setdefault("coaching_text", payload.get("coaching_text") or payload.get("gpt_text"))
    merged["_storage_id"] = row.get("id")
    merged["_source"] = "supabase"
    return merged


def _merge_row_from_user_records(row: dict[str, Any]) -> dict[str, Any]:
    scores = row.get("score_json") or {}
    return {
        "recorded_at": row.get("created_at"),
        "overall_score": scores.get("overall") if isinstance(scores, dict) else None,
        "stage_scores": scores,
        "vocal_mbti": row.get("vocal_mbti"),
        "coaching_text": row.get("coaching_text"),
        "_storage_id": row.get("id"),
        "_source": "supabase_user_records",
    }


def list_analysis_records(limit: int = 20, *, user_id: str | None = None) -> list[dict[str, Any]]:
    """Supabase 우선 + 로컬 fallback (DB 오류 시 크래시 없음)."""
    if supabase_configured() and user_id:
        try:
            client = _get_client()
            resp = (
                client.table(_PRIMARY_TABLE)
                .select("*")
                .eq("user_id", user_id)
                .order("recorded_at", desc=True)
                .limit(limit)
                .execute()
            )
            out = [_merge_row_from_analysis_table(row) for row in (resp.data or [])]
            if out:
                return out
        except Exception as exc:
            _log_db_error(f"{_PRIMARY_TABLE} select 실패", exc=exc, extra={"user_id": user_id})

        try:
            client = _get_client()
            resp = (
                client.table(_FALLBACK_TABLE)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            out = [_merge_row_from_user_records(row) for row in (resp.data or [])]
            if out:
                return out
        except Exception as exc:
            _log_db_error(f"{_FALLBACK_TABLE} select 실패", exc=exc, extra={"user_id": user_id})

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
    total = 0
    try:
        client = _get_client()
        resp = (
            client.table(_PRIMARY_TABLE)
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        total += int(resp.count or 0)
    except Exception:
        pass
    try:
        client = _get_client()
        resp = (
            client.table(_FALLBACK_TABLE)
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        total += int(resp.count or 0)
    except Exception:
        pass
    return total if total else None


def storage_mode() -> str:
    return "supabase" if supabase_configured() else "local"
