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
    kakao_redirect_uri,
    resolve_session,
    streamlit_url,
)
from ui.runtime_env import is_streamlit_cloud
from ui.utils import render_safe_html
from ui.error_guard import (
    clear_retry_ui_state,
    httpx_get_once,
    httpx_get_with_retry,
    httpx_post_once,
    httpx_post_with_retry,
    log_error,
    login_actions_enabled,
    login_disabled_tooltip,
    oauth_callback_active,
    queue_error_dialog,
    with_retry,
)

try:
    from gotrue._sync.storage import SyncSupportedStorage  # noqa: F401 — auth_storage

    _SUPABASE_IMPORT_OK = True
except ImportError:
    _SUPABASE_IMPORT_OK = False

from ui.supabase_client import create_supabase_client, is_supabase_key_format
from ui.auth_storage import PersistentAuthStorage, clear_auth_cache_files

_KAKAO_OAUTH_STATE = "vc_kakao"
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


def _secret_or_env(name: str) -> str | None:
    try:
        if name in st.secrets:
            value = str(st.secrets[name]).strip().strip('"').strip("'")
            if value:
                return value
    except Exception:
        pass
    value = os.environ.get(name, "").strip().strip('"').strip("'")
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
        return create_supabase_client(url, key, storage=PersistentAuthStorage())
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


def _clear_oauth_query_params() -> None:
    """OAuth 콜백 파라미터 제거 — URL 무한 루프 방지."""
    for key in ("code", "state", "error", "error_description"):
        try:
            if key in st.query_params:
                del st.query_params[key]
        except Exception:
            pass
    try:
        st.query_params.clear()
    except Exception:
        pass


def _on_login_success(*, previous_anon_id: str | None = None) -> None:
    """로그인 직후 — 게스트 분석 기록 클라우드 동기화."""
    st.session_state.pop("analysis_completed_guest", None)
    anon_id = previous_anon_id or st.session_state.pop("anon_analysis_id", None)
    user_id = current_user_id()
    if not anon_id or not user_id or not str(anon_id).startswith("anon_"):
        return
    try:
        from db_store import sync_guest_records_to_user

        count = sync_guest_records_to_user(anon_id=anon_id, user_id=user_id)
        if count:
            st.session_state["_guest_sync_count"] = count
    except Exception as exc:
        log_error("게스트 기록 동기화 실패", source="_on_login_success", exc=exc)


def _is_pkce_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "code verifier" in msg or "code_verifier" in msg or (
        "non-empty" in msg and "auth code" in msg
    )


def _try_supabase_code_exchange(code: str) -> bool:
    """Supabase PKCE — 디스크에서 code_verifier 복원 후 교환."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        response = _supabase_exchange_code_once(client, code)
        if response.session:
            _apply_supabase_session(response.session)
            clear_auth_cache_files()
            return True
    except Exception as exc:
        if _is_pkce_error(exc):
            st.session_state["_auth_last_error"] = (
                "로그인 연동이 만료되었어요. 상단 **로그인**을 다시 눌러 주세요."
            )
            log_error("PKCE code_verifier 유실", source="_try_supabase_code_exchange", exc=exc)
            clear_auth_cache_files()
            return False
        raise
    return False


def _exchange_oauth_code(code: str, state: str | None) -> bool:
    """authorization code → 세션 (직접 카카오 우선 · Supabase는 PKCE 디스크 복원)."""
    try:
        is_direct_flow = state == _KAKAO_OAUTH_STATE or (
            kakao_direct_configured() and state is None
        )

        if is_direct_flow and kakao_direct_configured():
            _complete_kakao_direct_login(code)
            if st.session_state.get("user"):
                clear_auth_cache_files()
                return True
            return False

        if supabase_configured() and state != _KAKAO_OAUTH_STATE:
            if _try_supabase_code_exchange(code):
                return True

        if kakao_direct_configured():
            _complete_kakao_direct_login(code)
            if st.session_state.get("user"):
                clear_auth_cache_files()
                return True

        return bool(st.session_state.get("user"))
    except Exception as exc:
        st.session_state["_auth_last_error"] = str(exc)
        log_error("OAuth code 교환 실패", source="_exchange_oauth_code", exc=exc)
        clear_auth_cache_files()
        return False


def handle_oauth_callback_if_present() -> None:
    """app.py 최상단 — URL ?code= 콜백 즉시 처리 (페이지 렌더 전)."""
    if _qp_first(st.query_params.get("kakao_debug")) == "1":
        return
    if _qp_first(st.query_params.get("error")):
        return

    code = _qp_first(st.query_params.get("code"))
    if not code:
        st.session_state.pop("_oauth_in_progress", None)
        return

    if st.session_state.get("user"):
        _clear_oauth_query_params()
        st.session_state.pop("_oauth_in_progress", None)
        st.rerun()

    if st.session_state.get("_oauth_handled_code") == code:
        _clear_oauth_query_params()
        st.session_state.pop("_oauth_in_progress", None)
        return

    st.session_state["_oauth_in_progress"] = True
    clear_retry_ui_state()

    state = _qp_first(st.query_params.get("state"))
    anon_before = st.session_state.get("anon_analysis_id")

    with st.spinner("카카오 로그인 연동 중입니다..."):
        success = _exchange_oauth_code(code, state)

    st.session_state["_oauth_handled_code"] = code
    st.session_state.pop("_oauth_in_progress", None)
    _clear_oauth_query_params()

    if success:
        _on_login_success(previous_anon_id=anon_before)
        try:
            from ui.navigation import go_to

            st.session_state["nav_page"] = "마이 페이지"
        except Exception:
            pass
        st.rerun()

    err = st.session_state.get("_auth_last_error") or "카카오 로그인에 실패했습니다. 다시 시도해 주세요."
    st.error(err)
    st.info("잠시 후 홈으로 이동합니다. 상단 **로그인** 또는 **체험 계정**을 이용해 주세요.")
    st.stop()


def render_pending_oauth_redirect() -> None:
    """다이얼로그/iframe 밖 최상위 창으로 OAuth 이동 (kauth.kakao.com iframe 차단 우회)."""
    url = st.session_state.pop("oauth_redirect_url", None)
    if not url:
        return

    import json

    import streamlit.components.v1 as components

    mode = st.session_state.pop("oauth_redirect_mode", "direct")
    components.html(
        f"<script>window.top.location.href = {json.dumps(url)};</script>",
        height=0,
        width=0,
    )
    st.info("카카오 로그인 페이지로 이동 중...")
    debug = _qp_first(st.query_params.get("kakao_debug")) == "1"
    try:
        from ui.admin_auth import is_admin_authenticated

        debug = debug or is_admin_authenticated()
    except Exception:
        pass
    if debug:
        from ui.kakao_setup import render_oauth_redirect_debug

        render_oauth_redirect_debug(url, mode=mode)
    st.link_button(
        "💬 카카오로 계속하기",
        url,
        use_container_width=True,
        type="primary",
    )
    st.stop()


def init_auth() -> None:
    """URL ?token= / Supabase OAuth / 세션에서 사용자 복원."""
    qp = st.query_params
    if _qp_first(qp.get("kakao_debug")) == "1":
        from ui.kakao_setup import render_kakao_debug_banner

        render_kakao_debug_banner()
        st.stop()

    if oauth_callback_active():
        clear_retry_ui_state()
        if _qp_first(st.query_params.get("code")):
            return

    _render_oauth_callback_errors()
    render_pending_oauth_redirect()

    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user" not in st.session_state:
        st.session_state.user = None

    try:
        check_user_session()
    except Exception as exc:
        st.session_state["_auth_last_error"] = str(exc)
        log_error("세션 복원 실패", source="init_auth", exc=exc)

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
        clear_auth_cache_files()
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

    if st.button(
        "로그인",
        key="top_auth_login_btn",
        use_container_width=False,
        type="secondary",
        disabled=not login_actions_enabled(),
        help=login_disabled_tooltip() if not login_actions_enabled() else None,
    ):
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
    enabled = login_actions_enabled()
    if st.button(
        "💬 카카오로 계속하기",
        key=key,
        use_container_width=True,
        disabled=not enabled,
        help=login_disabled_tooltip() if not enabled else None,
    ):
        _start_kakao_oauth()


def _render_oauth_callback_errors() -> None:
    """카카오/Supabase OAuth 에러 쿼리 파라미터 표시."""
    from ui.kakao_setup import render_koe006_fix_panel

    qp = st.query_params
    error = _qp_first(qp.get("error"))
    if not error:
        return

    desc = _qp_first(qp.get("error_description")) or error
    st.session_state["_auth_last_error"] = desc
    log_error(f"OAuth callback error: {error}", source="init_auth", extra={"description": desc})

    if error == "invalid_request" or "KOE006" in str(desc) or "redirect" in str(desc).lower():
        render_koe006_fix_panel()
    else:
        st.error(f"로그인 오류: {desc}")

    st.query_params.clear()
    st.stop()


def _qp_first(value: str | list[str] | None) -> str | None:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _complete_kakao_direct_login(code: str) -> None:
    """카카오 authorization code → 앱 세션 (Supabase Auth 미사용)."""
    import httpx

    rest_key = _secret_or_env("KAKAO_REST_API_KEY")
    if not rest_key or len(rest_key) < 20:
        msg = "KAKAO_REST_API_KEY가 Secrets에 없거나 형식이 올바르지 않습니다."
        st.session_state["_auth_last_error"] = msg
        log_error(msg, source="_complete_kakao_direct_login")
        queue_error_dialog(msg, source="kakao_oauth")
        return

    redirect = (kakao_redirect_uri() or streamlit_url() or "").rstrip("/")
    if not redirect.startswith("http"):
        msg = "Redirect URI(STREAMLIT_URL)가 설정되지 않았습니다."
        st.session_state["_auth_last_error"] = msg
        log_error(msg, source="_complete_kakao_direct_login", extra={"redirect_uri": redirect})
        queue_error_dialog(msg, source="kakao_oauth")
        return

    payload: dict[str, str] = {
        "grant_type": "authorization_code",
        "client_id": rest_key.strip(),
        "redirect_uri": redirect,
        "code": code.strip(),
    }
    secret = _secret_or_env("KAKAO_CLIENT_SECRET")
    if secret:
        payload["client_secret"] = secret.strip()

    try:
        token_resp = httpx.post(
            KAKAO_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    except Exception as exc:
        st.session_state["_auth_last_error"] = f"Kakao 토큰 교환 네트워크 오류: {exc}"
        log_error("Kakao 토큰 교환 네트워크 오류", source="_complete_kakao_direct_login", exc=exc)
        queue_error_dialog(
            "카카오 로그인 중 네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            source="kakao_oauth",
        )
        return

    if token_resp.status_code >= 400:
        body = token_resp.text[:2000]
        user_msg = (
            "카카오 로그인 설정 오류입니다.\n\n"
            "· 카카오 디벨로퍼스 → 카카오 로그인 → **보안** → Client Secret **사용 안함**\n"
            "· REST API 키 · Redirect URI(앱 URL) 등록 확인"
        )
        if token_resp.status_code == 401:
            user_msg = (
                "카카오 로그인 설정 오류 (401).\n\n"
                "카카오 디벨로퍼스에서 **Client Secret → 사용 안함**으로 설정했는지, "
                "REST API 키와 Redirect URI가 맞는지 확인해 주세요."
            )
        st.session_state["_auth_last_error"] = user_msg
        log_error(
            f"Kakao 토큰 교환 실패 HTTP {token_resp.status_code}",
            source="_complete_kakao_direct_login",
            extra={
                "redirect_uri": redirect,
                "client_id_prefix": rest_key[:8] + "...",
                "client_secret_sent": bool(secret),
                "response_body": body,
            },
        )
        queue_error_dialog(f"{user_msg}\n\n(상세: {body[:400]})", source="kakao_oauth")
        return

    access = token_resp.json().get("access_token")
    if not access:
        body = token_resp.text[:500]
        st.session_state["_auth_last_error"] = "Kakao access_token 없음"
        log_error(
            "Kakao access_token 없음",
            source="_complete_kakao_direct_login",
            extra={"response_body": body},
        )
        queue_error_dialog("카카오 로그인 설정 오류: access_token을 받지 못했습니다.", source="kakao_oauth")
        return

    try:
        user_resp = httpx_get_once(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access}"},
            timeout=15,
        )
    except Exception as exc:
        st.session_state["_auth_last_error"] = f"Kakao 사용자 정보 실패: {exc}"
        log_error("Kakao 사용자 정보 실패", source="_complete_kakao_direct_login", exc=exc)
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
    from ui.kakao_setup import build_kakao_direct_authorize_url

    rest_key = _secret_or_env("KAKAO_REST_API_KEY")
    if not rest_key:
        st.error("KAKAO_REST_API_KEY가 Secrets에 없습니다.")
        return

    url = build_kakao_direct_authorize_url(client_id=rest_key)
    st.session_state["oauth_redirect_url"] = url
    st.session_state["oauth_redirect_mode"] = "direct"
    st.rerun()


def _diagnose_kakao_auth() -> bool:
    if kakao_direct_configured():
        return True
    return _diagnose_supabase_auth()


def _diagnose_supabase_auth() -> bool:
    """Supabase 연결 및 OAuth Provider 설정 확인."""
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

    try:
        resp = httpx_get_with_retry(
            f"{url.rstrip('/')}/auth/v1/settings",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10,
        )
    except Exception as exc:
        log_error("Supabase settings 조회 실패", source="_diagnose_supabase_auth", exc=exc)
        st.error(f"Supabase 연결 실패: {exc}")
        return False

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
    if not login_actions_enabled():
        st.warning(login_disabled_tooltip())
        return

    if not kakao_direct_configured():
        from ui.kakao_setup import render_koe006_fix_panel

        st.error(
            "KAKAO_REST_API_KEY가 Secrets에 없습니다. "
            "Supabase 경유 로그인은 KOE006/KOE205가 자주 발생합니다."
        )
        render_koe006_fix_panel()
        return

    try:
        if not _diagnose_kakao_auth():
            return
    except Exception as exc:
        log_error("카카오 설정 진단 실패", source="_start_kakao_oauth", exc=exc)
        st.error("설정 에러: 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.")
        return

    _start_kakao_direct_oauth()


@with_retry
def _supabase_sign_in_with_oauth(client: Any, options: dict[str, Any]) -> Any:
    return client.auth.sign_in_with_oauth(options)


@with_retry
def _supabase_exchange_code(client: Any, code: str) -> Any:
    return client.auth.exchange_code_for_session(
        {"auth_code": code, "redirect_to": streamlit_url()}
    )


def _supabase_exchange_code_once(client: Any, code: str) -> Any:
    """OAuth 콜백 — 재시도 없이 1회 교환 (무한 스피너 방지)."""
    return client.auth.exchange_code_for_session(
        {"auth_code": code, "redirect_to": streamlit_url()}
    )


def _render_supabase_login_dialog(*, key_prefix: str) -> None:
    _render_supabase_kakao_styles()
    _render_kakao_login_button(key="supabase_kakao_login")

    st.caption("또는")
    if st.button("✦ 체험 계정으로 시작", key=f"{key_prefix}_demo", use_container_width=True):
        start_demo()


@st.dialog("3초 만에 시작하기", width="small")
def _show_login_dialog() -> None:
    prefix = st.session_state.get("_login_dialog_prefix", "dialog_auth")
    if not login_actions_enabled():
        st.warning(f"**{login_disabled_tooltip()}**")
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
    anon_before = st.session_state.get("anon_analysis_id")
    user = create_demo_user()
    token = create_session(user.id)
    st.session_state.auth_token = token
    st.session_state.user = user.to_dict()
    st.session_state.show_login = False
    _on_login_success(previous_anon_id=anon_before)
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
    """기존 세션 복원 — OAuth ?code= 는 handle_oauth_callback_if_present()에서 처리."""
    if _qp_first(st.query_params.get("code")):
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

    try:
        session = client.auth.get_session()
    except Exception:
        return

    if session and session.user and not st.session_state.get("user"):
        _apply_supabase_session(session)
