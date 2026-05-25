"""로그인 · 회원가입 UI (Google · Kakao · 체험)."""

from __future__ import annotations

import streamlit as st

from auth_service import (
    auth_base_url,
    create_demo_user,
    create_session,
    delete_session,
    google_configured,
    kakao_configured,
    resolve_session,
)
from ui.runtime_env import is_streamlit_cloud


def _oauth_unconfigured_hint(provider: str) -> str:
    if is_streamlit_cloud():
        return f"{provider}: 베타 — **체험 계정**으로 이용해 주세요"
    return f"{provider}: OAuth 미설정 (로컬 .env 참고)"


def init_auth() -> None:
    """URL ?token= 또는 세션에서 사용자 복원."""
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user" not in st.session_state:
        st.session_state.user = None

    qp = st.query_params
    token = qp.get("token")
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
    token = st.session_state.get("auth_token")
    if token:
        delete_session(token)
    st.session_state.auth_token = None
    st.session_state.user = None
    st.rerun()


def render_topbar_auth() -> None:
    """우측 상단 — 로그인 팝오버 또는 사용자 메뉴."""
    user = current_user()
    if user:
        name = user.get("name", "학습자")
        with st.popover(f"👤 {name}", use_container_width=True, key="top_auth_user"):
            st.markdown(f"**{name}**")
            if user.get("email"):
                st.caption(user["email"])
            provider = {"google": "Google", "kakao": "카카오", "demo": "체험"}.get(
                user.get("provider", ""), ""
            )
            if provider:
                st.caption(f"연동: {provider}")
            if st.button("로그아웃", key="btn_logout_top", use_container_width=True):
                logout()
        return

    with st.popover("로그인 / 회원가입", use_container_width=True, key="top_auth_popover"):
        render_login_compact(key_prefix="top_auth")


def render_login_compact(*, key_prefix: str = "auth_pop") -> None:
    """상단 팝오버용 — 카카오 · Google · 체험."""
    base = auth_base_url()
    g_ok = google_configured()
    k_ok = kakao_configured()

    st.caption("소셜 계정으로 빠르게 시작하세요")

    if g_ok:
        st.markdown(
            f'<a href="{base}/auth/google" class="vc-auth-btn vc-auth-google vc-auth-sm">Google로 시작</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="vc-auth-btn vc-auth-disabled vc-auth-sm">Google로 시작</span>',
            unsafe_allow_html=True,
        )
        st.caption(_oauth_unconfigured_hint("Google"))

    if k_ok:
        st.markdown(
            f'<a href="{base}/auth/kakao" class="vc-auth-btn vc-auth-kakao vc-auth-sm">카카오로 시작</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="vc-auth-btn vc-auth-disabled vc-auth-sm">카카오로 시작</span>',
            unsafe_allow_html=True,
        )
        st.caption(_oauth_unconfigured_hint("카카오"))

    st.divider()
    if st.button("✦ 체험 계정으로 시작", key=f"{key_prefix}_demo", use_container_width=True):
        start_demo()


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
    """로그인 전용 화면."""
    base = auth_base_url()
    g_ok = google_configured()
    k_ok = kakao_configured()

    st.markdown(
        """
        <div class="vc-login-wrap">
            <div class="vc-login-card">
                <p class="vc-login-eyebrow">VOCAL COACH AI</p>
                <h2 class="vc-login-title">보컬 레슨실에<br>오신 걸 환영해요</h2>
                <p class="vc-login-sub">로그인하면 분석 기록·성장 그래프를<br>내 마이 페이지에 모아둘 수 있어요.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vc-login-actions">', unsafe_allow_html=True)

    if g_ok:
        st.markdown(
            f'<a href="{base}/auth/google" class="vc-auth-btn vc-auth-google">Google로 시작하기</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="vc-auth-btn vc-auth-disabled" title="OAuth 미설정">Google로 시작하기</span>',
            unsafe_allow_html=True,
        )

    if k_ok:
        st.markdown(
            f'<a href="{base}/auth/kakao" class="vc-auth-btn vc-auth-kakao">카카오로 시작하기</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="vc-auth-btn vc-auth-disabled">카카오로 시작하기</span>',
            unsafe_allow_html=True,
        )

    st.markdown('<p class="vc-login-or">또는</p>', unsafe_allow_html=True)

    if st.button("체험 계정으로 바로 시작", use_container_width=True, key="demo_login"):
        start_demo()

    st.markdown("</div>", unsafe_allow_html=True)

    if not g_ok and not k_ok:
        with st.expander("소셜 로그인 연동 방법 (선택)"):
            st.markdown(
                "1. `.env.example` → `.env` 복사\n\n"
                "2. **Google** — [Cloud Console](https://console.cloud.google.com/) OAuth 클라이언트  \n"
                "   리디렉션: `http://localhost:8001/auth/google/callback`\n\n"
                "3. **Kakao** — [developers.kakao.com](https://developers.kakao.com/) REST API 키  \n"
                "   Redirect: `http://localhost:8001/auth/kakao/callback`\n\n"
                "4. `run_web.bat` 재실행\n\n"
                "**지금은 위 「체험 계정」으로 모든 기능을 쓸 수 있어요.**"
            )


def require_login() -> bool:
    if is_logged_in():
        return True
    render_login_page()
    return False
