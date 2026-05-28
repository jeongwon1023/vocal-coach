"""Plotly 인터랙티브 노트 히트맵 — 클릭 선택."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import librosa
import numpy as np

try:
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def plotly_available() -> bool:
    return PLOTLY_AVAILABLE


def _seg_dict(seg) -> dict:
    if hasattr(seg, "start_sec"):
        return {
            "start_sec": seg.start_sec,
            "end_sec": seg.end_sec,
            "midi_median": seg.midi_median,
            "mean_cents_error": seg.mean_cents_error,
            "hit": seg.hit,
        }
    return seg


def build_note_heatmap_figure(
    times: np.ndarray,
    f0: np.ndarray,
    cents_ref: np.ndarray,
    note_segments: list,
    *,
    title: str = "노트 히트맵 (클릭하여 선택)",
) -> Any | None:
    if not PLOTLY_AVAILABLE:
        return None

    segs = [_seg_dict(s) for s in (note_segments or [])]
    voiced = np.isfinite(f0) & (f0 > 0) & np.isfinite(cents_ref)

    fig = go.Figure()
    if np.any(voiced):
        midi = librosa.hz_to_midi(f0[voiced])
        abs_c = np.clip(np.abs(cents_ref[voiced]), 0, 80)
        fig.add_trace(
            go.Scattergl(
                x=times[voiced],
                y=midi,
                mode="markers",
                marker=dict(
                    size=7,
                    color=abs_c,
                    colorscale=[
                        [0, "#22c55e"],
                        [0.35, "#eab308"],
                        [0.65, "#f97316"],
                        [1, "#ef4444"],
                    ],
                    cmin=0,
                    cmax=50,
                    opacity=0.75,
                ),
                name="프레임",
                hovertemplate="시간 %{x:.2f}s<br>음 %{y:.0f}<br>|센트| %{marker.color:.0f}<extra></extra>",
            )
        )

    for idx, seg in enumerate(segs, 1):
        t0, t1 = seg["start_sec"], seg["end_sec"]
        midi_n = seg["midi_median"]
        err = float(seg.get("mean_cents_error", 0))
        hit = bool(seg.get("hit", False))
        color = "#22c55e" if hit else ("#f97316" if err < 35 else "#ef4444")
        note = librosa.midi_to_note(int(round(midi_n)), unicode=False)
        fig.add_shape(
            type="rect",
            x0=t0,
            x1=max(t0 + 0.05, t1),
            y0=midi_n - 0.45,
            y1=midi_n + 0.45,
            fillcolor=color,
            opacity=0.2,
            line=dict(color=color, width=1.5),
            layer="below",
        )
        fig.add_trace(
            go.Scatter(
                x=[(t0 + t1) / 2],
                y=[midi_n],
                mode="markers+text",
                marker=dict(size=16, color=color, opacity=0.01),
                text=[str(idx)],
                textfont=dict(size=10, color=color),
                textposition="middle center",
                name=f"#{idx} {note}",
                customdata=[[idx, note, t0, t1, err, hit]],
                hovertemplate=(
                    f"<b>#{idx} {note}</b><br>"
                    "시간 %{customdata[2]:.2f}–%{customdata[3]:.2f}s<br>"
                    "오차 %{customdata[4]:.0f}¢<br>"
                    "%{customdata[5]}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    if np.any(voiced):
        midi_v = librosa.hz_to_midi(f0[voiced])
        lo, hi = float(np.floor(np.min(midi_v) - 2)), float(np.ceil(np.max(midi_v) + 2))
    elif segs:
        mids = [s["midi_median"] for s in segs]
        lo, hi = min(mids) - 2, max(mids) + 2
    else:
        lo, hi = 48, 72

    yticks = list(range(int(lo), int(hi) + 1, 2))
    fig.update_layout(
        title=title,
        xaxis_title="시간 (초)",
        yaxis_title="음",
        yaxis=dict(
            tickmode="array",
            tickvals=yticks,
            ticktext=[librosa.midi_to_note(int(n), unicode=False) for n in yticks],
        ),
        height=420,
        margin=dict(l=50, r=20, t=50, b=40),
        plot_bgcolor="#faf8ff",
        paper_bgcolor="#f8f6ff",
        dragmode="select",
    )
    if len(times) > 0:
        fig.update_xaxes(range=[float(np.min(times)), float(np.max(times))])
    fig.update_yaxes(range=[lo, hi])
    return fig


def build_note_heatmap_figure_from_report(report) -> Any | None:
    from analysis import cents_vs_reference

    if not PLOTLY_AVAILABLE or report.f0.size == 0:
        return None
    cents_ref = cents_vs_reference(report.f0, report.f0_reference)
    segs = getattr(report, "note_segments", None) or []
    return build_note_heatmap_figure(
        report.times,
        report.f0,
        cents_ref,
        segs,
        title="노트 히트맵 · 번호 클릭/드래그 선택",
    )


def extract_selected_note_index(selection_event: Any) -> int | None:
    """Streamlit plotly_chart on_select 이벤트 → 노트 idx."""
    if not selection_event:
        return None
    points = getattr(selection_event, "selection", None)
    if points is None and isinstance(selection_event, dict):
        points = selection_event.get("selection")
    if not points:
        return None
    point_list = points.get("points") if isinstance(points, dict) else getattr(points, "points", None)
    if not point_list:
        return None
    for pt in point_list:
        cd = pt.get("customdata") if isinstance(pt, dict) else getattr(pt, "customdata", None)
        if cd and len(cd) >= 1:
            try:
                return int(cd[0][0] if isinstance(cd[0], list) else cd[0])
            except (TypeError, ValueError, IndexError):
                continue
    return None
