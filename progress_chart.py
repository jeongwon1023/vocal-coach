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

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

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
    overall: list[float] = []
    s1, s2, s3 = [], [], []

    for r in records:
        ts = r.get("recorded_at", "")
        try:
            dt = datetime.fromisoformat(ts)
            label = dt.strftime("%m/%d")
        except Exception:
            label = ts[:10] if ts else "?"
        dates.append(label)
        overall.append(float(r.get("overall_score") or 0))
        scores = r.get("stage_scores") or {}
        s1.append(float(scores.get(1) or scores.get("1") or 0))
        s2.append(float(scores.get(2) or scores.get("2") or 0))
        s3.append(float(scores.get(3) or scores.get("3") or 0))

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or CHARTS_DIR / "growth_chart.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(dates))
    ax.plot(x, overall, "o-", linewidth=2, label="종합", color="#1e3a8a")
    ax.plot(x, s1, "s--", alpha=0.85, label=STAGE_LABELS[1], color="#2563eb")
    ax.plot(x, s2, "^--", alpha=0.85, label=STAGE_LABELS[2], color="#dc2626")
    ax.plot(x, s3, "d--", alpha=0.85, label=STAGE_LABELS[3], color="#16a34a")
    ax.set_xticks(list(x))
    ax.set_xticklabels(dates, rotation=30, ha="right")
    ax.set_ylim(0, 105)
    ax.set_ylabel("점수")
    ax.set_title("보컬 코칭 성장 곡선")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    if show:
        plt.show()
    else:
        plt.close(fig)
    return out


if __name__ == "__main__":
    p = generate_growth_chart()
    print(f"저장: {p}" if p else "기록 없음")
