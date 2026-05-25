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
    page_title="Vocal Coach AI",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _import_ui():
    from gpt_coach import load_dotenv_if_present
    from ui import auth, dashboard, landing, my_page, navbar, navigation, styles

    load_dotenv_if_present(PROJECT_DIR)
    return auth, dashboard, landing, my_page, navbar, navigation, styles


try:
    auth, dashboard, landing, my_page, navbar, navigation, styles = _import_ui()
except Exception:
    st.error("모듈을 불러오지 못했습니다.")
    st.code(traceback.format_exc())
    st.stop()

auth.init_auth()
navigation.init_nav()

page = navigation.current_page()
styles.apply(page=page)

page = navbar.render_navbar()

from ui.beta import render_beta_banner

render_beta_banner()


if page == "홈":
    landing.render()
elif page == "분석":
    dashboard.render()
else:
    if not auth.is_logged_in():
        st.markdown("### 마이 페이지")
        st.info("분석 기록을 저장하려면 **우측 상단 로그인 / 회원가입**을 눌러 주세요.")
        auth.render_login_page()
        st.stop()
    styles.section_title(
        f"{auth.current_user().get('name', '학습자')}님의 성장 기록",
        "날짜별 점수 · 그래프 · 기록 비교",
    )
    my_page.render()
