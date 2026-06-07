"""브라우저 새로고침 후 로그인 유지 — 앱 세션 쿠키."""

from __future__ import annotations

import json

import streamlit as st

_AUTH_COOKIE = "vc_auth_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30일


def read_auth_cookie() -> str | None:
    try:
        token = st.context.cookies.get(_AUTH_COOKIE)
        if token and isinstance(token, str) and len(token) >= 16:
            return token.strip()
    except Exception:
        pass
    return None


def persist_auth_cookie(token: str) -> None:
    """로그인 성공 시 브라우저 쿠키에 앱 세션 토큰 저장."""
    if not token:
        return
    if st.session_state.get("_auth_cookie_set") == token:
        return
    import streamlit.components.v1 as components

    safe = json.dumps(token)
    components.html(
        f"""<script>
        document.cookie = {_AUTH_COOKIE} + "=" + encodeURIComponent({safe}) +
            "; path=/; max-age={_COOKIE_MAX_AGE}; SameSite=Lax" +
            (location.protocol === "https:" ? "; Secure" : "");
        </script>""",
        height=0,
        width=0,
    )
    st.session_state["_auth_cookie_set"] = token


def clear_auth_cookie() -> None:
    import streamlit.components.v1 as components

    components.html(
        f"""<script>
        document.cookie = "{_AUTH_COOKIE}=; path=/; max-age=0; SameSite=Lax";
        </script>""",
        height=0,
        width=0,
    )
    st.session_state.pop("_auth_cookie_set", None)
