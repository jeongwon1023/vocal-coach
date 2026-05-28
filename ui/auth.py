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
    """우측 상단 — 로그인 팝오버 또는 사용자 메뉴 (데스크톱)."""
    user = current_user()
    if user:
        name = user.get("name", "학습자")
        with st.popover(f"👤 {name}", use_container_width=True, key="top_auth_user"):
            _render_user_popover_body(user)
        return

    with st.popover("로그인", use_container_width=True, key="top_auth_popover"):
        render_login_compact(key_prefix="top_auth")


def render_menu_auth(*, key_prefix: str = "nav_menu") -> None:
    """모바일 햄버거 메뉴 안 — 계정 · 로그인."""
    user = current_user()
    if user:
        _render_user_popover_body(user, logout_key=f"{key_prefix}_logout")
        return

    st.caption("3초 만에 시작 · 기록 저장")
    render_login_compact(key_prefix=key_prefix)


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
    """상단 팝오버용 — 카카오 · Google · 체험."""
    from ui.auth_ui import render_auth_buttons

    st.caption("3초 만에 시작 · 기록 저장")
    render_auth_buttons(key_prefix=key_prefix, compact=True)


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
    """로그인 전용 화면 — 카카오·인스타 스타일 카드."""
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
    """홈 랜딩 — 체험 CTA (소셜 로그인은 상단 팝오버)."""
    st.markdown(
        """
        <div class="vc-landing-trial-banner">
            <div class="vc-landing-trial-copy">
                <span class="vc-landing-trial-tag">무료 체험</span>
                <p class="vc-landing-trial-title">가입 없이 바로 분석해 보세요</p>
                <p class="vc-landing-trial-sub">기록 저장은 상단 <b>로그인 / 회원가입</b> · 카카오 · Google</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    from ui.auth_ui import render_trial_button

    render_trial_button(key_prefix="landing_auth")
