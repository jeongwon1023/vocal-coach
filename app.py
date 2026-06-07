"""
Vocal Coach AI — Streamlit 진입점.
UI 렌더 전 Supabase 세션 복구 → 로그인 시 대시보드, 미로그인 시 로그인 화면만.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

APP_BUILD = "2026-06-07-dash-v9"

st.set_page_config(
    page_title="Vocal Coach AI — 무료 보컬 분석",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Vocal Coach AI — 녹음 한 번으로 음정·박자·호흡 분석 + AI 코칭.",
    },
)

from ui.auth import (  # noqa: E402
    handle_oauth_callback_if_present,
    init_auth,
    kakao_login_available,
    open_login_dialog,
    restore_persisted_auth,
)
from ui.safe_user import normalize_session_user  # noqa: E402


def _init_session_state() -> None:
    for key, val in (("user", None), ("auth_token", None)):
        if key not in st.session_state:
            st.session_state[key] = val


def _qp_has_oauth_code() -> bool:
    try:
        code = st.query_params.get("code")
        if isinstance(code, list):
            return bool(code)
        return bool(code)
    except Exception:
        return False


def sync_session_guard(*, force: bool = False) -> bool:
    """쿠키 · auth_token · supabase.auth.get_session() — UI 그리기 전 세션 복구."""
    _init_session_state()
    normalize_session_user()

    if st.session_state.get("user") and not force:
        return True
    if _qp_has_oauth_code():
        normalize_session_user()
        return bool(st.session_state.get("user"))

    restore_persisted_auth()
    normalize_session_user()
    if st.session_state.get("user"):
        return True

    if st.session_state.get("auth_token"):
        restore_persisted_auth()
        normalize_session_user()
    return bool(st.session_state.get("user"))


# ── UI 그리기 전 세션 복구 (OAuth → Supabase get_session) ──
handle_oauth_callback_if_present()
sync_session_guard(force=True)


def _render_login_screen() -> None:
    """미로그인 — 카카오/로그인만 (체험 배너·디버그 출력 없음)."""
    from ui.auth import _render_kakao_login_button, _render_supabase_kakao_styles
    from ui.utils import render_safe_html

    render_safe_html(
        f'<div aria-hidden="true" data-vc-build="{APP_BUILD}"></div>'
    )
    st.markdown("### ⚡️ Vocal Coach AI")
    st.markdown(
        "**무료로 내 보컬 분석** — 녹음 한 번이면 1분 안에 "
        "음정 · 박자 · 호흡 · AI 코칭 리포트를 받을 수 있어요."
    )
    st.caption("로그인하면 분석 기록이 클라우드에 안전하게 저장됩니다.")

    if kakao_login_available():
        _render_supabase_kakao_styles()
        _render_kakao_login_button(key="landing_hero_cta")
    else:
        if st.button(
            "🔐 카카오 / 로그인으로 시작",
            type="primary",
            use_container_width=True,
            key="landing_hero_cta",
        ):
            open_login_dialog(key_prefix="app_login_dialog")

    if st.button("로그인", type="secondary", use_container_width=True, key="app_login_secondary"):
        open_login_dialog(key_prefix="app_login_secondary_dialog")


def main() -> None:
    from gpt_coach import load_dotenv_if_present
    from ui.error_guard import (
        init_error_guard,
        render_error_dialog_if_needed,
        render_retry_indicator,
        run_preflight,
    )
    from ui.runtime_env import configure_matplotlib

    load_dotenv_if_present(PROJECT_DIR)
    init_error_guard()
    run_preflight()
    render_error_dialog_if_needed()

    from ui.analytics import inject_ga4

    inject_ga4()
    render_retry_indicator()
    configure_matplotlib()

    init_auth()
    sync_session_guard(force=not bool(st.session_state.get("user")))
    normalize_session_user()

    welcome = st.session_state.pop("_login_welcome", None)
    if welcome:
        st.toast(f"{welcome}님, 환영합니다! 🎤", icon="👋")

    from ui.admin_auth import try_admin_url_access

    try_admin_url_access()

    logged_in = bool(st.session_state.get("user"))
    from ui import styles

    styles.apply(page="마이 페이지" if logged_in else "홈")

    from ui.loading import render_loading_overlay

    render_loading_overlay()

    if logged_in:
        from ui import my_page

        my_page.render()
    else:
        _render_login_screen()


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
