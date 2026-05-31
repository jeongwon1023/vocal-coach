"""Supabase Auth 스토리지 — PKCE code_verifier 디스크 영속 (Streamlit 리다이렉트 대응)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

try:
    from gotrue._sync.storage import SyncSupportedStorage
except ImportError:
    SyncSupportedStorage = object  # type: ignore[misc, assignment]

PROJECT_DIR = Path(__file__).resolve().parent.parent
AUTH_CACHE_DIR = PROJECT_DIR / ".cache" / "supabase_auth"

_SESSION_KEY = "supabase_auth_storage"


def _safe_filename(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]


class PersistentAuthStorage(SyncSupportedStorage):
    """
    OAuth PKCE code_verifier 등을 session_state + 디스크에 이중 저장.

    Streamlit은 카카오/Supabase 리다이렉트 후 session_state가 초기화되므로
    디스크에서 verifier를 복원해야 exchange_code_for_session 이 성공합니다.
    """

    def _mem(self) -> dict[str, str]:
        if _SESSION_KEY not in st.session_state:
            st.session_state[_SESSION_KEY] = {}
        return st.session_state[_SESSION_KEY]

    def _path(self, key: str) -> Path:
        return AUTH_CACHE_DIR / f"{_safe_filename(key)}.txt"

    def get_item(self, key: str) -> str | None:
        mem = self._mem()
        if key in mem:
            return mem[key]
        path = self._path(key)
        if path.exists():
            try:
                value = path.read_text(encoding="utf-8")
                mem[key] = value
                return value
            except Exception:
                return None
        return None

    def set_item(self, key: str, value: str) -> None:
        self._mem()[key] = value
        AUTH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(value, encoding="utf-8")

    def remove_item(self, key: str) -> None:
        self._mem().pop(key, None)
        path = self._path(key)
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass


def clear_auth_cache_files() -> None:
    """OAuth 성공/실패 후 PKCE 임시 파일 정리."""
    if not AUTH_CACHE_DIR.exists():
        return
    for path in AUTH_CACHE_DIR.glob("*.txt"):
        try:
            path.unlink()
        except Exception:
            pass
    st.session_state.pop(_SESSION_KEY, None)
