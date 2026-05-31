"""Spotify Wrapped 스타일 Vocal MBTI 공유 카드."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.utils import render_safe_html


def render_wrapped_share_card(session: dict[str, Any]) -> None:
    """인스타 스토리 캡처용 세로형 카드."""
    from coaching_vocab import derive_vocal_title
    from ui.beta import BETA_SHARE_URL

    report = session["report"]
    full_record = session.get("full_record") or {}
    vocal_title = full_record.get("vocal_title") or derive_vocal_title(report.stages)
    overall = report.overall_score
    stages = report.stages[:3]
    stage_html = ""
    for s in stages:
        names = {1: "음정", 2: "박자", 3: "호흡"}
        stage_html += (
            f'<div class="vc-wrapped-stat">'
            f'<span class="vc-wrapped-stat-val">{s.score:.0f}</span>'
            f'<span class="vc-wrapped-stat-lbl">{names.get(s.stage, s.title)}</span>'
            f"</div>"
        )

    app_url = BETA_SHARE_URL.rstrip("/")

    render_safe_html(
        f"""
        <div class="vc-wrapped-card" id="vc-wrapped-share">
            <div class="vc-wrapped-glow"></div>
            <p class="vc-wrapped-eyebrow">VOCAL COACH AI · 2026</p>
            <h2 class="vc-wrapped-title">{html.escape(vocal_title)}</h2>
            <p class="vc-wrapped-score">{overall:.0f}<span>점</span></p>
            <div class="vc-wrapped-stats">{stage_html}</div>
            <p class="vc-wrapped-watermark">Vocal Coach AI에서 내 보컬 스탯 확인하기</p>
            <p class="vc-wrapped-url">{html.escape(app_url)}</p>
        </div>
        """
    )

    try:
        import plotly.graph_objects as go

        labels = ["음정", "박자", "호흡", "종합"]
        values = [
            float(stages[0].score) if len(stages) > 0 else overall,
            float(stages[1].score) if len(stages) > 1 else overall,
            float(stages[2].score) if len(stages) > 2 else overall,
            float(overall),
        ]
        values.append(values[0])
        labels.append(labels[0])
        fig = go.Figure(
            data=go.Scatterpolar(
                r=values,
                theta=labels,
                fill="toself",
                fillcolor="rgba(167,139,250,0.35)",
                line=dict(color="#a78bfa", width=2),
            )
        )
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], showgrid=True, gridcolor="rgba(255,255,255,0.15)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=260,
            margin=dict(l=40, r=40, t=20, b=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        pass

    st.caption("📸 위 카드를 캡처해서 인스타 스토리에 자랑해 보세요!")
    share_text = (
        f"👑 나의 Vocal MBTI는 [{vocal_title}]! 총점 {overall:.0f}점 🎤\n"
        f"Vocal Coach AI → {app_url}"
    )
    st.download_button(
        "📋 공유 텍스트 복사용 다운로드",
        data=share_text,
        file_name="vocal_coach_share.txt",
        mime="text/plain",
        use_container_width=True,
        key="wrapped_share_dl",
    )
