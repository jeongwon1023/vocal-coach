"""
보컬 코치 AI — 웹 UI (Streamlit)
상단 네비 · 우측 로그인 · 사이드바는 분석 페이지 전용
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
    initial_sidebar_state="expanded",
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


def _render_analysis_sidebar() -> None:
    from style_presets import PRESETS
    from ui.help_guide import render_song_title_help, render_youtube_guide_sidebar

    st.markdown(
        '<p class="vc-sidebar-title">옵션</p>',
        unsafe_allow_html=True,
    )
    styles.sidebar_label("분석 모드")
    st.checkbox(
        "빠른 분석 (권장)",
        key="fast_mode",
        value=True,
        help="약 2~4배 빠름. 유튜브/MR 믹스 자동 대응.",
    )
    st.divider()
    styles.sidebar_label("유튜브 가이드")
    render_song_title_help()
    st.text_input(
        "곡 제목",
        key="song_title",
        placeholder="예: 아이유 밤편지, NewJeans Ditto",
    )
    st.checkbox(
        "유튜브 가이드 사용",
        key="use_youtube",
        value=False,
        help="켜면 곡 제목으로 MR·가이드 멜로디를 찾아 원곡과 비교합니다.",
    )
    render_youtube_guide_sidebar()
    st.divider()
    styles.sidebar_label("기타 옵션")
    st.selectbox(
        "가창 스타일",
        options=list(PRESETS.keys()),
        format_func=lambda k: PRESETS[k].label,
        key="style_preset",
    )
    st.checkbox("GPT 코칭", key="use_gpt", value=False)
    st.checkbox("기록 저장", key="save_record", value=True)
    st.checkbox("이전 기록 비교", key="compare", value=True)
    st.divider()
    styles.sidebar_label("고급")
    st.checkbox("문제 구간 클립", key="export_clips", value=False)
    st.checkbox("성장 그래프", key="growth_chart", value=False)
    st.checkbox("백그라운드 분석 큐", key="use_queue", value=True)
    st.divider()
    st.markdown(
        "<div class='tip-box' style='font-size:0.82rem;'>"
        "🎧 MR은 이어폰 · 마이크엔 목소리만</div>",
        unsafe_allow_html=True,
    )


if page == "분석":
    with st.sidebar:
        st.markdown(
            '<p class="vc-sidebar-title">⚙️ 분석 설정</p>',
            unsafe_allow_html=True,
        )
        st.caption("빠른/정밀 · 유튜브 · GPT 등")
        _render_analysis_sidebar()

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
