"""분석 결과 PDF — matplotlib PdfPages (추가 의존성 없음)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from ui.runtime_env import configure_matplotlib

configure_matplotlib()

PROJECT_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = PROJECT_DIR / "exports"


def _stage_scores(full_record: dict, report: Any) -> dict[int, float]:
    raw = full_record.get("stage_scores") or {}
    if raw:
        return {
            int(k): float(v)
            for k, v in raw.items()
            if v is not None
        }
    return {s.stage: float(s.score) for s in report.stages[:4]}


def _coaching_lines(report: Any, full_record: dict, *, limit: int = 8) -> list[str]:
    lines: list[str] = []
    for stage in report.stages[:4]:
        if stage.summary:
            lines.append(f"[{stage.title}] {stage.summary}")
        for block in (stage.coaching_blocks or [])[:2]:
            text = block.strip() if isinstance(block, str) else str(block)
            if text:
                lines.append(f"  · {text[:200]}")
    for act in (full_record.get("priority_actions") or [])[:3]:
        title = act.get("title") or act.get("prescription") or ""
        if title:
            lines.append(f"★ {title}")
    return lines[:limit]


def _text_page(pdf: PdfPages, title: str, lines: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("#ffffff")
    ax.axis("off")
    ax.text(0.05, 0.95, title, fontsize=16, fontweight="bold", va="top", transform=ax.transAxes)
    body = "\n".join(lines)
    ax.text(0.05, 0.88, body, fontsize=10, va="top", transform=ax.transAxes, wrap=True)
    pdf.savefig(fig)
    plt.close(fig)


def _image_page(pdf: PdfPages, image_path: Path, caption: str) -> None:
    if not image_path.exists():
        return
    img = plt.imread(str(image_path))
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(caption, fontsize=12, pad=12)
    pdf.savefig(fig)
    plt.close(fig)


def generate_analysis_pdf(
    session: dict[str, Any],
    *,
    output_path: Path | None = None,
    user_id: str | None = None,
) -> Path | None:
    """세션 dict → PDF 리포트. report · full_record · plot/heatmap/chart 경로 사용."""
    report = session.get("report")
    if report is None:
        return None

    full_record = session.get("full_record") or {}
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = output_path or EXPORTS_DIR / f"vocal_coach_report_{stamp}.pdf"

    song = full_record.get("song_title") or getattr(report, "song_title", None) or "미지정"
    recorded = full_record.get("recorded_at") or datetime.now().isoformat(timespec="seconds")
    overall = float(getattr(report, "overall_score", 0) or full_record.get("overall_score") or 0)
    scores = _stage_scores(full_record, report)

    summary_lines = [
        f"곡: {song}",
        f"분석 시각: {recorded}",
        f"종합 점수: {overall:.1f}",
        "",
        "영역별 점수:",
    ]
    names = {1: "음정", 2: "박자·리듬", 3: "호흡·음색", 4: "종합"}
    for stage, score in sorted(scores.items()):
        summary_lines.append(f"  · {names.get(stage, f'Stage {stage}')}: {score:.1f}")

    engine = full_record.get("analysis_engine") or getattr(report, "analysis_engine", {}) or {}
    if engine:
        summary_lines.extend(
            [
                "",
                f"분석 엔진: {engine.get('separation', '—')} · {engine.get('f0_method', '—')}",
            ]
        )

    if session.get("compare_text"):
        summary_lines.extend(["", "이전 기록 비교:", session["compare_text"][:1200]])

    coaching = _coaching_lines(report, full_record)
    if coaching:
        summary_lines.extend(["", "코칭 요약:", *coaching])

    if session.get("gpt_text"):
        summary_lines.extend(["", "GPT 코칭:", session["gpt_text"][:1500]])

    with PdfPages(out) as pdf:
        _text_page(pdf, "Vocal Coach AI — 분석 리포트", summary_lines)

        plot = session.get("plot_path")
        if plot and Path(plot).exists():
            _image_page(pdf, Path(plot), "음정 그래프")

        heatmap = session.get("heatmap_path")
        if heatmap and Path(heatmap).exists():
            _image_page(pdf, Path(heatmap), "노트 히트맵")

        chart = session.get("chart_path")
        if not chart or not Path(chart).exists():
            try:
                from progress_chart import generate_growth_chart

                chart = generate_growth_chart(user_id=user_id)
            except Exception:
                chart = None
        if chart and Path(chart).exists():
            _image_page(pdf, Path(chart), "연습 히스토리 · 성장 곡선")

        d = pdf.infodict()
        d["Title"] = "Vocal Coach Analysis Report"
        d["Author"] = "Vocal Coach AI"
        d["Subject"] = str(song)
        d["CreationDate"] = datetime.now()

    return out if out.exists() else None
