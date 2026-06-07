"""PayLink 스타일 SaaS 대시보드 — Vocal Coach AI."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from progress_tracker import list_records, load_record
from weekly_summary import compute_weekly_summary
from ui.auth import current_user_id, is_logged_in, logout
from ui import dashboard
from ui.safe_user import normalize_session_user, safe_nickname
from ui.session_reset import clear_results_state

MY_PAGE_BUILD = "2026-06-07-dash-v9"
_WEEKLY_GOAL = 3
_VIEWS = ("dashboard", "analyze", "history", "settings")


def _inject_dashboard_css() -> None:
    st.markdown(
        """
        <style>
        .vc-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0 1.5rem;
        }
        @media (max-width: 768px) {
            .vc-stat-grid { grid-template-columns: 1fr; }
        }
        .vc-stat-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid rgba(0,0,0,0.04);
        }
        .vc-stat-label {
            margin: 0 0 0.5rem;
            font-size: 0.85rem;
            color: #64748b;
        }
        .vc-stat-value {
            margin: 0;
            font-size: 1.75rem;
            font-weight: 700;
            color: #1e293b;
        }
        .vc-stat-unit {
            font-size: 0.9rem;
            font-weight: 500;
            color: #94a3b8;
            margin-left: 2px;
        }
        .vc-recent-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.85rem 1rem;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin-bottom: 0.5rem;
        }
        .vc-recent-song { font-weight: 600; color: #1e293b; }
        .vc-recent-badge {
            display: inline-block;
            margin-left: 0.5rem;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            font-size: 0.75rem;
            background: #eef2ff;
            color: #4338ca;
        }
        .vc-empty-box {
            text-align: center;
            padding: 2.5rem 1rem;
            color: #64748b;
            background: #f8f9fa;
            border-radius: 12px;
            margin-top: 0.5rem;
        }
        .vc-gnb-right {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _safe_records(records) -> list:
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


def _load_merged_records(user_id: str, paths: list[Path]) -> list[dict]:
    cloud: list[dict] = []
    if is_logged_in() and user_id and not str(user_id).startswith("anon_"):
        try:
            from db_store import list_analysis_records, supabase_configured

            if supabase_configured():
                cloud = _safe_records(list_analysis_records(limit=50, user_id=user_id))
        except Exception:
            cloud = []
    if cloud:
        return cloud

    out: list[dict] = []
    for p in paths:
        try:
            r = load_record(p)
            r["_storage_id"] = p.stem
            r["_local_path"] = str(p)
            out.append(r)
        except Exception:
            continue
    return out


def _weekly_metrics(user_id: str, records: list[dict]) -> dict:
    count, avg, best = 0, 0.0, 0.0
    try:
        summary = compute_weekly_summary(user_id) or {}
        count = int(summary.get("count") or 0)
        if summary.get("avg_score") is not None:
            avg = float(summary["avg_score"])
        if summary.get("best_score") is not None:
            best = float(summary["best_score"])
    except Exception:
        pass

    if records:
        scores = [float(r.get("overall_score") or 0) for r in records if isinstance(r, dict)]
        if scores and count == 0:
            count = len(scores)
            avg = sum(scores) / len(scores)
            best = max(scores)

    remaining = max(0, _WEEKLY_GOAL - count)
    return {"count": count, "avg": avg, "best": best, "remaining": remaining}


def _status_badge(record: dict) -> str:
    scores = record.get("stage_scores") or {}
    rhythm = float(scores.get(2) or scores.get("2") or 100)
    pitch = float(scores.get(1) or scores.get("1") or 100)
    overall = float(record.get("overall_score") or 0)
    if rhythm < 60:
        return "⚠️ 박자 연체됨"
    if pitch < 60:
        return "⚠️ 음정 주의!"
    if overall >= 85:
        return "📈 성장 중!"
    if overall >= 70:
        return "👀 분석 완료!"
    return "💪 더 연습해요!"


def _render_gnb() -> None:
    nickname = safe_nickname()
    st.markdown(
        f'<div aria-hidden="true" data-vc-build="{MY_PAGE_BUILD}"></div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([4, 1], gap="small", vertical_alignment="center")
    with left:
        st.markdown("### ⚡️ Vocal Coach AI")
    with right:
        rc1, rc2 = st.columns([1.2, 1], gap="small", vertical_alignment="center")
        with rc1:
            st.markdown(f"<p style='text-align:right;margin:0;'>{html.escape(nickname)}님</p>", unsafe_allow_html=True)
        with rc2:
            if st.button("로그아웃", key="gnb_logout", type="secondary", use_container_width=True):
                logout()


def _render_sidebar() -> None:
    view = st.session_state.get("mypage_view", "dashboard")
    menu = (
        ("dashboard", "🏠", "홈 (대시보드)"),
        ("analyze", "🎤", "새 청구서(보컬 분석) 1분 만에 만들기"),
        ("history", "📈", "클라이언트 주소록(내 연습 기록)"),
        ("settings", "⚙️", "설정"),
    )
    with st.sidebar:
        st.markdown("**Vocal Coach**")
        st.caption("보컬 실력 관리 대시보드")
        for key, icon, label in menu:
            if st.button(
                f"{icon}  {label}",
                key=f"sb_{key}",
                use_container_width=True,
                type="primary" if view == key else "secondary",
            ):
                if key != view:
                    st.session_state["mypage_view"] = key
                    if key == "analyze":
                        st.session_state.pop("mypage_show_result", None)
                        clear_results_state()
                    st.rerun()


def _render_stat_cards(metrics: dict) -> None:
    count = int(metrics.get("count") or 0)
    avg = float(metrics.get("avg") or 0)
    best = float(metrics.get("best") or 0)
    avg_txt = f"{avg:.0f}" if count else "0"
    best_txt = f"{best:.0f}" if count else "0"
    count_txt = str(count)

    cards = (
        ("이번 주 평균 점수", avg_txt, "점"),
        ("누적 연습 횟수", count_txt, "회"),
        ("최고 스탯 점수", best_txt, "점"),
    )
    items = []
    for label, val, unit in cards:
        items.append(
            f'<div class="vc-stat-card">'
            f'<p class="vc-stat-label">{html.escape(label)}</p>'
            f'<p class="vc-stat-value">{html.escape(val)}'
            f'<span class="vc-stat-unit">{html.escape(unit)}</span></p></div>'
        )
    st.markdown(
        f'<div class="vc-stat-grid">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def _render_dashboard(user_id: str, paths: list[Path]) -> None:
    nickname = safe_nickname()
    records = _safe_records(_load_merged_records(user_id, paths))
    metrics = _weekly_metrics(user_id, records)
    remaining = int(metrics.get("remaining") or _WEEKLY_GOAL)

    st.info(
        f"안녕하세요, {nickname} 사장님(보컬러님)! 👋\n\n"
        f"이번 주, 아직 분석하지 않은 목표 곡이 **{remaining}곡** 남았어요."
    )

    if st.button(
        "＋ 새 노래 1분 만에 분석하기",
        type="primary",
        use_container_width=True,
        key="dash_cta",
    ):
        st.session_state["mypage_view"] = "analyze"
        st.rerun()

    try:
        _render_stat_cards(metrics)
    except Exception:
        _render_stat_cards({"count": 0, "avg": 0, "best": 0})

    st.markdown("#### 📝 최근 보컬 분석 내역")
    if not records:
        st.markdown(
            '<div class="vc-empty-box">📝 아직 보컬 분석 내역이 없습니다.</div>',
            unsafe_allow_html=True,
        )
        return

    for idx, record in enumerate(records[:5]):
        if not isinstance(record, dict):
            continue
        song = record.get("song_title") or record.get("user_recording") or "녹음"
        badge = _status_badge(record)
        st.markdown(
            f'<div class="vc-recent-row">'
            f'<span class="vc-recent-song">{html.escape(str(song))}'
            f'<span class="vc-recent-badge">{html.escape(badge)}</span></span>'
            f'<span>{float(record.get("overall_score") or 0):.0f}점</span></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"상세 · {str(song)[:16]}", key=f"recent_{idx}", use_container_width=True):
            _open_record(record, user_id)


def _render_analyze(user_id: str) -> None:
    st.markdown("#### 🎙️ 새 보컬 분석")
    st.caption("녹음 파일을 올리면 1분 안에 5축 보컬 분석 리포트를 받을 수 있어요.")
    from ui.legal_footer import render_upload_privacy_notice

    render_upload_privacy_notice()
    dashboard.render_analysis_section(show_settings=True)


def _render_history(user_id: str, paths: list[Path]) -> None:
    records = _safe_records(_load_merged_records(user_id, paths))
    st.markdown("#### 📈 내 연습 기록")

    if not records:
        st.markdown(
            '<div class="vc-empty-box">📝 아직 보컬 분석 내역이 없습니다.</div>',
            unsafe_allow_html=True,
        )
        if st.button("＋ 첫 노래 분석하기", type="primary", key="hist_cta"):
            st.session_state["mypage_view"] = "analyze"
            st.rerun()
        return

    for idx, record in enumerate(records[:20]):
        if not isinstance(record, dict):
            continue
        song = record.get("song_title") or record.get("user_recording") or "녹음"
        badge = _status_badge(record)
        overall = float(record.get("overall_score") or 0)
        st.markdown(
            f'<div class="vc-recent-row">'
            f'<span class="vc-recent-song">{html.escape(str(song))}'
            f'<span class="vc-recent-badge">{html.escape(badge)}</span></span>'
            f'<span>{overall:.0f}점</span></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"결과 보기 · {idx + 1}", key=f"hist_{idx}", use_container_width=True):
            _open_record(record, user_id)


def _render_settings() -> None:
    st.markdown("#### ⚙️ 설정")
    st.markdown(f"**닉네임:** {safe_nickname()}")
    user = st.session_state.get("user")
    if isinstance(user, dict) and user.get("email"):
        st.markdown(f"**이메일:** {user['email']}")
    if st.button("로그아웃", key="settings_logout", use_container_width=True):
        logout()


def _load_session_for_record(user_id: str, path: Path) -> dict:
    from ui.session_cache import load_session_cache, rebuild_session_from_record

    cached = load_session_cache(user_id, path.stem)
    if cached:
        return cached
    return rebuild_session_from_record(load_record(path), path)


def _open_record(record: dict, user_id: str) -> None:
    from ui.loading import mark_loading
    from ui.session_cache import rebuild_session_from_record

    mark_loading(message="결과를 불러오고 있어요…")
    clear_results_state()
    local = record.get("_local_path")
    if local and Path(local).exists():
        st.session_state["last_session"] = _load_session_for_record(user_id, Path(local))
        st.session_state["last_result_record_key"] = Path(local).stem
    else:
        st.session_state["last_session"] = rebuild_session_from_record(record)
    st.session_state["mypage_show_result"] = True
    st.rerun()


def _restore_result_session(user_id: str) -> bool:
    """rerun 후 last_session 유실 시 캐시·최신 기록에서 결과 뷰 복원."""
    if st.session_state.get("last_session"):
        return True

    show = st.session_state.get("mypage_show_result") or st.session_state.get("analysis_just_completed")
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


def render() -> None:
    """로그인 사용자 전용 SaaS 대시보드."""
    normalize_session_user()
    _inject_dashboard_css()

    from ui.lazy_auth import resolve_analysis_user_id

    resolve_analysis_user_id()
    user_id = current_user_id() or resolve_analysis_user_id()
    if not user_id:
        st.warning("세션을 시작할 수 없습니다. 페이지를 새로고침해 주세요.")
        return

    if dashboard.is_analyzing():
        from ui.analysis_overlay import close_analyze_stage, open_analyze_stage

        open_analyze_stage()
        dashboard.render_analysis_section(show_settings=False)
        close_analyze_stage()
        return

    if st.session_state.get("mypage_show_result") or st.session_state.get("analysis_just_completed"):
        _restore_result_session(user_id)

    if st.session_state.get("last_session") and (
        st.session_state.get("mypage_show_result") or st.session_state.get("analysis_just_completed")
    ):
        st.session_state.pop("analysis_just_completed", None)
        if st.button("← 기록 목록으로", key="back_list", type="secondary"):
            clear_results_state()
            st.rerun()
        dashboard.render_results_view()
        from ui.legal_footer import render_legal_footer

        render_legal_footer(compact=True)
        return

    _render_gnb()
    _render_sidebar()

    if "mypage_view" not in st.session_state:
        st.session_state["mypage_view"] = "dashboard"
    view = st.session_state.get("mypage_view", "dashboard")
    if view not in _VIEWS:
        view = "dashboard"
        st.session_state["mypage_view"] = view

    paths = _safe_paths(list_records(limit=50, user_id=user_id))

    if view == "analyze":
        _render_analyze(user_id)
    elif view == "history":
        _render_history(user_id, paths)
    elif view == "settings":
        _render_settings()
    else:
        _render_dashboard(user_id, paths)

    from ui.legal_footer import render_legal_footer

    render_legal_footer(compact=True)
