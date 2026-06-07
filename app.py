"""
보컬 코치 AI — Streamlit 앱 진입점.
UI 렌더 전 Supabase 세션 동기 가드 → F5 새로고침 로그아웃 방지.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

APP_BUILD = "2026-06-07-dash-v6"

st.set_page_config(
    page_title="Vocal Coach AI — 무료 보컬 분석",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Vocal Coach AI — 녹음 한 번으로 음정·박자·호흡 분석 + AI 코칭.",
    },
)

# ── UI 렌더 전: OAuth 콜백 + 세션 동기 (supabase.auth.get_session) ──
from ui.auth import (  # noqa: E402
    handle_oauth_callback_if_present,
    restore_persisted_auth,
)


def _init_session_state() -> None:
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None


def sync_session_guard(*, force: bool = False) -> bool:
    """
    동기식 세션 홀딩 가드.
    F5 / 페이지 전환 시 쿠키 → auth_token → supabase.auth.get_session() 순으로 복원.
    user가 이미 있으면 True. force=True면 get_session 재시도.
    """
    _init_session_state()
    if st.session_state.get("user") and not force:
        return True
    if _qp_has_oauth_code():
        return bool(st.session_state.get("user"))
    restore_persisted_auth()
    if st.session_state.get("user"):
        return True
    if st.session_state.get("auth_token"):
        restore_persisted_auth()
    return bool(st.session_state.get("user"))


def _qp_has_oauth_code() -> bool:
    try:
        code = st.query_params.get("code")
        if isinstance(code, list):
            return bool(code)
        return bool(code)
    except Exception:
        return False


handle_oauth_callback_if_present()
sync_session_guard(force=True)


def _import_ui():
    from gpt_coach import load_dotenv_if_present
    from ui import auth, landing, my_page, navbar, navigation, styles

    load_dotenv_if_present(PROJECT_DIR)
    return auth, landing, my_page, navbar, navigation, styles


def main() -> None:
    from ui.error_guard import (
        init_error_guard,
        render_error_dialog_if_needed,
        render_retry_indicator,
        run_preflight,
    )
    from ui.runtime_env import configure_matplotlib

    init_error_guard()
    run_preflight()
    render_error_dialog_if_needed()

    from ui.analytics import inject_ga4

    inject_ga4()
    render_retry_indicator()

    auth, landing, my_page, navbar, navigation, styles = _import_ui()
    configure_matplotlib()

    auth.init_auth()
    sync_session_guard(force=not bool(st.session_state.get("user")))

    welcome = st.session_state.pop("_login_welcome", None)
    if welcome:
        st.toast(f"{welcome}님, 환영합니다! 🎤", icon="👋")

    navigation.init_nav()

    from ui.admin_auth import try_admin_url_access

    try_admin_url_access()

    page = navigation.current_page()
    styles.apply(page=page)

    is_dashboard = page == "마이 페이지"

    if not is_dashboard:
        from ui.legal_footer import render_beta_data_warning

        render_beta_data_warning()
        page = navbar.render_navbar()
        from ui.beta import render_beta_banner

        render_beta_banner()
    else:
        from ui.dashboard_gnb import render_dashboard_gnb

        render_dashboard_gnb()

    from ui.loading import render_loading_overlay

    render_loading_overlay()

    if page == "홈":
        landing.render()
    elif page == "피드백":
        from ui.user_feedback import render_feedback_page

        render_feedback_page()
    elif page == "관리자":
        from ui.admin_errors import render_admin_page

        render_admin_page()
    else:
        my_page.render()


try:
    main()
except Exception as exc:
    try:
        from ui.error_guard import handle_global_exception

        handle_global_exception(exc, source="app.main")
    except Exception:
        st.warning("현재 일시적인 네트워크 지연이 발생했습니다. 잠시 후 다시 시도해 주세요.")
        with st.expander("상세 로그 보기"):
            st.code(traceback.format_exc())
    st.stop()
