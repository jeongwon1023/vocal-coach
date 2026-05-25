"""마이 페이지 — 로그인 사용자 전용 기록."""

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
from ui.components import render_radar_chart
from ui.styles import section_title


def _format_date(record: dict) -> str:
    ts = record.get("recorded_at", "")
    return ts.replace("T", " ")[:19] if ts else "날짜 없음"


def render() -> None:
    user = current_user()
    user_id = current_user_id()
    name = user.get("name", "학습자") if user else "학습자"

    section_title(f"{name}님의 레슨 기록", "로그인한 계정에 저장된 분석만 표시됩니다.")

    if not user_id:
        st.warning("로그인 정보를 확인할 수 없습니다.")
        return

    records_paths = list_records(limit=50, user_id=user_id)

    if not records_paths:
        st.markdown(
            """
            <div class="sx-card" style="text-align:center;padding:2.5rem 1.5rem;">
                <p style="margin:0;font-size:1.05rem;font-weight:700;">아직 기록이 없어요</p>
                <p style="margin:0.75rem 0 0;color:#9ca3af;font-size:0.9rem;">
                    「분석」 메뉴에서 녹음을 업로드하고<br>
                    「기록 저장」을 켠 채 분석해 보세요.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("분석하러 가기", type="primary"):
            from ui.navigation import go_to

            go_to("분석")
        return

    st.markdown("##### 📈 성장 곡선")
    chart_path = generate_growth_chart(user_id=user_id)
    if chart_path and chart_path.exists():
        st.image(str(chart_path), use_container_width=True)

    st.divider()
    st.markdown("##### 📋 분석 이력")

    rows = []
    for p in records_paths:
        try:
            r = load_record(p)
        except Exception:
            continue
        scores = r.get("stage_scores") or {}
        rows.append({
            "날짜": _format_date(r),
            "곡": r.get("song_title") or r.get("user_recording") or "-",
            "종합": f"{float(r.get('overall_score') or 0):.0f}",
            "음정": f"{float(scores.get(1) or scores.get('1') or 0):.0f}",
            "박자": f"{float(scores.get(2) or scores.get('2') or 0):.0f}",
            "호흡": f"{float(scores.get(3) or scores.get('3') or 0):.0f}",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    options = {f"{_format_date(load_record(p))}": p for p in records_paths}

    c1, c2 = st.columns(2)
    with c1:
        sel = st.selectbox("기록 선택", list(options.keys()))
    with c2:
        compare_sel = st.selectbox("비교할 이전 기록", ["없음"] + list(options.keys()))

    if not sel:
        return

    path = options[sel]
    record = load_record(path)
    scores = record.get("stage_scores") or {}

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("종합", f"{float(record.get('overall_score') or 0):.0f}")
    m2.metric("음정", f"{float(scores.get(1) or scores.get('1') or 0):.0f}")
    m3.metric("박자", f"{float(scores.get(2) or scores.get('2') or 0):.0f}")
    m4.metric("호흡·음색", f"{float(scores.get(3) or scores.get('3') or 0):.0f}")

    left, right = st.columns(2)
    with left:
        render_radar_chart(scores)
    with right:
        st.markdown(f"**기준 멜로디**  \n{record.get('reference_source', '-')}")
        teacher = (record.get("stage_details") or {}).get("teacher") or {}
        strengths = teacher.get("strengths") or []
        if strengths:
            st.markdown("**선생님이 칭찬한 점**")
            for s in strengths[:4]:
                st.caption(f"· {s}")

    if compare_sel != "없음" and compare_sel in options and options[compare_sel] != path:
        st.markdown("##### 🔄 기록 비교")
        st.text(compare_records(record, load_record(options[compare_sel])))

    with st.expander("JSON 상세"):
        st.json(record)

    st.download_button(
        "📥 JSON 다운로드",
        json.dumps(record, ensure_ascii=False, indent=2),
        file_name=path.name,
        mime="application/json",
    )
