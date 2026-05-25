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


try:
    auth, landing, my_page, navbar, navigation, styles = _import_ui()
except Exception:
    st.error("모듈을 불러오지 못했습니다.")
    st.code(traceback.format_exc())
    st.stop()

from ui.runtime_env import configure_matplotlib

configure_matplotlib()

auth.init_auth()
navigation.init_nav()

page = navigation.current_page()
styles.apply(page=page)

page = navbar.render_navbar()

from ui.beta import render_beta_banner

render_beta_banner()


if page == "홈":
    landing.render()
elif page == "피드백":
    from ui.user_feedback import render_feedback_page

    render_feedback_page()
else:
    if not auth.is_logged_in():
        st.markdown(
            """
            <div class="vc-page-head">
                <h2 class="vc-page-title">마이 페이지 📈</h2>
                <p class="vc-page-desc">분석 기록·성장 그래프는 로그인 후 이용할 수 있어요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        auth.render_login_page()
        st.stop()
    my_page.render()
