"""관리자 페이지 접근 제어."""

from __future__ import annotations

import os

import streamlit as st


def _secret_or_env(name: str) -> str | None:
    try:
        if name in st.secrets:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass
    value = os.environ.get(name, "").strip()
    return value or None


def admin_secret_configured() -> bool:
    secret = _secret_or_env("ADMIN_SECRET")
    return bool(secret and not secret.startswith("your-"))


def is_admin_authenticated() -> bool:
    return bool(st.session_state.get("admin_authenticated"))


def authenticate_admin(token: str) -> bool:
    secret = _secret_or_env("ADMIN_SECRET")
    if not secret or token.strip() != secret:
        return False
    st.session_state.admin_authenticated = True
    return True


def logout_admin() -> None:
    st.session_state.admin_authenticated = False


def try_admin_url_access() -> None:
    """?admin_token=SECRET → 관리자 페이지로 이동."""
    raw = st.query_params.get("admin_token")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if not raw:
        return
    if authenticate_admin(str(raw)):
        st.session_state.nav_page = "관리자"
        del st.query_params["admin_token"]
        st.rerun()
