"""대시보드·마이페이지 공통 UI 컴포넌트 — 시각화 중심."""

from __future__ import annotations

import html
import io
import json
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from ui.runtime_env import configure_matplotlib

configure_matplotlib()

from coaching_vocab import STAGE_NAMES, cent_to_words

from ui.text_format import format_step_lines

_STAGE_META: dict[int, tuple[str, str]] = {
    1: ("🎵", "음정"),
    2: ("⏱️", "박자"),
    3: ("🫁", "호흡·음색"),
    4: ("✨", "종합"),
}


def _score_color(score: float) -> str:
    if score >= 85:
        return "#22c55e"
    if score >= 70:
        return "#818cf8"
    if score >= 55:
        return "#f59e0b"
    return "#f87171"


def _score_grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def _dev_severity(cents: float) -> tuple[str, str]:
    if cents >= 50:
        return "high", "많이 틀림"
    if cents >= 25:
        return "mid", "조금 틀림"
    return "low", "살짝 어긋남"


def render_score_ring(score: float, *, label: str = "종합 점수") -> None:
    color = _score_color(score)
    grade = _score_grade(score)
    pct = min(max(score, 0), 100)
    st.markdown(
        f"""
        <div class="vc-score-ring-wrap">
            <div class="vc-score-ring" style="--pct:{pct:.1f}; --ring-color:{color}">
                <div class="vc-score-ring-inner">
                    <span class="vc-score-ring-grade">{grade}</span>
                    <span class="vc-score-ring-val">{score:.0f}</span>
                </div>
            </div>
            <p class="vc-score-ring-label">{label}</p>
            <p class="vc-score-ring-sub">/ 100점</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overall_score(score: float) -> None:
    render_score_ring(score)


def render_stage_score_cards(stages: list[Any]) -> None:
    """영역별 점수 — Streamlit 네이티브 (모바일 HTML 깨짐 방지)."""
    cols = st.columns(3)
    for col, stage in zip(cols, stages[:3]):
        emoji, short = _STAGE_META.get(stage.stage, ("📊", stage.title))
        title = stage.title.split(":")[-1].strip() if ":" in stage.title else short
        grade = _score_grade(stage.score)
        caption = stage.summary[:64] + ("…" if len(stage.summary) > 64 else "")
        pct = min(max(stage.score / 100.0, 0.0), 1.0)
        with col:
            st.markdown(
                f"""
                <div class="vc-stage-native">
                    <p class="vc-stage-native-label">{emoji} {html.escape(title)}</p>
                    <p class="vc-stage-native-score">{stage.score:.0f}<span>{grade}</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(pct, text=f"{stage.score:.0f}점")
            st.caption(caption)


def render_stage_metrics(stages: list[Any]) -> None:
    render_stage_score_cards(stages)


def render_radar_chart(scores: dict[int | str, float]) -> None:
    labels = [STAGE_NAMES[i] for i in (1, 2, 3)]
    values = [float(scores.get(i) or scores.get(str(i)) or 0) for i in (1, 2, 3)]
    values_closed = values + [values[0]]
    angles = [n / 3 * 2 * 3.14159 for n in range(4)]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#18181b")
    ax.set_facecolor("#18181b")

    ax.plot(angles, values_closed, "o-", linewidth=2.8, color="#818cf8", markersize=7)
    ax.fill(angles, values_closed, alpha=0.22, color="#6366f1")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10, color="#d4d4d8")
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="#71717a")
    ax.set_title("영역별 밸런스", pad=18, fontsize=12, color="#fafafa", fontweight="bold")
    ax.grid(color="#3f3f46", alpha=0.85, linestyle="-", linewidth=0.6)
    ax.spines["polar"].set_color("#52525b")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.markdown('<div class="vc-radar-frame">', unsafe_allow_html=True)
    st.image(buf, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_detail_summary_header() -> None:
    st.markdown(
        """
        <div class="vc-detail-hero">
            <div class="vc-detail-hero-icon">📊</div>
            <div>
                <p class="vc-detail-hero-title">상세 분석 리포트</p>
                <p class="vc-detail-hero-sub">그래프 · 영역별 점수 · 코칭 · 다운로드</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _plain_summary(summary: str) -> tuple[str, str]:
    """한 줄 요약(굵게) + 자세한 설명."""
    text = (summary or "").strip()
    if not text:
        return "이 영역을 들어봤어요", "아래 코칭 내용을 참고해 주세요."
    parts = re.split(r"[.!?\n]", text, maxsplit=1)
    headline = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    if len(headline) > 72:
        headline, rest = headline[:72] + "…", text
    return headline, rest or text


def render_coaching_stages(report: Any) -> None:
    for stage in report.stages:
        emoji, short = _STAGE_META.get(stage.stage, ("📋", ""))
        label = short or stage.title
        with st.expander(
            f"{emoji} {label} — {stage.score:.0f}점",
            expanded=(stage.stage == 1),
        ):
            headline, detail = _plain_summary(stage.summary)
            st.markdown(f"**{headline}**")
            if detail and detail != headline:
                st.markdown(detail)

            if not stage.coaching_blocks:
                st.caption("추가 코칭 포인트는 분석 설정에서 GPT 코칭을 켜면 더 자세히 받을 수 있어요.")
                continue

            for block in stage.coaching_blocks:
                result = (block.result or "").strip()
                cause = format_step_lines((block.cause or "").strip())
                solution = format_step_lines((block.solution or "").strip())
                if result:
                    st.markdown(f"**{result}**")
                if cause:
                    st.markdown(cause)
                if solution:
                    st.markdown(solution)
                st.markdown("")


def render_action_plan(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    st.markdown("**🎯 지금 당장 해야 할 3가지**")
    for item in items:
        title = html.escape(str(item.get("title") or ""))
        rx = str(item.get("prescription") or "").strip()
        practice = str(item.get("practice") or "").replace("**", "").strip()
        reason = str(item.get("reason") or "").strip()
        pri = item.get("priority", "?")
        st.markdown(f"**{pri}. {title}**")
        if rx:
            st.markdown(format_step_lines(rx))
        if practice:
            st.markdown(format_step_lines(practice.replace("\n", "\n\n")))
        if reason:
            st.caption(f"💡 왜 먼저? {reason}")
        st.markdown("")


def render_score_feedback(session: dict[str, Any], full_record: dict[str, Any]) -> None:
    """점수 일치 여부 — 보컬 선생님 말투."""
    from teacher_voice import (
        feedback_agree_thanks,
        feedback_comment_label,
        feedback_disagree_placeholder,
        feedback_disagree_prompt,
        feedback_disagree_thanks,
        feedback_intro,
        feedback_no_button,
        feedback_submit_button,
        feedback_yes_button,
    )

    fb_key = f"feedback_done_{full_record.get('recorded_at', '')}"
    overall = full_record.get("overall_score")

    st.markdown('<div class="vc-feedback-panel">', unsafe_allow_html=True)
    st.markdown("#### 🎓 선생님과 함께")

    if st.session_state.get(fb_key):
        msg = st.session_state.get(f"{fb_key}_msg", feedback_agree_thanks())
        st.success(msg)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(feedback_intro(overall))

    try:
        from feedback_trainer import load_calibration

        cal = load_calibration()
        if cal.min_samples_met:
            st.caption(f"📊 커뮤니티 피드백 반영 중 · {cal.summary_ko()}")
        else:
            st.caption(f"📊 {cal.summary_ko()} — 「맞아요/달라요」를 눌러 주시면 점수가 더 정확해져요.")
    except Exception:
        pass

    col_y, col_n = st.columns(2)
    record_path = session.get("record_path")
    record_id = Path(record_path).name if record_path else None

    with col_y:
        if st.button(feedback_yes_button(), key=f"fb_yes_{fb_key}", use_container_width=True):
            from feedback_store import save_feedback

            save_feedback(
                agrees=True,
                record_id=record_id,
                overall_score=overall,
                stage_scores=full_record.get("stage_scores"),
                song_title=full_record.get("song_title"),
                style_preset=full_record.get("style_preset"),
            )
            st.session_state[fb_key] = True
            st.session_state[f"{fb_key}_msg"] = feedback_agree_thanks()
            st.rerun()

    with col_n:
        if st.button(feedback_no_button(), key=f"fb_no_{fb_key}", use_container_width=True):
            st.session_state[f"{fb_key}_ask"] = True
            st.rerun()

    if st.session_state.get(f"{fb_key}_ask") and not st.session_state.get(fb_key):
        st.info(feedback_disagree_prompt())
        comment = st.text_area(
            feedback_comment_label(),
            placeholder=feedback_disagree_placeholder(),
            key=f"fb_comment_{fb_key}",
            height=100,
        )
        if st.button(feedback_submit_button(), key=f"fb_submit_{fb_key}", type="primary"):
            from feedback_store import save_feedback

            save_feedback(
                agrees=False,
                record_id=record_id,
                overall_score=overall,
                stage_scores=full_record.get("stage_scores"),
                song_title=full_record.get("song_title"),
                style_preset=full_record.get("style_preset"),
                comment=comment,
                record_snapshot={
                    k: full_record.get(k)
                    for k in (
                        "overall_score",
                        "stage_scores",
                        "stage_details",
                        "song_title",
                        "style_preset",
                        "mr_likely",
                    )
                },
            )
            st.session_state[fb_key] = True
            st.session_state[f"{fb_key}_msg"] = feedback_disagree_thanks()
            st.session_state.pop(f"{fb_key}_ask", None)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_deviation_table(report: Any) -> None:
    if not report.pitch_deviation_segments:
        st.markdown(
            '<p class="vc-empty-note">✨ 음정 이탈 구간이 거의 없어요 — 아주 안정적이에요!</p>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for seg in report.pitch_deviation_segments[:10]:
        sev, label = _dev_severity(seg.max_deviation_cents)
        rows.append(
            f"""
            <div class="vc-dev-item vc-dev-{sev}">
                <div class="vc-dev-main">
                    <span class="vc-dev-time">{seg.start_sec:.1f}s – {seg.end_sec:.1f}s</span>
                    <span class="vc-dev-note">{seg.note_hint or "—"}</span>
                </div>
                <span class="vc-dev-badge">{label}</span>
            </div>
            """
        )
    st.markdown(
        f"""
        <p class="vc-section-label">🎯 집중 연습 구간</p>
        <div class="vc-dev-list">{"".join(rows)}</div>
        """,
        unsafe_allow_html=True,
    )


def _render_insight_pills(report: Any, full_record: dict[str, Any]) -> None:
    pills: list[str] = []

    dtw = getattr(report, "dtw_result", None)
    if dtw is not None:
        musical = getattr(dtw, "musical_accuracy_percent", None) or getattr(dtw, "accuracy_percent", None)
        if musical is not None:
            pills.append(f'<span class="vc-insight-pill">🎼 음악적 정확도 {musical:.0f}%</span>')
        interval = getattr(dtw, "interval_match_percent", None)
        if interval is not None:
            pills.append(f'<span class="vc-insight-pill">↕ 인터벌 {interval:.0f}%</span>')
        if getattr(dtw, "rubato_detected", False):
            bonus = getattr(dtw, "expressiveness_bonus", 0)
            pills.append(f'<span class="vc-insight-pill vc-insight-accent">🎭 루바토 +{bonus:.0f}</span>')

    preset = getattr(report, "style_preset_label", None)
    if preset:
        pills.append(f'<span class="vc-insight-pill">🎤 {preset}</span>')

    s4 = next((s for s in report.stages if s.stage == 4), None)
    if s4 and s4.details.get("teacher_strengths"):
        for s in s4.details["teacher_strengths"][:2]:
            pills.append(f'<span class="vc-insight-pill vc-insight-good">🌟 {html.escape(str(s))}</span>')

    if pills:
        st.markdown(f'<div class="vc-insight-row">{"".join(pills)}</div>', unsafe_allow_html=True)

    if report.mr_message:
        css = "vc-mr-warn" if report.mr_likely else "vc-mr-info"
        st.markdown(
            f'<p class="vc-mr-note {css}">{report.mr_message}</p>',
            unsafe_allow_html=True,
        )


def render_session_results(session: dict[str, Any]) -> None:
    report = session["report"]
    full_record = session.get("full_record") or {}

    st.markdown('<div class="vc-detail-panel">', unsafe_allow_html=True)

    top_l, top_r = st.columns([1, 1.15])
    with top_l:
        render_score_ring(report.overall_score)
    with top_r:
        scores = full_record.get("stage_scores") or {
            i + 1: s.score for i, s in enumerate(report.stages[:3])
        }
        render_radar_chart(scores)

    st.markdown('<p class="vc-section-label">📈 영역별 점수</p>', unsafe_allow_html=True)
    render_stage_score_cards(report.stages)

    _render_insight_pills(report, full_record)
    render_score_feedback(session, full_record)

    tab_graph, tab_coach, tab_gpt, tab_clips = st.tabs(
        ["🎼 음정 그래프", "📝 코칭 리포트", "🤖 GPT 멘트", "💾 클립 · 다운로드"]
    )

    with tab_graph:
        plot = session.get("plot_path")
        plot_err = session.get("plot_error")
        if plot and Path(plot).exists():
            st.markdown(
                """
                <div class="vc-graph-legend">
                    <span class="vc-legend-pill vc-legend-ok">● 음정 OK</span>
                    <span class="vc-legend-pill vc-legend-bad">● 음정 틀림</span>
                    <span class="vc-legend-pill vc-legend-guide">● 가이드 멜로디</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="vc-graph-frame">', unsafe_allow_html=True)
            st.image(str(plot), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if plot_err:
                st.markdown(
                    f'<p class="vc-empty-note">음정 그래프는 생성되지 않았어요 ({plot_err}). 분석 점수·코칭은 정상이에요.</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<p class="vc-empty-note">이번 분석에서는 음정 그래프 파일이 없어요.</p>',
                    unsafe_allow_html=True,
                )
        render_deviation_table(report)

    with tab_coach:
        render_coaching_stages(report)
        actions = full_record.get("priority_actions") or []
        render_action_plan(actions)
        if session.get("compare_text"):
            st.markdown('<p class="vc-section-label">📊 이전 기록과 비교</p>', unsafe_allow_html=True)
            st.code(session["compare_text"])

    with tab_gpt:
        if session.get("gpt_text"):
            with st.container(border=True):
                st.markdown(session["gpt_text"])
        elif session.get("gpt_error"):
            st.error(session["gpt_error"])
        else:
            st.markdown(
                '<p class="vc-empty-note"><b>분석 설정</b>에서 GPT 코칭을 켜고 다시 분석하면 AI 멘트가 여기에 표시돼요.</p>',
                unsafe_allow_html=True,
            )

    with tab_clips:
        if session.get("record_path"):
            st.markdown(
                f"""
                <div class="vc-download-card">
                    <span class="vc-download-icon">💾</span>
                    <div>
                        <p class="vc-download-title">분석 기록 저장됨</p>
                        <p class="vc-download-path">{session['record_path']}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if session.get("chart_path") and Path(session["chart_path"]).exists():
            st.markdown('<p class="vc-section-label">📈 성장 곡선</p>', unsafe_allow_html=True)
            st.markdown('<div class="vc-graph-frame">', unsafe_allow_html=True)
            st.image(str(session["chart_path"]), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        if session.get("clip_paths"):
            st.markdown('<p class="vc-section-label">🎧 집중 연습 클립</p>', unsafe_allow_html=True)
            for p in session["clip_paths"]:
                p = Path(p)
                if p.exists():
                    st.markdown(
                        f'<p class="vc-clip-name">▶ {p.name}</p>',
                        unsafe_allow_html=True,
                    )
                    st.audio(str(p), format="audio/wav")
        st.markdown(
            """
            <div class="vc-download-card vc-download-action">
                <span class="vc-download-icon">⬇️</span>
                <div>
                    <p class="vc-download-title">분석 JSON 다운로드</p>
                    <p class="vc-download-path">마이페이지·외부 도구 연동용</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            "JSON 파일 받기",
            json.dumps(full_record, ensure_ascii=False, indent=2),
            file_name="analysis_report.json",
            mime="application/json",
            use_container_width=True,
            key="dl_analysis_json",
        )

    st.markdown("</div>", unsafe_allow_html=True)
