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

_WEEKLY_GOAL = 3
_MYPAGE_VIEWS = ("dashboard", "analyze", "history", "settings")
MY_PAGE_BUILD = "2026-06-07-dash-v3"


def _safe_records(records) -> list:
    """None / 비 iterable 방어 — TypeError 크래시 방지."""
    if records is None:
        return []
    if isinstance(records, list):
        return records
    try:
        return list(records)
    except TypeError:
        return []


def _safe_paths(paths) -> list[Path]:
    if paths is None:
        return []
    return list(paths) if paths else []


def _record_status_badge(record: dict) -> str:
    scores = record.get("stage_scores") or {}
    rhythm = float(scores.get(2) or scores.get("2") or 100)
    pitch = float(scores.get(1) or scores.get("1") or 100)
    overall = float(record.get("overall_score") or 0)
    if rhythm < 60:
        return "⚠️ 박자 주의!"
    if pitch < 60:
        return "⚠️ 음정 주의!"
    if overall >= 85:
        return "📈 성장 중!"
    if overall >= 70:
        return "👀 분석 완료!"
    return "💪 더 연습해요!"


def _load_merged_records(user_id: str, records_paths: list[Path]) -> list[dict]:
    """클라우드 우선 + 로컬 fallback (None-safe)."""
    records_paths = _safe_paths(records_paths)
    cloud_records: list[dict] = []
    if is_logged_in() and user_id and not str(user_id).startswith("anon_"):
        try:
            from db_store import list_analysis_records, supabase_configured

            if supabase_configured():
                cloud_records = _safe_records(list_analysis_records(limit=50, user_id=user_id))
        except Exception:
            cloud_records = []

    if cloud_records:
        return cloud_records

    local: list[dict] = []
    for p in records_paths:
        try:
            r = load_record(p)
            r["_storage_id"] = p.stem
            r["_local_path"] = str(p)
            local.append(r)
        except Exception:
            continue
    return local


def _weekly_display_metrics(user_id: str, records: list[dict]) -> dict:
    """대시보드 st.metric용 — 데이터 없으면 0."""
    count = 0
    avg = 0.0
    best = 0.0
    try:
        summary = compute_weekly_summary(user_id) or {}
        count = int(summary.get("count") or 0)
        if summary.get("avg_score") is not None:
            avg = float(summary["avg_score"])
        if summary.get("best_score") is not None:
            best = float(summary["best_score"])
    except Exception:
        summary = {}

    if records:
        scores = [float(r.get("overall_score") or 0) for r in records]
        if scores and best == 0:
            best = max(scores)
        if scores and avg == 0 and count == 0:
            avg = sum(scores) / len(scores)
            count = len(records)
            best = max(scores)

    remaining = max(0, _WEEKLY_GOAL - count)
    return {"avg": avg, "best": best, "count": count, "remaining_goal": remaining}


def _render_empty_state(*, compact: bool = False) -> None:
    render_safe_html(
        """
        <div class="vc-empty-card vc-dash-empty">
            <p class="vc-empty-emoji">🎤</p>
            <p class="vc-empty-title">아직 분석 기록이 없습니다</p>
            <p class="vc-empty-desc">아래 버튼을 눌러 첫 노래를 분석해 보세요! 🎤</p>
        </div>
        """
    )
    if not compact:
        st.caption("위 **[+ 새 노래 1분 만에 분석하기]** 버튼으로 바로 시작할 수 있어요.")


def _render_saas_sidebar() -> None:
    """PayLink 스타일 — 좌측 SaaS 네비게이션."""
    view = st.session_state.get("mypage_view", "dashboard")
    with st.sidebar:
        render_safe_html(
            """
            <div class="vc-dash-sidebar-brand">
                <span class="vc-dash-sidebar-logo">🎤</span>
                <span class="vc-dash-sidebar-name">Vocal Coach</span>
            </div>
            <p class="vc-dash-sidebar-caption">보컬 실력 관리 대시보드</p>
            """
        )
        menu = (
            ("dashboard", "🏠", "홈 (대시보드)"),
            ("analyze", "🎤", "새 보컬 분석"),
            ("history", "📈", "내 연습 기록"),
            ("settings", "⚙️", "설정"),
        )
        for key, icon, label in menu:
            active = view == key
            if st.button(
                f"{icon}  {label}",
                key=f"mypage_sb_{key}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                if key != view:
                    st.session_state["mypage_view"] = key
                    if key == "analyze":
                        st.session_state.pop("mypage_show_result", None)
                        clear_results_state()
                    st.rerun()

        user = current_user()
        if user:
            st.divider()
            st.caption(f"👤 {user.get('name', '학습자')}")


def _open_record_detail(record: dict, user_id: str, *, path: Path | None = None) -> None:
    from ui.loading import mark_loading
    from ui.session_cache import rebuild_session_from_record

    mark_loading(message="결과를 불러오고 있어요…")
    clear_results_state()
    if path is not None:
        st.session_state["last_session"] = _load_session_for_record(user_id, path)
        st.session_state["last_result_record_key"] = path.stem
    else:
        st.session_state["last_session"] = rebuild_session_from_record(record)
    st.session_state["mypage_show_result"] = True
    st.rerun()


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


def _record_stats_from_cloud(records: list[dict] | None) -> dict:
    records = _safe_records(records)
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
                recs = _safe_records(list_analysis_records(limit=1, user_id=user_id))
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
        records = _safe_records(list_analysis_records(limit=30, user_id=user_id))
    except Exception:
        return

    with st.expander("📂 과거 분석 기록 보기", expanded=bool(records)):
        if not records:
            _render_empty_state(compact=True)
            return
        st.caption("클라우드에 저장된 기록 · 언제 어디서 로그인해도 동일하게 보입니다.")
        for idx, record in enumerate(records):
            _render_cloud_record_card(record, idx, user_id)


def _render_weekly_summary_card(user_id: str) -> None:
    """이번 주 연습 요약 — 기록 없으면 조용히 스킵."""
    try:
        summary = compute_weekly_summary(user_id)
    except Exception:
        st.info("주간 연습 요약을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        return

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


def _render_saas_dashboard(user_id: str, name: str, records_paths: list[Path]) -> None:
    """SaaS B2B 스타일 홈 대시보드 — PayLink 매핑."""
    records = _load_merged_records(user_id, records_paths)
    metrics = _weekly_display_metrics(user_id, records)
    nickname = html.escape(name or "게스트")

    render_safe_html(
        f"""
        <div class="vc-dash-header">
            <h1 class="vc-dash-greeting">안녕하세요, {nickname} 보컬러님! 👋</h1>
        </div>
        """
    )

    remaining = metrics["remaining_goal"]
    if remaining > 0:
        st.info(f"이번 주 목표 연습량이 **{remaining}곡** 남았습니다.")
    else:
        st.success("이번 주 목표 연습량을 달성했어요! 🎉")

    if st.button(
        "＋ 새 노래 1분 만에 분석하기",
        type="primary",
        use_container_width=True,
        key="dash_primary_cta",
    ):
        st.session_state["mypage_view"] = "analyze"
        st.rerun()

    st.markdown("#### 📊 주간 연습 흐름")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("이번 주 평균 점수", f"{metrics['avg']:.0f}점")
    with c2:
        st.metric("누적 연습 횟수", f"{metrics['count']}회")
    with c3:
        st.metric("최고 스탯 점수", f"{metrics['best']:.0f}점")

    st.markdown("#### 📝 최근 보컬 분석 내역")
    if not records:
        _render_empty_state()
    else:
        for idx, record in enumerate(records[:3]):
            song = record.get("song_title") or record.get("user_recording") or "녹음"
            overall = float(record.get("overall_score") or 0)
            badge = _record_status_badge(record)
            date_short = _format_date_short(record)
            render_safe_html(
                f"""
                <div class="vc-dash-recent-item">
                    <div class="vc-dash-recent-row">
                        <span class="vc-dash-recent-song">{html.escape(str(song))}</span>
                        <span class="vc-dash-recent-score">{overall:.0f}점</span>
                    </div>
                    <div class="vc-dash-recent-meta">
                        <span>{html.escape(date_short)}</span>
                        <span class="vc-dash-recent-badge">{html.escape(badge)}</span>
                    </div>
                </div>
                """
            )
            if st.button(
                f"상세 보기 · {str(song)[:18]}",
                key=f"dash_recent_{idx}",
                use_container_width=True,
            ):
                local_path = record.get("_local_path")
                path = Path(local_path) if local_path else None
                if path and path.exists():
                    _open_record_detail(record, user_id, path=path)
                else:
                    _open_record_detail(record, user_id)

    if records:
        _render_weekly_summary_card(user_id)
        _render_growth_trend_chart(user_id)


def _render_analyze_view(user_id: str) -> None:
    st.markdown("#### 🎙️ 새 보컬 분석")
    st.caption("녹음 파일을 올리면 1분 안에 5축 보컬 분석 리포트를 받을 수 있어요.")
    from ui.legal_footer import render_upload_privacy_notice

    render_upload_privacy_notice()
    dashboard.render_analysis_section(show_settings=True)


def _render_history_tab(user_id: str, records_paths: list[Path] | None = None) -> None:
    """
    내 연습 기록 탭 — TypeError 원천 차단.
    records가 None이거나 비어 있으면 Empty State만 렌더 (크래시 금지).
    """
    records_paths = _safe_paths(records_paths)
    records = _load_merged_records(user_id, records_paths)

    st.markdown("#### 📈 내 연습 기록")

    if records is None or len(records) == 0:
        if not records_paths:
            _render_empty_state()
            if st.button("첫 분석 시작하기", type="primary", key="history_empty_cta"):
                st.session_state["mypage_view"] = "analyze"
                st.rerun()
            return
        st.info("아직 분석 기록이 없습니다. 아래 버튼을 눌러 첫 노래를 분석해 보세요! 🎤")
        if st.button("＋ 새 노래 분석하기", type="primary", key="history_empty_cta2"):
            st.session_state["mypage_view"] = "analyze"
            st.rerun()
        return

    _render_cloud_history_expander(user_id)

    if records_paths:
        st.markdown("##### 📂 기기 저장 기록")
        for idx, p in enumerate(records_paths[:20]):
            try:
                r = load_record(p)
            except Exception:
                continue
            overall = float(r.get("overall_score") or 0)
            song = r.get("song_title") or r.get("user_recording") or "녹음"
            _render_history_banner(r, overall, song, idx, p)
    else:
        st.caption("클라우드에 저장된 기록입니다.")
        for idx, record in enumerate(records[:20]):
            _render_cloud_record_card(record, idx, user_id)

    if records_paths and len(records_paths) > 1:
        st.markdown("##### 📈 연습 히스토리")
        spark = generate_history_sparkline(user_id=user_id)
        if spark and spark.exists():
            render_safe_html('<div class="vc-graph-frame vc-sparkline-frame">')
            st.image(str(spark), use_container_width=True)
            render_safe_html("</div>")
        chart_path = generate_growth_chart(user_id=user_id)
        if chart_path and chart_path.exists():
            render_safe_html('<div class="vc-graph-frame">')
            st.image(str(chart_path), use_container_width=True)
            render_safe_html("</div>")


def _render_history_view(user_id: str, records_paths: list[Path]) -> None:
    """하위 호환 — _render_history_tab 위임."""
    _render_history_tab(user_id, records_paths)


def _render_settings_view() -> None:
    st.markdown("#### ⚙️ 설정")
    user = current_user()
    if user:
        st.markdown(f"**닉네임:** {user.get('name', '학습자')}")
        if user.get("email"):
            st.markdown(f"**이메일:** {user['email']}")
        provider = {"google": "Google", "kakao": "카카오", "demo": "체험"}.get(
            user.get("provider", ""), user.get("provider", "")
        )
        if provider:
            st.markdown(f"**로그인:** {provider}")
    try:
        from db_store import cloud_record_count, storage_mode

        mode = storage_mode()
        uid = current_user_id()
        hint = "클라우드 + 로컬" if mode == "supabase" else "기기 로컬"
        if mode == "supabase" and uid:
            n = cloud_record_count(uid)
            if n is not None:
                hint += f" · 클라우드 {n}건"
        st.caption(f"저장 방식: {hint}")
    except Exception:
        pass

    if not is_logged_in():
        from ui.auth_ui import render_login_card

        render_login_card(key_prefix="settings_login", compact=True)
        return

    if st.button("로그아웃", key="settings_logout", use_container_width=True):
        from ui.auth import logout

        logout()



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

    records_paths = _safe_paths(list_records(limit=50, user_id=user_id))

    if "mypage_view" not in st.session_state:
        st.session_state["mypage_view"] = "dashboard"
    view = st.session_state.get("mypage_view", "dashboard")
    if view not in _MYPAGE_VIEWS:
        view = "dashboard"
        st.session_state["mypage_view"] = view

    _render_saas_sidebar()

    if view == "analyze":
        _render_analyze_view(user_id)
    elif view == "history":
        _render_history_tab(user_id, records_paths)
    elif view == "settings":
        _render_settings_view()
    else:
        _render_saas_dashboard(user_id, name, records_paths)

    st.caption(f"빌드 {MY_PAGE_BUILD} · SaaS 대시보드")

    from ui.beta import render_beta_footer

    render_beta_footer()

    if not dashboard.is_analyzing() and not st.session_state.get("mypage_show_result"):
        from ui.b2c_theme import render_floating_cta

        render_floating_cta(variant="mypage")

    if st.button("💬 서비스 피드백 남기기", use_container_width=True, key="mypage_feedback"):
        go_to("피드백")
