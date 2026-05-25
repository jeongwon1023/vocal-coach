"""마이 페이지 — 분석 · 기록 배너 · 결과 보기."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from progress_chart import generate_growth_chart
from progress_tracker import list_records, load_record
from ui.auth import current_user, current_user_id, is_logged_in, start_demo
from ui import dashboard
from ui.navigation import go_to


def _format_date(record: dict) -> str:
    ts = record.get("recorded_at", "")
    if not ts:
        return "날짜 없음"
    return ts.replace("T", " ")[:16]


def _format_date_short(record: dict) -> str:
    ts = record.get("recorded_at", "")
    return ts[:10] if ts else "—"


def _score_color(score: float) -> str:
    if score >= 85:
        return "#22c55e"
    if score >= 70:
        return "#818cf8"
    if score >= 55:
        return "#f59e0b"
    return "#f87171"


def _record_stats(records_paths: list[Path]) -> dict:
    scores: list[float] = []
    for p in records_paths:
        try:
            r = load_record(p)
            scores.append(float(r.get("overall_score") or 0))
        except Exception:
            continue
    if not scores:
        return {"count": 0, "best": 0, "latest": 0, "avg": 0}
    return {
        "count": len(scores),
        "best": max(scores),
        "latest": scores[0],
        "avg": sum(scores) / len(scores),
    }


def _load_session_for_record(user_id: str, path: Path) -> dict:
    from ui.session_cache import load_session_cache, rebuild_session_from_record

    cached = load_session_cache(user_id, path.stem)
    if cached:
        return cached
    record = load_record(path)
    return rebuild_session_from_record(record, path)


def _render_login_gate() -> None:
    st.markdown(
        """
        <div class="vc-login-gate">
            <div class="vc-chat-card vc-login-card">
                <div class="vc-chat-avatar">🔐</div>
                <div class="vc-chat-body">
                    <p class="vc-chat-name">Vocal Coach AI</p>
                    <p class="vc-chat-msg">분석·기록은 로그인 후 이용할 수 있어요.<br>
                    카카오 · Google · 체험 계정 중 하나를 선택해 주세요.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✦ 체험 계정으로 시작", type="primary", use_container_width=True, key="mypage_gate_demo"):
            start_demo()
    with col2:
        st.markdown(
            '<p class="vc-gate-hint">또는 상단 <b>로그인 / 회원가입</b> 클릭</p>',
            unsafe_allow_html=True,
        )


def _render_history_banner(record: dict, overall: float, song: str, idx: int, path: Path) -> None:
    scores = record.get("stage_scores") or {}
    color = _score_color(overall)
    date_str = _format_date(record)
    date_short = _format_date_short(record)
    pitch = float(scores.get(1) or scores.get("1") or 0)
    rhythm = float(scores.get(2) or scores.get("2") or 0)
    breath = float(scores.get(3) or scores.get("3") or 0)

    st.markdown(
        f"""
        <div class="vc-history-banner" style="--banner-accent:{color}">
            <div class="vc-history-banner-left">
                <span class="vc-history-date">{html.escape(date_short)}</span>
                <p class="vc-history-song">{html.escape(str(song))}</p>
                <p class="vc-history-sub">{html.escape(date_str)} · 음{pitch:.0f} · 박{rhythm:.0f} · 호{breath:.0f}</p>
            </div>
            <div class="vc-history-score">
                <span class="vc-history-overall">{overall:.0f}</span>
                <span class="vc-history-score-label">점</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        f"결과 보기 · {date_short}",
        key=f"mypage_open_{idx}",
        use_container_width=True,
    ):
        user_id = current_user_id()
        if user_id:
            from ui.loading import mark_loading

            mark_loading(message="결과를 불러오고 있어요…")
            st.session_state["last_session"] = _load_session_for_record(user_id, path)
            st.session_state["mypage_show_result"] = True
            st.rerun()


def _render_hub(user_id: str, name: str, records_paths: list[Path]) -> None:
    stats = _record_stats(records_paths)
    st.markdown(
        f"""
        <div class="vc-page-head">
            <h2 class="vc-page-title">{html.escape(name)}님의 마이 페이지 🎤</h2>
            <p class="vc-page-desc">새 분석 · 완료 기록 · 성장 곡선을 한곳에서</p>
        </div>
        <div class="vc-mypage-stats">
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['count']}</span><span class="vc-mypage-stat-lbl">분석 횟수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['latest']:.0f}</span><span class="vc-mypage-stat-lbl">최근 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['best']:.0f}</span><span class="vc-mypage-stat-lbl">최고 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['avg']:.0f}</span><span class="vc-mypage-stat-lbl">평균</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if records_paths:
        st.markdown("##### 📋 분석 완료 기록")
        st.caption("날짜별 배너를 눌러 코치 DM · 상세 리포트를 다시 볼 수 있어요.")
        for idx, p in enumerate(records_paths[:20]):
            try:
                r = load_record(p)
            except Exception:
                continue
            overall = float(r.get("overall_score") or 0)
            song = r.get("song_title") or r.get("user_recording") or "녹음"
            _render_history_banner(r, overall, song, idx, p)

        if len(records_paths) > 1:
            st.markdown("##### 📈 성장 곡선")
            chart_path = generate_growth_chart(user_id=user_id)
            if chart_path and chart_path.exists():
                st.markdown('<div class="vc-graph-frame">', unsafe_allow_html=True)
                st.image(str(chart_path), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="vc-empty-card">
                <p class="vc-empty-title">아직 분석 기록이 없어요</p>
                <p class="vc-empty-desc">아래에서 녹음을 올리고 첫 분석을 시작해 보세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("##### 🎙️ 새 분석")
    dashboard.render_analysis_section(show_settings=True)


def render() -> None:
    if not is_logged_in():
        _render_login_gate()
        return

    user = current_user()
    user_id = current_user_id()
    name = user.get("name", "학습자") if user else "학습자"

    if not user_id:
        st.warning("로그인 정보를 확인할 수 없습니다.")
        return

    if not dashboard.is_analyzing():
        from ui.analysis_overlay import clear_analyze_stage

        clear_analyze_stage()

    if dashboard.is_analyzing():
        from ui.analysis_overlay import close_analyze_stage, open_analyze_stage

        open_analyze_stage()
        dashboard.render_analysis_section(show_settings=False)
        close_analyze_stage()
        return

    if st.session_state.get("last_session") and st.session_state.get("mypage_show_result"):
        from ui.analysis_overlay import clear_analyze_stage

        clear_analyze_stage()
        if st.session_state.pop("scroll_result", False):
            from ui.scroll import scroll_to_top

            scroll_to_top(anchor_id="vc-result-top")
        if st.button("← 기록 목록으로", key="mypage_back_list", type="secondary"):
            dashboard.clear_results_state()
            st.rerun()
        dashboard.render_results_view()
        from ui.beta import render_beta_footer

        render_beta_footer()
        return

    records_paths = list_records(limit=50, user_id=user_id)
    _render_hub(user_id, name, records_paths)

    from ui.beta import render_beta_footer

    render_beta_footer()

    if st.button("💬 서비스 피드백 남기기", use_container_width=True, key="mypage_feedback"):
        go_to("피드백")
