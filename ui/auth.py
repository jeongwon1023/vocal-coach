"""로그인 · 회원가입 UI (Supabase Kakao · Google · 체험)."""

from __future__ import annotations

import html
import os
import urllib.parse
from typing import Any

import streamlit as st

from auth_service import (
    auth_base_url,
    create_demo_user,
    create_session,
    delete_session,
    find_or_create_oauth_user,
    google_configured,
    kakao_configured,
    resolve_session,
    streamlit_url,
)
from ui.runtime_env import is_streamlit_cloud
from ui.utils import render_safe_html

try:
    from gotrue._sync.storage import SyncSupportedStorage

    _SUPABASE_IMPORT_OK = True
except ImportError:
    _SUPABASE_IMPORT_OK = False
    SyncSupportedStorage = object  # type: ignore[misc, assignment]

from ui.supabase_client import create_supabase_client, is_supabase_key_format

_KAKAO_OAUTH_STATE = "vc_kakao"
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


class _StreamlitAuthStorage(SyncSupportedStorage):
    """PKCE code_verifier · Supabase 세션을 st.session_state에 유지."""

    _KEY = "supabase_auth_storage"

    def _store(self) -> dict[str, str]:
        if self._KEY not in st.session_state:
            st.session_state[self._KEY] = {}
        return st.session_state[self._KEY]

    def get_item(self, key: str) -> str | None:
        return self._store().get(key)

    def set_item(self, key: str, value: str) -> None:
        self._store()[key] = value

    def remove_item(self, key: str) -> None:
        self._store().pop(key, None)


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


def supabase_configured() -> bool:
    url = _secret_or_env("SUPABASE_URL")
    key = _secret_or_env("SUPABASE_KEY")
    return bool(_SUPABASE_IMPORT_OK and url and key and is_supabase_key_format(key or ""))


def kakao_direct_configured() -> bool:
    """Streamlit 직접 카카오 OAuth (Supabase Auth KOE205/account_email 우회)."""
    key = _secret_or_env("KAKAO_REST_API_KEY")
    return bool(key and len(key) >= 20 and not key.startswith("your-"))


def kakao_login_available() -> bool:
    return kakao_direct_configured() or supabase_configured()


def get_auth_config_status() -> dict[str, Any]:
    """디버그용 — Supabase/카카오 등록 상태 (키 값은 노출하지 않음)."""
    url = _secret_or_env("SUPABASE_URL")
    key = _secret_or_env("SUPABASE_KEY")
    return {
        "supabase_package": _SUPABASE_IMPORT_OK,
        "supabase_url_set": bool(url),
        "supabase_key_set": bool(key),
        "supabase_key_valid_format": bool(key and is_supabase_key_format(key)),
        "supabase_ready": supabase_configured(),
        "kakao_direct": kakao_direct_configured(),
        "kakao_login_available": kakao_login_available(),
        "legacy_kakao_env": kakao_configured(),
        "redirect_url": streamlit_url(),
    }


def get_supabase_client() -> Any | None:
    """st.secrets 기반 Supabase 클라이언트 (세션 스토리지 = session_state)."""
    if not supabase_configured():
        return None
    url = _secret_or_env("SUPABASE_URL")
    key = _secret_or_env("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        return create_supabase_client(url, key, storage=_StreamlitAuthStorage())
    except Exception:
        return None


def _oauth_unconfigured_hint(provider: str) -> str:
    if is_streamlit_cloud():
        return f"{provider}: 베타 — **체험 계정**으로 이용해 주세요"
    return f"{provider}: OAuth 미설정 (로컬 .env / secrets.toml 참고)"


def _user_from_supabase_session(session: Any) -> dict[str, Any]:
    user = session.user
    meta = user.user_metadata or {}
    app_meta = user.app_metadata or {}
    provider = app_meta.get("provider") or "kakao"
    name = (
        meta.get("name")
        or meta.get("full_name")
        or meta.get("nickname")
        or meta.get("preferred_username")
        or user.email
        or "학습자"
    )
    return {
        "id": user.id,
        "name": name,
        "email": user.email,
        "provider": provider,
        "avatar_url": meta.get("avatar_url") or meta.get("picture"),
    }


def _apply_supabase_session(session: Any) -> None:
    st.session_state.user = _user_from_supabase_session(session)
    st.session_state.auth_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token


def render_pending_oauth_redirect() -> None:
    """다이얼로그/iframe 밖 최상위 창으로 OAuth 이동 (kauth.kakao.com iframe 차단 우회)."""
    url = st.session_state.pop("oauth_redirect_url", None)
    if not url:
        return

    import json

    import streamlit.components.v1 as components

    components.html(
        f"<script>window.top.location.href = {json.dumps(url)};</script>",
        height=0,
        width=0,
    )
    st.info("카카오 로그인 페이지로 이동 중...")
    safe = html.escape(url, quote=True)
    render_safe_html(
        f'<p style="text-align:center;margin:1rem 0;">'
        f'<a href="{safe}" target="_top" rel="noopener noreferrer" '
        f'style="display:inline-block;padding:12px 20px;background:#FEE500;'
        f'color:#191919;border-radius:8px;font-weight:700;text-decoration:none;">'
        f"💬 카카오 로그인 페이지로 이동</a></p>"
    )
    st.stop()


def init_auth() -> None:
    """URL ?token= / Supabase OAuth / 세션에서 사용자 복원."""
    render_pending_oauth_redirect()

    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user" not in st.session_state:
        st.session_state.user = None

    try:
        check_user_session()
    except Exception as exc:
        st.session_state["_auth_last_error"] = str(exc)

    qp = st.query_params
    token = qp.get("token")
    if isinstance(token, list):
        token = token[0] if token else None
    if token and isinstance(token, str):
        user = resolve_session(token)
        if user:
            st.session_state.auth_token = token
            st.session_state.user = user.to_dict()
            st.query_params.clear()
            st.rerun()

    if st.session_state.auth_token and not st.session_state.user:
        user = resolve_session(st.session_state.auth_token)
        if user:
            st.session_state.user = user.to_dict()
        else:
            st.session_state.auth_token = None


def is_logged_in() -> bool:
    return bool(st.session_state.get("user"))


def current_user() -> dict | None:
    return st.session_state.get("user")


def current_user_id() -> str | None:
    u = current_user()
    return u.get("id") if u else None


def logout() -> None:
    if supabase_configured():
        client = get_supabase_client()
        if client:
            try:
                client.auth.sign_out()
            except Exception:
                pass
        st.session_state.pop("supabase_auth_storage", None)
        st.session_state.pop("supabase_refresh_token", None)

    token = st.session_state.get("auth_token")
    if token and not supabase_configured():
        delete_session(token)
    st.session_state.auth_token = None
    st.session_state.user = None
    from ui.session_reset import reset_user_session_state

    reset_user_session_state()
    st.rerun()


def render_topbar_auth() -> None:
    """우측 상단 — 로그인 모달 또는 사용자 메뉴."""
    user = current_user()
    if user:
        name = user.get("name", "학습자")
        with st.popover(f"👤 {name}", use_container_width=False, key="top_auth_user"):
            _render_user_popover_body(user)
        return

    if st.button("로그인", key="top_auth_login_btn", use_container_width=False, type="secondary"):
        open_login_dialog(key_prefix="top_auth_dialog")


def render_menu_auth(*, key_prefix: str = "nav_menu") -> None:
    """모바일 햄버거 메뉴 안 — 계정 · 로그인."""
    user = current_user()
    if user:
        _render_user_popover_body(user, logout_key=f"{key_prefix}_logout")
        return

    st.caption("3초 만에 시작 · 기록 저장")
    if st.button("로그인 / 시작하기", key=f"{key_prefix}_login_btn", use_container_width=True):
        open_login_dialog(key_prefix=f"{key_prefix}_dialog")


def _render_user_popover_body(user: dict, *, logout_key: str = "btn_logout_top") -> None:
    name = user.get("name", "학습자")
    st.markdown(f"**{name}**")
    if user.get("email"):
        st.caption(user["email"])
    provider = {"google": "Google", "kakao": "카카오", "demo": "체험"}.get(
        user.get("provider", ""), ""
    )
    if provider:
        st.caption(f"연동: {provider}")
    if st.button("로그아웃", key=logout_key, use_container_width=True):
        logout()


def render_login_compact(*, key_prefix: str = "auth_pop") -> None:
    """다이얼로그/팝오버용 — 카카오 · Google · 체험."""
    from ui.auth_ui import render_auth_buttons

    st.caption("3초 만에 시작 · 기록 저장")
    render_auth_buttons(key_prefix=key_prefix, compact=True)


def _render_supabase_kakao_styles() -> None:
    render_safe_html(
        """
        <style>
        .st-key-supabase_kakao_login button,
        .st-key-page_supabase_kakao button,
        .st-key-landing_kakao button {
            width: 100% !important;
            background: #FEE500 !important;
            color: #191919 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            min-height: 48px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        }
        .st-key-supabase_kakao_login button:hover,
        .st-key-page_supabase_kakao button:hover,
        .st-key-landing_kakao button:hover {
            background: #f5dc00 !important;
            color: #191919 !important;
        }
        .vc-login-dialog-lead {
            margin: 0 0 1rem;
            font-size: 0.95rem;
            line-height: 1.55;
            color: #4b5563;
            text-align: center;
        }
        </style>
        <p class="vc-login-dialog-lead">내 보컬 분석 리포트를 저장하려면 로그인해 주세요.</p>
        """
    )


def _render_kakao_login_button(*, key: str) -> None:
    if st.button("💬 카카오로 계속하기", key=key, use_container_width=True):
        _start_kakao_oauth()


def _qp_first(value: str | list[str] | None) -> str | None:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _complete_kakao_direct_login(code: str) -> None:
    """카카오 authorization code → 앱 세션 (Supabase Auth 미사용)."""
    import httpx

    rest_key = _secret_or_env("KAKAO_REST_API_KEY")
    if not rest_key:
        st.session_state["_auth_last_error"] = "KAKAO_REST_API_KEY 없음"
        return

    redirect = streamlit_url()
    payload: dict[str, str] = {
        "grant_type": "authorization_code",
        "client_id": rest_key,
        "redirect_uri": redirect,
        "code": code,
    }
    secret = _secret_or_env("KAKAO_CLIENT_SECRET")
    if secret:
        payload["client_secret"] = secret

    token_resp = httpx.post(
        KAKAO_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if token_resp.status_code != 200:
        st.session_state["_auth_last_error"] = f"Kakao 토큰 교환 실패 ({token_resp.status_code})"
        return

    access = token_resp.json().get("access_token")
    if not access:
        st.session_state["_auth_last_error"] = "Kakao access_token 없음"
        return

    user_resp = httpx.get(
        KAKAO_USER_URL,
        headers={"Authorization": f"Bearer {access}"},
        timeout=15,
    )
    if user_resp.status_code != 200:
        st.session_state["_auth_last_error"] = f"Kakao 사용자 정보 실패 ({user_resp.status_code})"
        return

    info = user_resp.json()
    kakao_account = info.get("kakao_account") or {}
    profile = kakao_account.get("profile") or {}
    user = find_or_create_oauth_user(
        provider="kakao",
        provider_uid=str(info.get("id", "")),
        name=profile.get("nickname") or "카카오 사용자",
        email=kakao_account.get("email"),
        avatar_url=profile.get("profile_image_url"),
    )
    token = create_session(user.id)
    st.session_state.auth_token = token
    st.session_state.user = user.to_dict()


def _start_kakao_direct_oauth() -> None:
    """Supabase 경유 없이 카카오 OAuth (scope 미지정 → KOE205 방지)."""
    rest_key = _secret_or_env("KAKAO_REST_API_KEY")
    if not rest_key:
        st.error("KAKAO_REST_API_KEY가 Secrets에 없습니다.")
        return

    params = {
        "client_id": rest_key,
        "redirect_uri": streamlit_url(),
        "response_type": "code",
        "state": _KAKAO_OAUTH_STATE,
    }
    url = KAKAO_AUTH_URL + "?" + urllib.parse.urlencode(params)
    st.session_state["oauth_redirect_url"] = url
    st.rerun()


def _diagnose_kakao_auth() -> bool:
    if kakao_direct_configured():
        st.write("카카오 직접 로그인 준비 OK (이메일 scope 미요청)")
        st.caption(f"Redirect URI: {streamlit_url()}")
        return True
    return _diagnose_supabase_auth()


def _diagnose_supabase_auth() -> bool:
    """Supabase 연결 및 OAuth Provider 설정 확인."""
    import httpx

    st.write("Supabase 설정 확인 중...")
    status = get_auth_config_status()
    if not status["supabase_ready"]:
        st.error(
            "Secrets 확인: SUPABASE_URL · SUPABASE_KEY · STREAMLIT_URL "
            "(placeholder 키는 사용할 수 없습니다)"
        )
        st.json(status)
        return False

    url = _secret_or_env("SUPABASE_URL")
    key = _secret_or_env("SUPABASE_KEY")
    if not url or not key:
        st.error("SUPABASE_URL / SUPABASE_KEY가 Secrets에 없습니다.")
        return False

    resp = httpx.get(
        f"{url.rstrip('/')}/auth/v1/settings",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=10,
    )
    resp.raise_for_status()
    external = (resp.json().get("external") or {})
    enabled = sorted(name for name, on in external.items() if on)
    st.write(f"**연결 OK** · 활성 Provider: {', '.join(enabled) or '(없음)'}")

    if "kakao" not in enabled:
        st.error("Kakao Provider가 Supabase Dashboard에서 꺼져 있습니다.")
        return False

    st.caption(
        "KOE205 오류 시: Supabase Kakao → **Allow users without an email** ON · "
        "카카오 동의항목에서 닉네임/프로필만 켜기 (docs/kakao-oauth-setup.md)"
    )
    return True


def _start_kakao_oauth() -> None:
    try:
        if not _diagnose_kakao_auth():
            return
    except Exception as exc:
        st.error(f"설정 에러: {exc}")
        return

    if kakao_direct_configured():
        _start_kakao_direct_oauth()
        return

    client = get_supabase_client()
    if not client:
        st.error("Supabase 설정(SUPABASE_URL, SUPABASE_KEY)이 없습니다.")
        return
    try:
        response = client.auth.sign_in_with_oauth(
            {
                "provider": "kakao",
                "options": {
                    "redirect_to": streamlit_url(),
                    "scopes": "profile_nickname profile_image",
                },
            }
        )
    except Exception as exc:
        st.error(f"카카오 로그인을 시작하지 못했습니다: {exc}")
        return

    st.session_state["oauth_redirect_url"] = response.url
    st.rerun()


def _render_supabase_login_dialog(*, key_prefix: str) -> None:
    _render_supabase_kakao_styles()
    _render_kakao_login_button(key="supabase_kakao_login")

    st.caption("또는")
    if st.button("✦ 체험 계정으로 시작", key=f"{key_prefix}_demo", use_container_width=True):
        start_demo()


@st.dialog("3초 만에 시작하기", width="small")
def _show_login_dialog() -> None:
    prefix = st.session_state.get("_login_dialog_prefix", "dialog_auth")
    if kakao_login_available():
        _render_supabase_login_dialog(key_prefix=prefix)
        return

    from ui.auth_ui import render_login_card

    render_login_card(key_prefix=prefix, compact=True)
    st.caption("카카오 · Google · 체험 계정 중 선택하세요.")


def open_login_dialog(*, key_prefix: str = "dialog_auth") -> None:
    """화면 이동 없이 로그인 모달."""
    st.session_state["_login_dialog_prefix"] = key_prefix
    _show_login_dialog()


def render_sidebar_user() -> None:
    """(deprecated) — 상단 auth 사용."""
    pass


def start_demo() -> None:
    """체험 계정 로그인."""
    _start_demo()


def _start_demo() -> None:
    user = create_demo_user()
    token = create_session(user.id)
    st.session_state.auth_token = token
    st.session_state.user = user.to_dict()
    st.session_state.show_login = False
    st.rerun()


def render_login_page() -> None:
    """로그인 전용 화면 — 모달 또는 카드."""
    if st.button("🔐 로그인 / 체험 시작", type="primary", use_container_width=True, key="page_login_open"):
        open_login_dialog(key_prefix="page_login_dialog")
        return

    if kakao_login_available():
        _render_supabase_kakao_styles()
        _render_kakao_login_button(key="page_supabase_kakao")
        if st.button("✦ 체험 계정으로 시작", key="page_demo", use_container_width=True, type="primary"):
            start_demo()
        return

    from ui.auth_ui import render_login_card

    render_login_card(key_prefix="page_login")

    if not google_configured() and not kakao_configured():
        with st.expander("소셜 로그인 연동 방법 (선택)"):
            st.markdown(
                "1. `.env.example` → `.env` 복사\n\n"
                "2. **Google** — [Cloud Console](https://console.cloud.google.com/) OAuth 클라이언트  \n"
                "   리디렉션: `http://localhost:8001/auth/google/callback`\n\n"
                "3. **Kakao** — [developers.kakao.com](https://developers.kakao.com/) REST API 키  \n"
                "   Redirect: `http://localhost:8001/auth/kakao/callback`\n\n"
                "4. `run_web.bat` 재실행\n\n"
                "**지금은 「체험 계정」으로 모든 기능을 쓸 수 있어요.**"
            )


def require_login() -> bool:
    if is_logged_in():
        return True
    render_login_page()
    return False


def render_landing_auth_banner() -> None:
    """홈 랜딩 — 카카오 로그인 + 체험 CTA."""
    render_safe_html(
        """
        <div class="vc-landing-trial-banner">
            <div class="vc-landing-trial-copy">
                <span class="vc-landing-trial-tag">무료 체험</span>
                <p class="vc-landing-trial-title">가입 없이 바로 분석해 보세요</p>
                <p class="vc-landing-trial-sub">기록 저장은 <b>카카오 로그인</b> 또는 상단 <b>로그인</b> 메뉴</p>
            </div>
        </div>
        """
    )

    if kakao_login_available():
        _render_supabase_kakao_styles()
        _render_kakao_login_button(key="landing_kakao")
    else:
        st.caption(
            "카카오 로그인: Streamlit Secrets에 **KAKAO_REST_API_KEY** 추가 · "
            "카카오 Redirect URI에 앱 URL 등록 (docs/kakao-oauth-setup.md)"
        )

    from ui.auth_ui import render_trial_button

    render_trial_button(key_prefix="landing_auth")


def check_user_session() -> None:
    """카카오 직접 OAuth / Supabase OAuth 콜백 처리."""
    qp = st.query_params
    code = _qp_first(qp.get("code"))
    state = _qp_first(qp.get("state"))

    if code and state == _KAKAO_OAUTH_STATE:
        try:
            _complete_kakao_direct_login(code)
        except Exception as exc:
            st.session_state["_auth_last_error"] = str(exc)
        st.query_params.clear()
        st.rerun()
        return

    if not supabase_configured():
        return

    try:
        client = get_supabase_client()
    except Exception as exc:
        st.session_state["_auth_last_error"] = str(exc)
        return

    if not client:
        return

    if code and state != _KAKAO_OAUTH_STATE:
        try:
            response = client.auth.exchange_code_for_session(
                {"auth_code": code, "redirect_to": streamlit_url()}
            )
            if response.session:
                _apply_supabase_session(response.session)
            st.query_params.clear()
            st.rerun()
        except Exception as exc:
            st.session_state["_auth_last_error"] = str(exc)
            st.query_params.clear()
            return

    try:
        session = client.auth.get_session()
    except Exception:
        return

    if session and session.user and not st.session_state.get("user"):
        _apply_supabase_session(session)
