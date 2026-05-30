"""노트 단위 피치 히트맵 — Simply Sing / Yousician 스타일."""

from __future__ import annotations

import gc
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

from ui.runtime_env import configure_matplotlib

configure_matplotlib()


def _release_matplotlib_figure(fig) -> None:
    try:
        fig.clf()
    except Exception:
        pass
    try:
        plt.close(fig)
    except Exception:
        pass
    gc.collect()


def _segments_to_dicts(segments) -> list[dict]:
    out = []
    for s in segments or []:
        out.append(
            {
                "start_sec": s.start_sec,
                "end_sec": s.end_sec,
                "midi_median": s.midi_median,
                "mean_cents_error": s.mean_cents_error,
                "hit": s.hit,
            }
        )
    return out


def plot_note_heatmap(
    times: np.ndarray,
    f0: np.ndarray,
    cents_ref: np.ndarray,
    note_segments: list,
    *,
    title: str = "노트 히트맵",
    save_path: Path | None = None,
    dpi: int = 120,
) -> None:
    """노트 구간 + 프레임 센트 오차를 피아노롤 형태로 표시."""
    voiced = np.isfinite(f0) & (f0 > 0) & np.isfinite(cents_ref)
    if not np.any(voiced) and not note_segments:
        return

    fig, ax = plt.subplots(figsize=(13, 4.8))
    fig.patch.set_facecolor("#f8f6ff")
    ax.set_facecolor("#faf8ff")

    cmap = LinearSegmentedColormap.from_list(
        "vc_pitch",
        ["#22c55e", "#eab308", "#f97316", "#ef4444"],
    )

    if np.any(voiced):
        midi = librosa.hz_to_midi(f0[voiced])
        t_v = times[voiced]
        abs_c = np.clip(np.abs(cents_ref[voiced]), 0, 80)
        sc = ax.scatter(
            t_v,
            midi,
            c=abs_c,
            cmap=cmap,
            vmin=0,
            vmax=50,
            s=14,
            alpha=0.75,
            linewidths=0,
            zorder=2,
        )
        plt.colorbar(sc, ax=ax, label="|센트| (0=정확)", shrink=0.85)

    for idx, seg in enumerate(note_segments or [], 1):
        if hasattr(seg, "start_sec"):
            t0, t1 = seg.start_sec, seg.end_sec
            midi_n = seg.midi_median
            err = seg.mean_cents_error
            hit = seg.hit
        else:
            t0, t1 = seg["start_sec"], seg["end_sec"]
            midi_n = seg["midi_median"]
            err = seg["mean_cents_error"]
            hit = seg.get("hit", False)
        color = "#22c55e" if hit else ("#f97316" if err < 35 else "#ef4444")
        ax.add_patch(
            Rectangle(
                (t0, midi_n - 0.45),
                max(0.05, t1 - t0),
                0.9,
                linewidth=1.2,
                edgecolor=color,
                facecolor=color,
                alpha=0.18,
                zorder=1,
            )
        )
        ax.text(
            (t0 + t1) / 2,
            midi_n,
            str(idx),
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color=color,
            zorder=3,
        )

    if np.any(voiced):
        midi_v = librosa.hz_to_midi(f0[voiced])
        lo = float(np.floor(np.min(midi_v) - 2))
        hi = float(np.ceil(np.max(midi_v) + 2))
    elif note_segments:
        mids = [
            (s.midi_median if hasattr(s, "midi_median") else s["midi_median"])
            for s in note_segments
        ]
        lo, hi = min(mids) - 2, max(mids) + 2
    else:
        lo, hi = 48, 72

    ax.set_ylim(lo, hi)
    if len(times) > 0:
        ax.set_xlim(float(np.min(times)), float(np.max(times)))

    yticks = np.arange(int(lo), int(hi) + 1, 2)
    ax.set_yticks(yticks)
    ax.set_yticklabels([librosa.midi_to_note(int(n), unicode=False) for n in yticks])
    ax.set_xlabel("시간 (초)")
    ax.set_ylabel("음")
    ax.set_title(title)
    ax.grid(True, alpha=0.2, axis="x")

    fig.tight_layout()
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=dpi, facecolor=fig.get_facecolor())
    if plt.get_backend().lower() != "agg":
        plt.show()
    _release_matplotlib_figure(fig)


def plot_note_heatmap_from_report(report, save_path: Path | None = None, *, dpi: int = 120) -> None:
    """CurriculumReport → 히트맵 PNG."""
    from analysis import cents_vs_reference

    if report.f0.size == 0 or report.times.size == 0:
        return
    cents_ref = cents_vs_reference(report.f0, report.f0_reference)
    segs = getattr(report, "note_segments", None) or []
    plot_note_heatmap(
        report.times,
        report.f0,
        cents_ref,
        segs,
        title="노트 히트맵 · 녹색=정확 · 빨강=벗어남",
        save_path=save_path,
        dpi=dpi,
    )
