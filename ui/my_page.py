"""마이 페이지 — 분석 · 기록 배너 · 결과 보기."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from progress_chart import (
    compute_practice_streak,
    generate_growth_chart,
    generate_history_sparkline,
    load_all_records_chronological,
    recent_overall_scores
)
from progress_tracker import list_records, load_record
from weekly_summary import compute_weekly_summary
from ui.auth import current_user, current_user_id, is_logged_in
from ui import dashboard
from ui.navigation import go_to
from ui.session_reset import clear_results_state
from ui.utils import render_safe_html


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


def _record_stats_from_cloud(records: list[dict]) -> dict:
    scores: list[float] = []
    for r in records:
        try:
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


def _restore_result_session(user_id: str) -> bool:
    """rerun 후 last_session 유실 시 캐시·최신 기록에서 결과 뷰 복원."""
    if st.session_state.get("last_session"):
        return True

    show = st.session_state.get("mypage_show_result") or st.session_state.get(
        "analysis_just_completed"
    )
    if not show:
        return False

    from ui.session_cache import load_session_cache, rebuild_session_from_record

    key = st.session_state.get("last_result_record_key")
    if key:
        cached = load_session_cache(user_id, key)
        if cached:
            st.session_state["last_session"] = cached
            st.session_state["mypage_show_result"] = True
            return True
        for path in list_records(limit=10, user_id=user_id):
            if path.stem == key:
                st.session_state["last_session"] = _load_session_for_record(user_id, path)
                st.session_state["mypage_show_result"] = True
                return True

    if st.session_state.get("analysis_just_completed"):
        paths = list_records(limit=1, user_id=user_id)
        if paths:
            st.session_state["last_session"] = _load_session_for_record(user_id, paths[0])
            st.session_state["last_result_record_key"] = paths[0].stem
            st.session_state["mypage_show_result"] = True
            return True
        try:
            from db_store import list_analysis_records, supabase_configured

            if supabase_configured() and user_id and not str(user_id).startswith("anon_"):
                recs = list_analysis_records(limit=1, user_id=user_id)
                if recs:
                    st.session_state["last_session"] = rebuild_session_from_record(recs[0])
                    st.session_state["mypage_show_result"] = True
                    return True
        except Exception:
            pass

    return False


def _render_login_gate() -> None:
    from ui.auth_ui import render_login_card

    render_login_card(key_prefix="mypage_gate", compact=True)


def _render_history_banner(record: dict, overall: float, song: str, idx: int, path: Path) -> None:
    scores = record.get("stage_scores") or {}
    color = _score_color(overall)
    date_str = _format_date(record)
    date_short = _format_date_short(record)
    pitch = float(scores.get(1) or scores.get("1") or 0)
    rhythm = float(scores.get(2) or scores.get("2") or 0)
    breath = float(scores.get(3) or scores.get("3") or 0)

    render_safe_html(f"""
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
        """
    )
    if st.button(
        f"결과 보기 · {date_short}",
        key=f"mypage_open_{idx}",
        use_container_width=True
    ):
        user_id = current_user_id()
        if user_id:
            from ui.loading import mark_loading

            mark_loading(message="결과를 불러오고 있어요…")
            clear_results_state()
            st.session_state["last_session"] = _load_session_for_record(user_id, path)
            st.session_state["mypage_show_result"] = True
            st.rerun()


def _render_cloud_record_card(record: dict, idx: int, user_id: str) -> None:
    """Supabase analysis_records — 카드 + 결과 보기."""
    from ui.session_cache import rebuild_session_from_record

    overall = float(record.get("overall_score") or 0)
    song = record.get("song_title") or record.get("user_recording") or "녹음"
    mbti = record.get("vocal_mbti") or record.get("vocal_title") or ""
    color = _score_color(overall)
    date_short = _format_date_short(record)
    date_str = _format_date(record)
    scores = record.get("stage_scores") or {}
    pitch = float(scores.get(1) or scores.get("1") or 0)
    rhythm = float(scores.get(2) or scores.get("2") or 0)
    breath = float(scores.get(3) or scores.get("3") or 0)
    mbti_line = f" · {html.escape(mbti)}" if mbti else ""

    render_safe_html(
        f"""
        <div class="vc-history-banner" style="--banner-accent:{color}">
            <div class="vc-history-banner-left">
                <span class="vc-history-date">{html.escape(date_short)}</span>
                <p class="vc-history-song">{html.escape(str(song))}{mbti_line}</p>
                <p class="vc-history-sub">{html.escape(date_str)} · 음{pitch:.0f} · 박{rhythm:.0f} · 호{breath:.0f} · ☁️ 클라우드</p>
            </div>
            <div class="vc-history-score">
                <span class="vc-history-overall">{overall:.0f}</span>
                <span class="vc-history-score-label">점</span>
            </div>
        </div>
        """
    )
    if st.button(
        f"결과 보기 · {date_short}",
        key=f"cloud_open_{idx}_{record.get('_storage_id', idx)}",
        use_container_width=True,
    ):
        from ui.loading import mark_loading

        mark_loading(message="클라우드에서 결과를 불러오고 있어요…")
        clear_results_state()
        st.session_state["last_session"] = rebuild_session_from_record(record)
        st.session_state["mypage_show_result"] = True
        st.rerun()


def _render_cloud_history_expander(user_id: str) -> None:
    """로그인 유저 — Supabase 과거 분석 기록."""
    if not is_logged_in() or str(user_id).startswith("anon_"):
        return
    try:
        from db_store import list_analysis_records, supabase_configured

        if not supabase_configured():
            return
        records = list_analysis_records(limit=30, user_id=user_id)
    except Exception:
        return

    with st.expander("📂 과거 분석 기록 보기", expanded=bool(records)):
        if not records:
            st.info("아직 분석 기록이 없습니다. 첫 노래를 녹음해 보세요! 🎤")
            return
        st.caption("클라우드에 저장된 기록 · 언제 어디서 로그인해도 동일하게 보입니다.")
        for idx, record in enumerate(records):
            _render_cloud_record_card(record, idx, user_id)
    summary = compute_weekly_summary(user_id)
    if summary.get("total_records", 0) == 0:
        return

    count = summary["count"]
    avg = summary.get("avg_score")
    delta = summary.get("delta")
    best = summary.get("best_score")
    top_song = summary.get("top_song") or "—"
    message = summary.get("message") or ""

    avg_txt = f"{avg:.0f}점" if avg is not None else "—"
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        delta_txt = f"{sign}{delta:.1f}pt"
        delta_cls = "vc-week-delta-up" if delta >= 0 else "vc-week-delta-down"
    else:
        delta_txt = "—"
        delta_cls = "vc-week-delta-neutral"

    best_txt = f"{best:.0f}점" if best is not None else "—"

    render_safe_html(
        f"""
        <div class="vc-weekly-card">
            <div class="vc-weekly-head">
                <p class="vc-weekly-title">📅 이번 주 연습 요약</p>
                <span class="vc-weekly-range">최근 7일</span>
            </div>
            <div class="vc-weekly-grid">
                <div class="vc-weekly-stat">
                    <span class="vc-weekly-val">{count}회</span>
                    <span class="vc-weekly-lbl">분석</span>
                </div>
                <div class="vc-weekly-stat">
                    <span class="vc-weekly-val">{avg_txt}</span>
                    <span class="vc-weekly-lbl">평균</span>
                </div>
                <div class="vc-weekly-stat">
                    <span class="vc-weekly-val {delta_cls}">{delta_txt}</span>
                    <span class="vc-weekly-lbl">전주 대비</span>
                </div>
                <div class="vc-weekly-stat">
                    <span class="vc-weekly-val">{best_txt}</span>
                    <span class="vc-weekly-lbl">주간 최고</span>
                </div>
            </div>
            <p class="vc-weekly-song">🎵 많이 연습한 곡 · {html.escape(str(top_song))}</p>
            <p class="vc-weekly-msg">{html.escape(message)}</p>
        </div>
        """
    )


def _render_growth_trend_chart(user_id: str) -> None:
    """최근 5회 종합 점수 — Plotly 트렌드 + 예상 성장 가이드."""
    records = load_all_records_chronological(user_id)
    if not records:
        return

    streak = compute_practice_streak(records)
    points = recent_overall_scores(records, limit=5)
    labels = [p[0] for p in points]
    scores = [p[1] for p in points]

    st.markdown("##### 📈 나의 보컬 히스토리")
    if streak >= 2:
        render_safe_html(
            f'<p class="vc-streak-badge">🔥 연속 <b>{streak}일</b> 연습 달성!</p>'
        )
    elif len(records) == 1:
        st.caption("내일도 녹음하면 성장 그래프가 이어져요.")

    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=scores,
                mode="lines+markers",
                name="종합 점수",
                line=dict(color="#6366f1", width=3),
                marker=dict(size=10, color="#6366f1")
            )
        )
        if len(scores) == 1:
            projected = [scores[0], min(100.0, scores[0] + 6.0)]
            fig.add_trace(
                go.Scatter(
                    x=[labels[0], "다음"],
                    y=projected,
                    mode="lines",
                    name="예상 성장",
                    line=dict(color="#a5b4fc", width=2, dash="dot")
                )
            )
        elif len(scores) >= 2:
            import numpy as np

            x_idx = list(range(len(scores)))
            coef = np.polyfit(x_idx, scores, 1)
            trend = np.poly1d(coef)
            fig.add_trace(
                go.Scatter(
                    x=labels,
                    y=[float(trend(i)) for i in x_idx],
                    mode="lines",
                    name="추세",
                    line=dict(color="#a5b4fc", width=2, dash="dot")
                )
            )

        fig.update_layout(
            height=280,
            margin=dict(l=8, r=8, t=28, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 105], title="", gridcolor="rgba(99,102,241,0.12)"),
            xaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            title=dict(text=f"최근 {len(scores)}회 · 최고 {max(scores):.0f}점", x=0, font=dict(size=13))
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        import pandas as pd

        st.line_chart(pd.DataFrame({"점수": scores}, index=labels))


def _render_hub(user_id: str, name: str, records_paths: list[Path]) -> None:
    cloud_records: list[dict] = []
    if is_logged_in() and not str(user_id).startswith("anon_"):
        try:
            from db_store import list_analysis_records, supabase_configured

            if supabase_configured():
                cloud_records = list_analysis_records(limit=50, user_id=user_id)
        except Exception:
            pass

    if cloud_records:
        stats = _record_stats_from_cloud(cloud_records)
    else:
        stats = _record_stats(records_paths)
    try:
        from db_store import cloud_record_count, storage_mode

        storage_hint = "클라우드+로컬" if storage_mode() == "supabase" else "기기 로컬"
        cloud_n = cloud_record_count(user_id) if storage_mode() == "supabase" else None
        if cloud_n is not None:
            storage_hint += f" · 클라우드 {cloud_n}건"
    except Exception:
        storage_hint = "기기 로컬"
    render_safe_html(
        f"""
        <div class="vc-page-head">
            <h2 class="vc-page-title">{html.escape(name)}님의 마이 페이지 🎤</h2>
            <p class="vc-page-desc">새 분석 · 완료 기록 · 성장 곡선을 한곳에서 · 저장: {html.escape(storage_hint)}</p>
        </div>
        <div class="vc-mypage-stats">
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['count']}</span><span class="vc-mypage-stat-lbl">분석 횟수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['latest']:.0f}</span><span class="vc-mypage-stat-lbl">최근 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['best']:.0f}</span><span class="vc-mypage-stat-lbl">최고 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['avg']:.0f}</span><span class="vc-mypage-stat-lbl">평균</span></div>
        </div>
        """
    )

    _render_weekly_summary_card(user_id)

    if records_paths:
        _render_growth_trend_chart(user_id)
    elif cloud_records:
        _render_growth_trend_chart(user_id)

    _render_cloud_history_expander(user_id)

    try:
        from ui.beta import render_beta_invite_card

        with st.expander("📣 베타 테스터 초대", expanded=False):
            render_beta_invite_card()
    except Exception:
        pass

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
            st.markdown("##### 📈 연습 히스토리")
            spark = generate_history_sparkline(user_id=user_id)
            if spark and spark.exists():
                render_safe_html('<div class="vc-graph-frame vc-sparkline-frame">')
                st.image(str(spark), use_container_width=True)
                render_safe_html("</div>")
            render_safe_html("##### 📈 성장 곡선")
            chart_path = generate_growth_chart(user_id=user_id)
            if chart_path and chart_path.exists():
                render_safe_html('<div class="vc-graph-frame">')
                st.image(str(chart_path), use_container_width=True)
                render_safe_html("</div>")
    else:
        render_safe_html(
            """
            <div class="vc-empty-card">
                <p class="vc-empty-title">아직 분석 기록이 없어요</p>
                <p class="vc-empty-desc">아래에서 녹음을 올리고 첫 분석을 시작해 보세요.</p>
            </div>
            """
        )

    st.divider()
    st.markdown("##### 🎙️ 새 분석")
    from ui.legal_footer import render_upload_privacy_notice

    render_upload_privacy_notice()
    dashboard.render_analysis_section(show_settings=True)


def render() -> None:
    from ui.lazy_auth import resolve_analysis_user_id

    resolve_analysis_user_id()

    user = current_user()
    user_id = current_user_id() or resolve_analysis_user_id()
    name = user.get("name", "게스트") if user else "게스트"

    if not user_id:
        st.warning("세션을 시작할 수 없습니다. 페이지를 새로고침해 주세요.")
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

    if st.session_state.get("mypage_show_result") or st.session_state.get(
        "analysis_just_completed"
    ):
        _restore_result_session(user_id)

    if st.session_state.get("last_session") and (
        st.session_state.get("mypage_show_result")
        or st.session_state.get("analysis_just_completed")
    ):
        from ui.analysis_overlay import clear_analyze_stage

        clear_analyze_stage()
        st.session_state.pop("analysis_just_completed", None)
        if st.session_state.pop("scroll_result", False):
            from ui.scroll import scroll_to_top

            scroll_to_top(anchor_id="vc-result-top")
        if st.button("← 기록 목록으로", key="mypage_back_list", type="secondary"):
            clear_results_state()
            st.rerun()
        dashboard.render_results_view()
        from ui.legal_footer import render_legal_footer

        render_legal_footer(compact=True)
        from ui.beta import render_beta_footer

        render_beta_footer()
        return

    records_paths = list_records(limit=50, user_id=user_id)
    _render_hub(user_id, name, records_paths)

    from ui.beta import render_beta_footer

    render_beta_footer()

    if not dashboard.is_analyzing() and not st.session_state.get("mypage_show_result"):
        from ui.b2c_theme import render_floating_cta

        render_floating_cta(variant="mypage")

    if st.button("💬 서비스 피드백 남기기", use_container_width=True, key="mypage_feedback"):
        go_to("피드백")
