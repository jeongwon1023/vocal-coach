"""유저 세션 정규화 — 'authenticated' 등 디버그/날것 텍스트 노출 차단."""

from __future__ import annotations

import streamlit as st

_BLOCKED_NAMES = frozenset(
    {"authenticated", "anon", "user", "unknown", "null", "none", ""}
)


def safe_nickname(user: dict | None = None) -> str:
    """닉네임 — 절대 'authenticated' 등 시스템 문자열 노출 금지."""
    if user is None:
        user = st.session_state.get("user")
    if not user or not isinstance(user, dict):
        return "보컬러"

    for key in ("name", "nickname", "display_name"):
        val = user.get(key)
        if val and isinstance(val, str):
            cleaned = val.strip()
            if cleaned.lower() not in _BLOCKED_NAMES:
                return cleaned

    meta = user.get("user_metadata")
    if isinstance(meta, dict):
        for key in ("name", "nickname", "full_name", "preferred_username"):
            val = meta.get(key)
            if val and isinstance(val, str):
                cleaned = str(val).strip()
                if cleaned.lower() not in _BLOCKED_NAMES:
                    return cleaned

    email = user.get("email")
    if email and isinstance(email, str) and "@" in email:
        return email.split("@")[0]

    return "보컬러"


def normalize_session_user() -> None:
    """st.session_state.user — dict 아닌 값 / 날것 name 제거."""
    raw = st.session_state.get("user")
    if raw is None:
        return
    if not isinstance(raw, dict):
        st.session_state.user = None
        return

    name = raw.get("name")
    if name is not None and str(name).strip().lower() in _BLOCKED_NAMES:
        raw["name"] = safe_nickname(raw)

    provider = raw.get("provider")
    if provider is not None and str(provider).strip().lower() in _BLOCKED_NAMES:
        raw.pop("provider", None)
