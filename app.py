"""
보컬 코치 AI — 웹 UI (Streamlit)
상단 네비 · 우측 로그인 · 분석 설정은 버튼 다이얼로그
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

st.set_page_config(
    page_title="Vocal Coach AI — 무료 보컬 분석",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "Vocal Coach AI — 녹음 한 번으로 음정·박자·호흡 분석 + AI 코칭. 무료 체험 가능.",
    },
)


def _import_ui():
    from gpt_coach import load_dotenv_if_present
    from ui import auth, landing, my_page, navbar, navigation, styles

    load_dotenv_if_present(PROJECT_DIR)
    return auth, landing, my_page, navbar, navigation, styles


def main() -> None:
    from ui.error_guard import (
        handle_global_exception,
        init_error_guard,
        render_error_dialog_if_needed,
        run_preflight,
    )
    from ui.runtime_env import configure_matplotlib

    init_error_guard()
    run_preflight()
    render_error_dialog_if_needed()

    from ui.analytics import inject_ga4
    from ui.error_guard import render_retry_indicator
    from ui.legal_footer import render_beta_data_warning

    inject_ga4()
    render_retry_indicator()
    render_beta_data_warning()

    auth, landing, my_page, navbar, navigation, styles = _import_ui()
    configure_matplotlib()

    auth.init_auth()
    navigation.init_nav()

    from ui.admin_auth import try_admin_url_access

    try_admin_url_access()

    page = navigation.current_page()
    styles.apply(page=page)

    page = navbar.render_navbar()

    from ui.beta import render_beta_banner

    render_beta_banner()

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
