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

from ui.text_format import (
    format_coach_rich_html,
    format_step_lines,
    normalize_checklist_markdown,
    normalize_markdown_noise,
    sanitize_coach_text,
    solution_to_checklist
)
from ui.utils import render_safe_html

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
    render_safe_html(f"""
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
        """
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
            render_safe_html(
                f"""
                <div class="vc-stage-native">
                    <p class="vc-stage-native-label">{emoji} {html.escape(title)}</p>
                    <p class="vc-stage-native-score">{stage.score:.0f}<span>{grade}</span></p>
                </div>
                """
            )
            st.progress(pct, text=f"{stage.score:.0f}점")
            st.caption(caption)


def render_stage_metrics(stages: list[Any]) -> None:
    render_stage_score_cards(stages)


def render_radar_chart(
    scores: dict[int | str, float] | None = None,
    *,
    report: Any = None,
    full_record: dict[str, Any] | None = None,
    show_insight: bool = True
) -> None:
    """5축 Plotly 레이더 차트 (음정·박자·호흡·발성·표현력)."""
    from vocal_radar import build_vocal_radar_scores, radar_insight_text

    radar: dict[str, float]
    if report is not None:
        radar = build_vocal_radar_scores(report, full_record)
    elif scores:
        radar = {
            "음정": float(scores.get(1) or scores.get("1") or 0),
            "박자": float(scores.get(2) or scores.get("2") or 0),
            "호흡": float(scores.get(3) or scores.get("3") or 0),
            "발성": float(scores.get(3) or scores.get("3") or 0),
            "표현력": float(scores.get(4) or scores.get("4") or 68),
        }
    else:
        radar = {"음정": 0, "박자": 0, "호흡": 0, "발성": 0, "표현력": 0}

    categories = list(radar.keys())
    values = list(radar.values())
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill="toself",
                fillcolor="rgba(99, 102, 241, 0.32)",
                line=dict(color="#6366f1", width=2.8),
                marker=dict(size=9, color="#6366f1"),
                name="보컬 밸런스"
            )
        )
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(248, 246, 255, 0.6)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[25, 50, 75, 100],
                    tickfont=dict(size=10, color="#6e667d"),
                    gridcolor="rgba(196, 189, 212, 0.55)"
                ),
                angularaxis=dict(tickfont=dict(size=12, color="#1c1528", family="Pretendard"))
            ),
            showlegend=False,
            height=340,
            margin=dict(l=44, r=44, t=40, b=28),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            title=dict(text="보컬 밸런스", x=0.5, font=dict(size=14, color="#1c1528"))
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key="vc_vocal_radar_chart"
        )
        if show_insight:
            render_safe_html(
                f'<p class="vc-radar-insight">💬 {html.escape(radar_insight_text(radar))}</p>'
            )
        return
    except Exception:
        pass

    labels = [STAGE_NAMES[i] for i in (1, 2, 3)]
    values3 = [float(scores.get(i) or scores.get(str(i)) or 0) if scores else 0 for i in (1, 2, 3)]
    values_closed3 = values3 + [values3[0]]
    angles = [n / 3 * 2 * 3.14159 for n in range(4)]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#f8f6ff")
    ax.set_facecolor("#f8f6ff")
    ax.plot(angles, values_closed3, "o-", linewidth=2.8, color="#6366f1", markersize=7)
    ax.fill(angles, values_closed3, alpha=0.22, color="#818cf8")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10, color="#52525b")
    ax.set_ylim(0, 100)
    ax.set_title("영역별 밸런스", pad=18, fontsize=12, color="#1c1528", fontweight="bold")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    st.image(buf, use_container_width=True)


def render_detail_summary_header() -> None:
    render_safe_html(
        """
        <div class="vc-detail-hero">
            <div class="vc-detail-hero-icon">📊</div>
            <div>
                <p class="vc-detail-hero-title">상세 분석 리포트</p>
                <p class="vc-detail-hero-sub">그래프 · 영역별 점수 · 코칭 · 다운로드</p>
            </div>
        </div>
        """
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


def _open_card(title: str, *, icon: str = "") -> None:
    label = f"{icon} {title}".strip()
    st.markdown(f"### {label}")


def _close_card() -> None:
    st.markdown("")


def _render_coach_rich(text: str) -> None:
    html_out = format_coach_rich_html(text)
    if html_out:
        render_safe_html(html_out)


def render_coaching_stages(report: Any) -> None:
    """세로 스크롤 — 강점·약점 코칭 (색상·줄바꿈 적용)."""
    for stage in report.stages:
        emoji, short = _STAGE_META.get(stage.stage, ("📋", ""))
        label = short or stage.title
        render_safe_html(f'<div class="vc-coach-stage"><p class="vc-coach-stage-title">'
            f"{emoji} {html.escape(label)} — {stage.score:.0f}점</p></div>"
        )
        headline, detail = _plain_summary(sanitize_coach_text(stage.summary or ""))
        if headline:
            st.markdown(f"**{headline}**")
        if detail and detail != headline:
            _render_coach_rich(detail)

        if not stage.coaching_blocks:
            st.caption("추가 코칭은 아래 AI 코치와 대화하면 더 자세히 받을 수 있어요.")
            st.markdown("")
            continue

        for block in stage.coaching_blocks:
            result = sanitize_coach_text((block.result or "").strip())
            cause = sanitize_coach_text((block.cause or "").strip())
            solution_raw = sanitize_coach_text((block.solution or "").strip())
            if result:
                st.markdown(f"**{result}**")
            if cause:
                _render_coach_rich(cause)
            if solution_raw:
                _render_coach_rich(solution_raw)
            st.markdown("")


def render_action_plan(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    for item in items:
        title = html.escape(str(item.get("title") or ""))
        rx = sanitize_coach_text(str(item.get("prescription") or "").strip())
        practice_raw = str(item.get("practice") or "").replace("**", "").strip()
        practice = practice_raw if practice_raw.startswith("- [ ]") else solution_to_checklist(practice_raw)
        if "- [ ]" in practice:
            practice = normalize_checklist_markdown(practice)
        reason = sanitize_coach_text(str(item.get("reason") or "").strip())
        pri = item.get("priority", "?")
        render_safe_html('<div class="coach-card">')
        render_safe_html(f'<p class="coach-card-title">{pri}. {title}</p>')
        if rx:
            _render_coach_rich(rx)
        if practice:
            if "- [ ]" in practice:
                render_safe_html(practice)
            else:
                _render_coach_rich(practice)
        if reason:
            st.caption(f"💡 왜 먼저? {reason}")
        render_safe_html("</div>")


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
        feedback_yes_button
    )

    fb_key = f"feedback_done_{full_record.get('recorded_at', '')}"
    overall = full_record.get("overall_score")

    render_safe_html('<div class="vc-feedback-panel">')
    render_safe_html("#### 🎓 선생님과 함께")

    if st.session_state.get(fb_key):
        msg = st.session_state.get(f"{fb_key}_msg", feedback_agree_thanks())
        st.success(msg)
        render_safe_html("</div>")
        return

    render_safe_html(feedback_intro(overall))

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
                style_preset=full_record.get("style_preset")
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
            height=100
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
                        "mr_likely"
                    )
                }
            )
            st.session_state[fb_key] = True
            st.session_state[f"{fb_key}_msg"] = feedback_disagree_thanks()
            st.session_state.pop(f"{fb_key}_ask", None)
            st.rerun()

    render_safe_html("</div>")


def render_deviation_table(report: Any) -> None:
    if not report.pitch_deviation_segments:
        render_safe_html('<p class="vc-empty-note">✨ 음정 이탈 구간이 거의 없어요 — 아주 안정적이에요!</p>'
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
    render_safe_html(
        f"""
        <p class="vc-section-label">🎯 집중 연습 구간</p>
        <div class="vc-dev-list">{"".join(rows)}</div>
        """
    )


def render_precision_panel(report: Any, full_record: dict[str, Any] | None = None) -> None:
    """정밀 음정 지표 — Singing Carrots / Yousician 스타일."""
    full_record = full_record or {}
    stage_details = full_record.get("stage_details") or {}
    pitch_d = stage_details.get("pitch") or {}

    s1 = next((s for s in report.stages if s.stage == 1), None)
    details = {**pitch_d, **(s1.details if s1 else {})}

    precision = details.get("precision_ratio")
    sustain = details.get("sustain_ratio_pitch")
    note_hit = details.get("note_hit_ratio")
    transposition = details.get("transposition_cents")
    timing = details.get("timing_score")
    note_count = details.get("note_count")

    if precision is None and sustain is None and note_hit is None:
        return

    def _pct(v: float | None) -> str:
        if v is None:
            return "—"
        return f"{float(v) * 100:.0f}%"

    engine = full_record.get("analysis_engine") or getattr(report, "analysis_engine", {}) or {}
    sep = engine.get("separation", "")
    f0m = engine.get("f0_method", "")
    mode_badge = "정밀" if engine.get("precision_mode") else "빠른"

    sep_ko = {"enhanced_hpss": "강화 HPSS", "demucs": "Demucs AI", "original": "원본"}.get(
        sep, sep or "—"
    )
    engine_line = f"{mode_badge} · {sep_ko}"
    if f0m:
        engine_line += f" · F0 {f0m}"

    trans_html = ""
    if transposition is not None and abs(float(transposition)) >= 10:
        trans_html = (
            f'<div class="vc-precision-chip vc-precision-chip-key">'
            f"조 보정 {float(transposition):+.0f}¢</div>"
        )

    render_safe_html(
        f"""
        <div class="vc-precision-panel">
            <div class="vc-precision-head">
                <p class="vc-precision-title">🎯 정밀 음정 분석</p>
                <span class="vc-precision-engine">{html.escape(engine_line)}</span>
            </div>
            <div class="vc-precision-grid">
                <div class="vc-precision-stat">
                    <span class="vc-precision-val">{_pct(precision)}</span>
                    <span class="vc-precision-label">정밀도<br><small>±장르 허용치</small></span>
                </div>
                <div class="vc-precision-stat">
                    <span class="vc-precision-val">{_pct(sustain)}</span>
                    <span class="vc-precision-label">Sustain<br><small>±5¢ 유지</small></span>
                </div>
                <div class="vc-precision-stat">
                    <span class="vc-precision-val">{_pct(note_hit)}</span>
                    <span class="vc-precision-label">노트 적중<br><small>{note_count or "—"}개</small></span>
                </div>
                <div class="vc-precision-stat">
                    <span class="vc-precision-val">{f"{timing:.0f}" if timing is not None else "—"}</span>
                    <span class="vc-precision-label">타이밍<br><small>/ 100</small></span>
                </div>
            </div>
            {trans_html}
        </div>
        """
    )

    precise_n = details.get("precise_frames")
    if precise_n is not None:
        buckets = [
            ("너무 낮음", details.get("too_low", 0), "#6366f1"),
            ("약간 낮음", details.get("slightly_low", 0), "#818cf8"),
            ("정확", precise_n, "#22c55e"),
            ("약간 높음", details.get("slightly_high", 0), "#f59e0b"),
            ("너무 높음", details.get("too_high", 0), "#f87171"),
        ]
        total = sum(int(b[1] or 0) for b in buckets) or 1
        bars = "".join(
            f'<span class="vc-pitch-bucket" style="--w:{100*int(n or 0)/total:.1f}%;--c:{c}" '
            f'title="{label} {n}"></span>'
            for label, n, c in buckets
            if int(n or 0) > 0
        )
        if bars:
            render_safe_html(
                f"""
                <div class="vc-pitch-quality">
                    <p class="vc-pitch-quality-title">음정 분포 (프레임)</p>
                    <div class="vc-pitch-bucket-row">{bars}</div>
                    <div class="vc-pitch-quality-legend">
                        <span>● 정확</span><span>● 낮음</span><span>● 높음</span>
                    </div>
                </div>
                """
            )


def _render_pdf_download(session: dict[str, Any]) -> None:
    user_id = None
    try:
        from ui.auth import current_user_id

        user_id = current_user_id()
    except Exception:
        pass

    cache_key = session.get("record_path") or str(id(session))
    pdf_state_key = f"vc_pdf_{cache_key}"

    render_safe_html(
        """
        <div class="vc-download-card vc-download-action">
            <span class="vc-download-icon">📄</span>
            <div>
                <p class="vc-download-title">PDF 리포트</p>
                <p class="vc-download-path">점수 · 코칭 · 그래프 · 성장 곡선</p>
            </div>
        </div>
        """
    )

    if st.button("PDF 리포트 만들기", key=f"btn_pdf_{cache_key}", use_container_width=True):
        try:
            from report_pdf import generate_analysis_pdf

            pdf_path = generate_analysis_pdf(session, user_id=user_id)
            if pdf_path and pdf_path.exists():
                st.session_state[pdf_state_key] = str(pdf_path)
            else:
                st.session_state.pop(pdf_state_key, None)
                st.warning("PDF를 만들지 못했어요.")
        except Exception as exc:
            st.error(f"PDF 생성 실패: {exc}")

    pdf_path = st.session_state.get(pdf_state_key)
    if pdf_path and Path(pdf_path).exists():
        st.download_button(
            "PDF 파일 받기",
            Path(pdf_path).read_bytes(),
            file_name=Path(pdf_path).name,
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf_{cache_key}"
        )


def render_note_drill_panel(session: dict[str, Any], full_record: dict[str, Any]) -> None:
    """히트맵 탭 — 노트 선택 · 구간 듣기."""
    note_clips = session.get("note_clip_paths") or []
    note_segments = full_record.get("note_segments") or []
    clip_err = session.get("note_clip_error")

    if not note_clips and not note_segments:
        return

    render_safe_html('<p class="vc-section-label">🎯 노트 선택 · 집중 연습</p>')
    st.caption("히트맵 박스 번호와 동일 · 틀린 노트부터 연습해 보세요.")

    entries: list[dict[str, Any]] = []
    clip_by_start: dict[float, dict] = {}
    for clip in note_clips:
        t0 = round(float(clip.get("start_sec") or 0), 1)
        clip_by_start[t0] = clip

    for idx, seg in enumerate(note_segments, 1):
        midi = seg.get("midi_median", 0)
        try:
            import librosa

            note = librosa.midi_to_note(int(round(midi)), unicode=False)
        except Exception:
            note = f"M{midi:.0f}"
        t0 = float(seg.get("start_sec", 0))
        t1 = float(seg.get("end_sec", t0))
        err = float(seg.get("mean_cents_error", 0))
        hit = bool(seg.get("hit", False))
        clip = clip_by_start.get(round(t0, 1))
        entries.append(
            {
                "idx": idx,
                "note": note,
                "t0": t0,
                "t1": t1,
                "err": err,
                "hit": hit,
                "clip_path": clip.get("path") if clip else None,
                "seg": seg,
            }
        )

    if not entries and note_clips:
        for i, clip in enumerate(note_clips, 1):
            entries.append(
                {
                    "idx": i,
                    "note": clip.get("label") or f"#{i}",
                    "t0": float(clip.get("start_sec") or 0),
                    "t1": float(clip.get("end_sec") or 0),
                    "err": float(clip.get("mean_cents") or 0),
                    "hit": bool(clip.get("hit")),
                    "clip_path": clip.get("path"),
                    "seg": None,
                }
            )

    if not entries:
        if clip_err:
            st.caption(f"노트 클립 생성 실패 ({clip_err})")
        return

    def _label(e: dict) -> str:
        status = "✓" if e["hit"] else f"오차 {e['err']:.0f}¢"
        return f"#{e['idx']} {e['note']} · {e['t0']:.1f}s · {status}"

    misses_first = sorted(entries, key=lambda e: (e["hit"], -e["err"]))
    labels = [_label(e) for e in misses_first]
    label_to_entry = {_label(e): e for e in misses_first}
    pick_idx_key = "vc_note_pick_idx"

    st.caption("히트맵 번호 버튼을 누르면 해당 구간을 재생해요.")
    chip_cols = st.columns(6)
    for i, e in enumerate(misses_first[:18]):
        kind = "primary" if e["idx"] == st.session_state.get(pick_idx_key) else "secondary"
        if chip_cols[i % 6].button(
            f"#{e['idx']}",
            key=f"note_chip_{e['idx']}",
            type=kind,
            use_container_width=True,
            help=f"{e['note']} · {e['t0']:.1f}s"
        ):
            st.session_state[pick_idx_key] = e["idx"]
            st.rerun()

    default_idx = 0
    if pick_idx_key in st.session_state:
        for i, e in enumerate(misses_first):
            if e["idx"] == st.session_state[pick_idx_key]:
                default_idx = i
                break

    selected = st.selectbox(
        "노트 구간",
        options=labels,
        index=default_idx,
        key="vc_note_drill_pick",
        label_visibility="collapsed"
    )
    picked = label_to_entry[selected]
    st.session_state[pick_idx_key] = picked["idx"]

    dur_total = max((e["t1"] for e in entries), default=picked["t1"] + 1.0)
    timeline = "".join(
        f'<span class="vc-note-tick {"vc-note-tick-hit" if e["hit"] else "vc-note-tick-miss"}'
        f'{" vc-note-tick-active" if e["idx"] == picked["idx"] else ""}" '
        f'style="--left:{100 * e["t0"] / max(dur_total, 0.1):.1f}%;'
        f'--width:{max(2.0, 100 * (e["t1"] - e["t0"]) / max(dur_total, 0.1)):.1f}%;" '
        f'title="#{e["idx"]} {html.escape(e["note"])}"></span>'
        for e in entries
    )
    render_safe_html(f'<div class="vc-note-timeline">{timeline}</div>')

    status = "적중" if picked["hit"] else f"오차 {picked['err']:.0f}¢"
    render_safe_html(f"""
        <div class="vc-note-drill-row vc-note-drill-active">
            <span class="vc-note-drill-badge">#{picked["idx"]}</span>
            <div>
                <p class="vc-note-drill-title">{html.escape(str(picked["note"]))} · {picked["t0"]:.1f}–{picked["t1"]:.1f}s</p>
                <p class="vc-note-drill-meta">{html.escape(status)}</p>
            </div>
        </div>
        """
    )

    clip_path = picked.get("clip_path")
    if clip_path and Path(clip_path).exists():
        st.audio(str(clip_path), format="audio/wav")
        return

    audio_src = session.get("audio_path")
    if audio_src and picked.get("seg") and Path(audio_src).exists():
        try:
            from note_clip_exporter import export_single_note_clip

            clip = export_single_note_clip(Path(audio_src), picked["seg"])
            if clip and clip.path.exists():
                st.audio(str(clip.path), format="audio/wav")
                return
        except Exception as exc:
            st.caption(f"구간 재생 준비 실패 ({exc})")

    if clip_err:
        st.caption(f"노트 클립 생성 실패 ({clip_err})")
    else:
        st.caption("이 구간 오디오는 정밀 분석 후 재생할 수 있어요.")


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
        render_safe_html(f'<div class="vc-insight-row">{"".join(pills)}</div>')

    if report.mr_message:
        css = "vc-mr-warn" if report.mr_likely else "vc-mr-info"
        render_safe_html(f'<p class="vc-mr-note {css}">{report.mr_message}</p>'
        )


def _render_pitch_graph(session: dict[str, Any], report: Any) -> None:
    plot = session.get("plot_path")
    plot_err = session.get("plot_error")
    if plot and Path(plot).exists():
        render_safe_html(
            """
            <div class="vc-graph-legend">
                <span class="vc-legend-pill vc-legend-ok">● 음정 OK</span>
                <span class="vc-legend-pill vc-legend-bad">● 음정 틀림</span>
                <span class="vc-legend-pill vc-legend-guide">● 가이드 멜로디</span>
            </div>
            """
        )
        render_safe_html('<div class="vc-graph-frame">')
        st.image(str(plot), use_container_width=True)
        render_safe_html("</div>")
    elif plot_err:
        render_safe_html(f'<p class="vc-empty-note">음정 그래프는 생성되지 않았어요 ({plot_err}). 분석 점수·코칭은 정상이에요.</p>'
        )
    else:
        render_safe_html(
            '<p class="vc-empty-note">이번 분석에서는 음정 그래프 파일이 없어요.</p>'
        )
    render_deviation_table(report)


def _render_heatmap_panel(session: dict[str, Any], report: Any, full_record: dict[str, Any]) -> None:
    heatmap = session.get("heatmap_path")
    heatmap_err = session.get("heatmap_error")
    note_segments = full_record.get("note_segments") or []
    plotly_used = False

    if note_segments:
        try:
            from pitch_heatmap_plotly import (
                build_note_heatmap_figure_from_report,
                extract_selected_note_index,
                plotly_available
            )

            if plotly_available():
                fig = build_note_heatmap_figure_from_report(report)
                if fig is not None:
                    st.caption("노트 번호를 **클릭**하거나 드래그하여 선택하세요.")
                    event = st.plotly_chart(
                        fig,
                        on_select="rerun",
                        key="vc_note_heatmap_plotly",
                        use_container_width=True
                    )
                    sel = extract_selected_note_index(event)
                    if sel is not None:
                        st.session_state["vc_note_pick_idx"] = sel
                    plotly_used = True
        except Exception as exc:
            st.caption(f"인터랙티브 차트 표시 불가 ({exc})")

    if not plotly_used and heatmap and Path(heatmap).exists():
        render_safe_html(
            """
            <p class="vc-graph-legend">
                <span class="vc-legend-pill vc-legend-ok">● 녹색=정확</span>
                <span class="vc-legend-pill vc-legend-bad">● 빨강=벗어남</span>
                · 노트 박스 + 점 = 프레임별 센트
            </p>
            """
        )
        render_safe_html('<div class="vc-graph-frame">')
        st.image(str(heatmap), use_container_width=True)
        render_safe_html("</div>")

    if note_segments or session.get("note_clip_paths"):
        render_note_drill_panel(session, full_record)
    elif heatmap_err:
        st.caption(f"노트 히트맵 생성 실패 ({heatmap_err})")
    elif not plotly_used:
        render_safe_html('<p class="vc-empty-note">정밀 분석 후 노트 히트맵이 여기에 표시됩니다. '
            "⚙️ 분석 설정에서 <b>빠른 분석</b>을 끄고 다시 분석해 보세요.</p>"
        )


def _render_downloads_card(session: dict[str, Any], full_record: dict[str, Any]) -> None:
    if session.get("record_path"):
        render_safe_html(
            f"""
            <div class="vc-download-card">
                <span class="vc-download-icon">💾</span>
                <div>
                    <p class="vc-download-title">분석 기록 저장됨</p>
                    <p class="vc-download-path">{session['record_path']}</p>
                </div>
            </div>
            """
        )
    if session.get("chart_path") and Path(session["chart_path"]).exists():
        render_safe_html('<p class="vc-section-label">📈 성장 곡선</p>')
        render_safe_html('<div class="vc-graph-frame">')
        st.image(str(session["chart_path"]), use_container_width=True)
        render_safe_html("</div>")
    if session.get("clip_paths"):
        render_safe_html('<p class="vc-section-label">🎧 집중 연습 클립</p>')
        for p in session["clip_paths"]:
            p = Path(p)
            if p.exists():
                render_safe_html(f'<p class="vc-clip-name">▶ {p.name}</p>'
                )
                st.audio(str(p), format="audio/wav")
    _render_pdf_download(session)
    render_safe_html(
        """
        <div class="vc-download-card vc-download-action">
            <span class="vc-download-icon">⬇️</span>
            <div>
                <p class="vc-download-title">분석 JSON 다운로드</p>
                <p class="vc-download-path">마이페이지·외부 도구 연동용</p>
            </div>
        </div>
        """
    )
    st.download_button(
        "JSON 파일 받기",
        json.dumps(full_record, ensure_ascii=False, indent=2),
        file_name="analysis_report.json",
        mime="application/json",
        use_container_width=True,
        key="dl_analysis_json"
    )


def _render_sandwich_triptych(
    session: dict[str, Any],
    report: Any,
    full_record: dict[str, Any]
) -> None:
    """👍 잘한 점 · 🎯 아쉬운 점 · 💡 오늘 처방전 — 3분할 카드 (모바일 세로 스택)."""
    from ui.coach_insights import build_focus_items, build_strength_items

    strengths = build_strength_items(session)
    focus_items = build_focus_items(session)
    actions = full_record.get("priority_actions") or []

    good = strengths[0] if strengths else {
        "headline": "오늘도 연습하러 와 주셔서 감사해요",
        "detail": "꾸준히 녹음하면 실력 변화를 숫자로 확인할 수 있어요.",
    }

    weak = focus_items[0] if focus_items else {"headline": "전체적으로 골고루", "detail": "약한 영역 위주로 짧게 반복해 보세요."}
    weakest = min(report.stages[:3], key=lambda s: s.score) if report.stages else None
    if weakest and weakest.coaching_blocks:
        block = weakest.coaching_blocks[0]
        weak = {
            "headline": sanitize_coach_text((block.result or weak["headline"])[:100]),
            "detail": sanitize_coach_text((block.cause or weak["detail"])[:160]),
        }

    listen_hint = ""
    if report.pitch_deviation_segments:
        from coaching_vocab import time_range

        seg = report.pitch_deviation_segments[0]
        listen_hint = (
            f"{time_range(seg.start_sec, seg.end_sec)}에서 주의 — "
            "위 🎧 녹음을 재생해 직접 들어보세요."
        )

    action_lines: list[str] = []
    if actions:
        practice = str(actions[0].get("practice") or "")
        for line in practice.split("\n"):
            line = line.strip().lstrip("- [ ]").strip()
            if line:
                action_lines.append(line)
    if not action_lines:
        action_lines = [
            "메트로놈 70BPM 켜기",
            "문제 구간 2마디만 '스-' 발음으로 리듬 타기",
            "손뼉과 가사 첫 음절 동시에 맞추기 5회",
        ]

    action_html = "".join(
        f'<li class="vc-triptych-action-item">{html.escape(line)}</li>' for line in action_lines[:4]
    )

    render_safe_html(
        f"""\
<div class="vc-triptych-stack">
<article class="vc-triptych-card vc-triptych-good">
<p class="vc-triptych-label">👍 잘한 점</p>
<p class="vc-triptych-head">{html.escape(good["headline"])}</p>
<p class="vc-triptych-body">{html.escape(good["detail"][:180])}</p>
</article>
<article class="vc-triptych-card vc-triptych-weak">
<p class="vc-triptych-label">🎯 아쉬운 점</p>
<p class="vc-triptych-head">{html.escape(weak["headline"])}</p>
<p class="vc-triptych-body">{html.escape(weak["detail"][:180])}</p>
{f'<p class="vc-triptych-listen">{html.escape(listen_hint)}</p>' if listen_hint else ''}
</article>
<article class="vc-triptych-card vc-triptych-action">
<p class="vc-triptych-label">💡 오늘의 처방전</p>
<ul class="vc-triptych-actions">{action_html}</ul>
</article>
</div>"""
    )


def _render_charts_sticky_bar(report: Any) -> None:
    """차트 탭 상단 sticky 미니 대시보드."""
    stages = report.stages[:3]
    weakest = min(stages, key=lambda s: s.score) if stages else None
    wlabel = STAGE_NAMES.get(weakest.stage, "—") if weakest else "—"
    wscore = f"{weakest.score:.0f}점" if weakest else "—"

    alert = "—"
    if report.pitch_deviation_segments:
        from coaching_vocab import time_range

        d = report.pitch_deviation_segments[0]
        t0 = getattr(d, "start_sec", 0)
        t1 = getattr(d, "end_sec", 0)
        hint = getattr(d, "note_hint", "") or ""
        alert = f"{time_range(t0, t1)} {hint}".strip()

    render_safe_html(
        f"""\
<div class="vc-sticky-chart-bar">
<span class="vc-sticky-chip">종합 <b>{report.overall_score:.0f}점</b></span>
<span class="vc-sticky-chip">🎯 {html.escape(wlabel)} {wscore}</span>
<span class="vc-sticky-chip vc-sticky-warn">⚠️ {html.escape(alert)}</span>
</div>"""
    )


def _render_at_a_glance_summary(report: Any, full_record: dict[str, Any]) -> None:
    """한눈에 보기 — 오늘 집중 포인트 + 레이더 (중복 점수 링 제거)."""
    from vocal_radar import build_vocal_radar_scores, radar_insight_text

    from ui.text_format import sanitize_coach_text

    radar = build_vocal_radar_scores(report, full_record)
    insight = radar_insight_text(radar)

    weakest = min(report.stages[:3], key=lambda s: s.score) if report.stages else None
    focus = ""
    if weakest and weakest.coaching_blocks:
        focus = sanitize_coach_text((weakest.coaching_blocks[0].result or "").strip())

    render_safe_html(
        f"""
        <div class="vc-glance-head">
            <p class="vc-glance-kicker">5축 분석 요약</p>
            <p class="vc-glance-title">{html.escape(insight)}</p>
        </div>
        """
    )
    if focus:
        render_safe_html(
            f"""
            <div class="vc-focus-banner">
                <span class="vc-focus-icon" aria-hidden="true">🎯</span>
                <div class="vc-focus-body">
                    <p class="vc-focus-label">오늘 집중</p>
                    <p class="vc-focus-text">{html.escape(focus)}</p>
                </div>
            </div>
            """
        )

    render_radar_chart(report=report, full_record=full_record, show_insight=False)

    cols = st.columns(3)
    for col, stage in zip(cols, report.stages[:3]):
        emoji, short = _STAGE_META.get(stage.stage, ("📊", stage.title))
        label = short or stage.title
        with col:
            st.metric(f"{emoji} {label}", f"{stage.score:.0f}점")


def render_session_results(session: dict[str, Any]) -> None:
    """탭형 리포트 — 진단 · 구간 분석 · 연습장 · 보관함."""
    report = session["report"]
    full_record = session.get("full_record") or {}
    actions = full_record.get("priority_actions") or []

    render_safe_html('<div class="vc-detail-panel vc-layout-bound">')

    tab_summary, tab_charts, tab_practice, tab_save = st.tabs(
        ["📊 나의 진단서", "🔍 구간별 분석", "🏋️ 맞춤 연습장", "💾 보관함"]
    )

    with tab_summary:
        _render_sandwich_triptych(session, report, full_record)
        _render_at_a_glance_summary(report, full_record)
        from ui.wrapped_share import render_wrapped_share_card

        render_wrapped_share_card(session)
        render_score_feedback(session, full_record)

        sparkline = session.get("sparkline_path")
        if sparkline and Path(sparkline).exists():
            render_safe_html('<p class="vc-section-label">📈 연습 히스토리</p>')
            render_safe_html('<div class="vc-graph-frame vc-sparkline-frame">')
            st.image(str(sparkline), use_container_width=True)
            render_safe_html("</div>")

        try:
            from ui.auth import current_user_id
            from weekly_summary import compute_weekly_summary

            uid = current_user_id()
            if uid:
                ws = compute_weekly_summary(uid)
                if ws.get("total_records", 0) > 0 and ws.get("count", 0) > 0:
                    delta = ws.get("delta")
                    delta_txt = f" · 전주 {delta:+.1f}pt" if delta is not None else ""
                    avg = ws.get("avg_score")
                    avg_txt = f"{avg:.0f}점" if avg is not None else "—"
                    render_safe_html(f'<p class="vc-weekly-inline">📅 이번 주 {ws["count"]}회 · 평균 {avg_txt}{delta_txt}</p>'
                    )
        except Exception:
            pass

    with tab_charts:
        _render_charts_sticky_bar(report)
        _render_pitch_graph(session, report)
        render_safe_html('<p class="vc-section-label">🎹 노트 히트맵</p>')
        _render_heatmap_panel(session, report, full_record)
        render_precision_panel(report, full_record)
        _render_insight_pills(report, full_record)

    with tab_practice:
        render_safe_html('<p class="vc-practice-intro">🚀 <b>지금 당장</b> 따라 할 연습만 모았어요. '
            "궁금하면 아래 AI 코치에게 물어보세요.</p>"
        )
        if actions:
            render_action_plan(actions)
        else:
            st.info("맞춤 처방전을 준비 중이에요. AI 코치에게 「10분 루틴 짜줘」라고 물어보세요.")
        if session.get("compare_text"):
            render_safe_html('<p class="vc-section-label">📊 이전 기록과 비교</p>')
            st.code(session["compare_text"])

    with tab_save:
        _render_downloads_card(session, full_record)

    _render_share_button(session)

    render_safe_html("</div>")


def _build_share_text(session: dict[str, Any]) -> str:
    from coaching_vocab import derive_vocal_title

    report = session["report"]
    full_record = session.get("full_record") or {}
    vocal_title = full_record.get("vocal_title") or derive_vocal_title(report.stages)
    overall = report.overall_score
    try:
        from ui.beta import BETA_SHARE_URL

        app_url = BETA_SHARE_URL.rstrip("/")
    except Exception:
        app_url = "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app"
    return (
        f"👑 나의 보컬 MBTI는 [{vocal_title}]! 총점 {overall:.0f}점 🎤\n"
        f"Vocal Coach AI에서 무료로 내 목소리 분석해 보기 → {app_url}"
    )


def _render_share_button(session: dict[str, Any]) -> None:
    """그라데이션 풀와이즈 배너 + 클립보드 복사."""
    import json

    text = _build_share_text(session)
    js_payload = json.dumps(text, ensure_ascii=False)
    btn_id = f"vcShareBanner_{abs(hash(text)) % 10_000_000}"

    render_safe_html(
        f"""\
<div class="vc-share-wrap">
<button type="button" class="vc-share-banner" id="{btn_id}" aria-label="보컬 진단서 공유">
<span class="vc-share-banner-icon">🚀</span>
<span class="vc-share-banner-text">내 보컬 MBTI 친구들에게 자랑하기</span>
</button>
<p class="vc-share-toast" id="{btn_id}_toast" hidden>복사 완료! 친구들에게 공유해 보세요.</p>
</div>
<script>
(function() {{
    const btn = document.getElementById("{btn_id}");
    const toast = document.getElementById("{btn_id}_toast");
    const payload = {js_payload};
    if (!btn) return;
    btn.addEventListener("click", function() {{
        const done = function() {{
            if (toast) {{
                toast.hidden = false;
                toast.classList.add("vc-share-toast-show");
                setTimeout(function() {{
                    toast.classList.remove("vc-share-toast-show");
                    setTimeout(function() {{ toast.hidden = true; }}, 300);
                }}, 2600);
            }}
        }};
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(payload).then(done).catch(function() {{
                window.prompt("아래 텍스트를 복사해 주세요:", payload);
                done();
            }});
        }} else {{
            window.prompt("아래 텍스트를 복사해 주세요:", payload);
            done();
        }}
    }});
}})();
</script>"""
    )
