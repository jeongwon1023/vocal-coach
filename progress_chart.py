"""
성장 그래프 — records/*.json 점수 추이 PNG 생성.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

from progress_tracker import load_record, list_records, user_records_dir

PROJECT_DIR = Path(__file__).resolve().parent
CHARTS_DIR = PROJECT_DIR / "charts"

from ui.runtime_env import configure_matplotlib

configure_matplotlib()

STAGE_LABELS = {1: "음정", 2: "박자·리듬", 3: "호흡·음색"}


def load_all_records_chronological(user_id: str | None = None) -> list[dict]:
    files = sorted(
        user_records_dir(user_id).glob("record_*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    records = []
    for p in files:
        try:
            records.append(load_record(p))
        except Exception:
            continue
    return records


def generate_growth_chart(
    output_path: Path | None = None,
    *,
    show: bool = False,
    user_id: str | None = None,
) -> Path | None:
    """records JSON으로 종합·Stage별 성장 곡선 PNG."""
    records = load_all_records_chronological(user_id)
    if len(records) < 1:
        return None

    dates: list[str] = []
    labels: list[str] = []
    overall: list[float] = []
    s1, s2, s3 = [], [], []

    for r in records:
        ts = r.get("recorded_at", "")
        try:
            dt = datetime.fromisoformat(ts)
            label = dt.strftime("%m/%d")
            full = dt.strftime("%Y-%m-%d")
        except Exception:
            label = ts[:10] if ts else "?"
            full = label
        song = (r.get("song_title") or "")[:12]
        if song:
            label = f"{label}\n{song}"
        dates.append(label)
        labels.append(full)
        overall.append(float(r.get("overall_score") or 0))
        scores = r.get("stage_scores") or {}
        s1.append(float(scores.get(1) or scores.get("1") or 0))
        s2.append(float(scores.get(2) or scores.get("2") or 0))
        s3.append(float(scores.get(3) or scores.get("3") or 0))

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or CHARTS_DIR / "growth_chart.png"

    fig, ax = plt.subplots(figsize=(10, 5.2))
    fig.patch.set_facecolor("#f8f6ff")
    ax.set_facecolor("#f8f6ff")
    ax.tick_params(colors="#52525b")
    ax.xaxis.label.set_color("#3f3f46")
    ax.yaxis.label.set_color("#3f3f46")
    ax.title.set_color("#1c1528")
    for spine in ax.spines.values():
        spine.set_color("#c4bdd4")
    x = range(len(dates))
    ax.plot(x, overall, "o-", linewidth=2, label="종합", color="#1e3a8a")
    ax.plot(x, s1, "s--", alpha=0.85, label=STAGE_LABELS[1], color="#2563eb")
    ax.plot(x, s2, "^--", alpha=0.85, label=STAGE_LABELS[2], color="#dc2626")
    ax.plot(x, s3, "d--", alpha=0.85, label=STAGE_LABELS[3], color="#16a34a")

    if len(overall) >= 2:
        import numpy as np

        coef = np.polyfit(list(x), overall, 1)
        trend = np.poly1d(coef)
        ax.plot(list(x), trend(list(x)), ":", color="#6366f1", alpha=0.7, label="종합 추세")

    ax.set_xticks(list(x))
    ax.set_xticklabels(dates, rotation=0, ha="center", fontsize=8)
    ax.set_ylim(0, 105)
    ax.set_ylabel("점수")
    n = len(records)
    delta = overall[-1] - overall[0] if n >= 2 else 0
    sign = "+" if delta >= 0 else ""
    ax.set_title(f"보컬 코칭 성장 곡선 · {n}회 · 최근 {sign}{delta:.1f}pt")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=fig.get_facecolor())
    if show:
        plt.show()
    else:
        plt.close(fig)
    return out


def generate_history_sparkline(user_id: str | None = None) -> Path | None:
    """마이·결과 패널용 미니 성장 차트."""
    records = load_all_records_chronological(user_id)
    if len(records) < 2:
        return None
    overall = [float(r.get("overall_score") or 0) for r in records]
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out = CHARTS_DIR / "history_sparkline.png"
    fig, ax = plt.subplots(figsize=(6.5, 2.2))
    fig.patch.set_facecolor("#f8f6ff")
    ax.set_facecolor("#f8f6ff")
    ax.plot(overall, "o-", color="#6366f1", linewidth=2, markersize=5)
    ax.fill_between(range(len(overall)), overall, alpha=0.12, color="#6366f1")
    ax.set_ylim(max(0, min(overall) - 8), min(105, max(overall) + 8))
    ax.set_xticks([])
    ax.set_yticks([min(overall), max(overall)])
    ax.set_title(f"최근 {len(overall)}회 · {overall[-1]:.0f}점", fontsize=10)
    ax.grid(True, alpha=0.2, axis="y")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


if __name__ == "__main__":
    p = generate_growth_chart()
    print(f"저장: {p}" if p else "기록 없음")
