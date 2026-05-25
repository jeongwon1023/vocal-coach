"""마이 페이지 — 로그인 사용자 전용 기록 · 성장."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from progress_chart import generate_growth_chart
from progress_tracker import compare_records, list_records, load_record
from ui.auth import current_user, current_user_id
from ui.components import render_radar_chart, render_score_ring
from ui.navigation import go_to


def _format_date(record: dict) -> str:
    ts = record.get("recorded_at", "")
    return ts.replace("T", " ")[:19] if ts else "날짜 없음"


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
        "latest": scores[0] if scores else 0,
        "avg": sum(scores) / len(scores),
    }


def render() -> None:
    user = current_user()
    user_id = current_user_id()
    name = user.get("name", "학습자") if user else "학습자"

    st.markdown(
        f"""
        <div class="vc-page-head">
            <h2 class="vc-page-title">{name}님의 레슨 기록 📈</h2>
            <p class="vc-page-desc">분석 점수 · 성장 곡선 · 이전 기록과 비교</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not user_id:
        st.warning("로그인 정보를 확인할 수 없습니다.")
        return

    records_paths = list_records(limit=50, user_id=user_id)

    if not records_paths:
        st.markdown(
            """
            <div class="vc-empty-card">
                <p class="vc-empty-title">아직 기록이 없어요</p>
                <p class="vc-empty-desc">「분석」에서 녹음을 올리고<br>「기록 저장」을 켠 채 분석해 보세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎤 분석하러 가기", type="primary", use_container_width=True, key="mypage_go_analysis"):
                go_to("분석")
        with c2:
            if st.button("💬 피드백 남기기", use_container_width=True, key="mypage_go_feedback"):
                go_to("피드백")
        return

    stats = _record_stats(records_paths)
    st.markdown(
        f"""
        <div class="vc-mypage-stats">
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['count']}</span><span class="vc-mypage-stat-lbl">분석 횟수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['latest']:.0f}</span><span class="vc-mypage-stat-lbl">최근 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['best']:.0f}</span><span class="vc-mypage-stat-lbl">최고 점수</span></div>
            <div class="vc-mypage-stat"><span class="vc-mypage-stat-val">{stats['avg']:.0f}</span><span class="vc-mypage-stat-lbl">평균</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### 📈 성장 곡선")
    chart_path = generate_growth_chart(user_id=user_id)
    if chart_path and chart_path.exists():
        st.markdown('<div class="vc-graph-frame">', unsafe_allow_html=True)
        st.image(str(chart_path), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("기록이 더 쌓이면 성장 곡선이 그려져요.")

    st.divider()
    st.markdown("##### 📋 분석 이력")

    for p in records_paths[:12]:
        try:
            r = load_record(p)
        except Exception:
            continue
        scores = r.get("stage_scores") or {}
        overall = float(r.get("overall_score") or 0)
        song = r.get("song_title") or r.get("user_recording") or "녹음"
        st.markdown(
            f"""
            <div class="vc-record-row">
                <div>
                    <p class="vc-record-date">{_format_date(r)}</p>
                    <p class="vc-record-song">{song}</p>
                </div>
                <div class="vc-record-scores">
                    <span class="vc-record-overall">{overall:.0f}</span>
                    <span class="vc-record-sub">음{float(scores.get(1) or scores.get('1') or 0):.0f} · 박{float(scores.get(2) or scores.get('2') or 0):.0f} · 호{float(scores.get(3) or scores.get('3') or 0):.0f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    options = {}
    for p in records_paths:
        try:
            r = load_record(p)
            options[f"{_format_date(r)} · {r.get('song_title') or '녹음'}"] = p
        except Exception:
            continue

    if not options:
        return

    c1, c2 = st.columns(2)
    with c1:
        sel = st.selectbox("상세 보기", list(options.keys()), key="mypage_sel")
    with c2:
        compare_sel = st.selectbox("비교할 기록", ["없음"] + list(options.keys()), key="mypage_cmp")

    path = options[sel]
    record = load_record(path)
    scores = record.get("stage_scores") or {}

    left, right = st.columns([1, 1.2])
    with left:
        render_score_ring(float(record.get("overall_score") or 0), label="선택 기록")
    with right:
        render_radar_chart(scores)

    teacher = (record.get("stage_details") or {}).get("teacher") or {}
    strengths = teacher.get("strengths") or []
    if strengths:
        st.markdown("**🌟 선생님이 칭찬한 점**")
        for s in strengths[:4]:
            st.caption(f"· {s}")

    if compare_sel != "없음" and compare_sel in options and options[compare_sel] != path:
        st.markdown("##### 🔄 기록 비교")
        st.code(compare_records(record, load_record(options[compare_sel])))

    with st.expander("JSON 상세"):
        st.json(record)

    st.download_button(
        "📥 JSON 다운로드",
        json.dumps(record, ensure_ascii=False, indent=2),
        file_name=path.name,
        mime="application/json",
        key="mypage_dl_json",
    )

    st.divider()
    if st.button("💬 서비스 피드백 남기기", use_container_width=True, key="mypage_feedback"):
        go_to("피드백")
