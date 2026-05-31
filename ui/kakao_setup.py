"""카카오 OAuth URL 생성 · KOE006 진단."""

from __future__ import annotations

import urllib.parse

import streamlit as st

from auth_service import kakao_redirect_uri, kakao_required_redirect_uris, streamlit_url
from ui.utils import render_safe_html

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
_KAKAO_OAUTH_STATE = "vc_kakao"


def extract_redirect_uri_from_auth_url(auth_url: str) -> str:
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query)
        values = qs.get("redirect_uri") or []
        return urllib.parse.unquote(values[0]) if values else ""
    except Exception:
        return ""


def extract_client_id_from_auth_url(auth_url: str) -> str:
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query)
        values = qs.get("client_id") or []
        return values[0] if values else ""
    except Exception:
        return ""


def build_kakao_direct_authorize_url(*, client_id: str) -> str:
    redirect = kakao_redirect_uri().rstrip("/")
    params = {
        "client_id": client_id.strip(),
        "redirect_uri": redirect,
        "response_type": "code",
        "state": _KAKAO_OAUTH_STATE,
    }
    return KAKAO_AUTH_URL + "?" + urllib.parse.urlencode(params)


def render_koe006_fix_panel(*, redirect_uri: str | None = None) -> None:
    """KOE006 — Redirect URI 미등록 안내."""
    uri = (redirect_uri or kakao_redirect_uri()).rstrip("/")
    required = kakao_required_redirect_uris()

    st.error(
        "**KOE006** — 카카오에 등록되지 않은 Redirect URI입니다.\n\n"
        "아래 URI를 **REST API 키 → 리다이렉트 URI**에 **모두** 추가하세요."
    )
    st.code(uri, language=None)

    st.markdown("**REST API 키에 등록해야 할 URI (2줄)**")
    for item in required:
        if item.startswith("http://localhost"):
            continue
        st.code(item, language=None)

    st.markdown(
        "**등록 위치**\n"
        "1. [Kakao Developers](https://developers.kakao.com/) → vocal coach ai\n"
        "2. **앱 → 플랫폼 키 → REST API 키** 클릭 → **리다이렉트 URI** 추가\n"
        "3. **저장** 후 Streamlit **Reboot app**"
    )

    st.caption(
        "Supabase 경유 로그인을 쓰는 경우 `supabase.co/auth/v1/callback` URI도 "
        "반드시 등록해야 KOE006이 사라집니다."
    )


def render_oauth_redirect_debug(auth_url: str, *, mode: str = "direct") -> None:
    """리다이렉트 직전 — 실제 요청 파라미터 표시."""
    uri = extract_redirect_uri_from_auth_url(auth_url) or kakao_redirect_uri()
    client_id = extract_client_id_from_auth_url(auth_url)

    st.warning(
        f"**OAuth 모드:** `{mode}` · **client_id:** `{client_id[:8]}...` "
        f"· **redirect_uri:** `{uri}`"
    )
    st.markdown("카카오 REST API 키 → 리다이렉트 URI에 **아래 두 줄** 모두 있는지 확인:")
    for item in kakao_required_redirect_uris():
        if item.startswith("http://localhost"):
            continue
        st.code(item, language=None)

    with st.expander("전체 OAuth URL (개발자용)", expanded=False):
        st.code(auth_url, language=None)


def render_kakao_debug_banner() -> None:
    """?kakao_debug=1 — Secrets · redirect URI 진단."""
    from ui.auth import _secret_or_env, get_auth_config_status, kakao_direct_configured

    st.subheader("카카오 OAuth 진단")
    status = get_auth_config_status()
    st.json(status)

    key = _secret_or_env("KAKAO_REST_API_KEY") or ""
    st.markdown(f"- **KAKAO_REST_API_KEY:** {'✅ ' + key[:8] + '...' if key else '❌ 없음'}")
    st.markdown(f"- **직접 OAuth:** {'✅' if kakao_direct_configured() else '❌ (Supabase 경유 → KOE006 가능)'}")
    st.markdown(f"- **redirect_uri:** `{kakao_redirect_uri()}`")

    st.markdown("**카카오 REST API 키에 등록할 URI:**")
    for item in kakao_required_redirect_uris():
        st.code(item, language=None)

    if key and kakao_direct_configured():
        url = build_kakao_direct_authorize_url(client_id=key)
        st.link_button("🔗 카카오 로그인 테스트 (직접 URL)", url)
