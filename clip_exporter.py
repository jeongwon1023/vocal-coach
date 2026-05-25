"""
문제 구간 WAV 클립 자동 추출 — 집중 연습용.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parent
CLIPS_DIR = PROJECT_DIR / "clips"
PAD_SEC = 0.25
MAX_CLIPS = 8


@dataclass
class ClipInfo:
    path: Path
    start_sec: float
    end_sec: float
    label: str


def export_segment_clips(
    audio_path: Path,
    segments: list,
    *,
    prefix: str = "focus",
    pad_sec: float = PAD_SEC,
    max_clips: int = MAX_CLIPS,
    sr: int = 22050,
) -> list[ClipInfo]:
    """
    PitchDeviationSegment 또는 유사 객체(start_sec, end_sec, note_hint) 리스트에서 클립 추출.
    """
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    y, file_sr = librosa.load(audio_path, sr=sr, mono=True)
    if file_sr != sr:
        pass  # already resampled

    exported: list[ClipInfo] = []
    for i, seg in enumerate(segments[:max_clips], 1):
        start = max(0.0, float(seg.start_sec) - pad_sec)
        end = min(len(y) / sr, float(seg.end_sec) + pad_sec)
        if end - start < 0.15:
            continue
        i0 = int(start * sr)
        i1 = int(end * sr)
        note = getattr(seg, "note_hint", "") or getattr(seg, "issue_type", "")
        label = f"{prefix}_{i:02d}_{start:.1f}s_{note}".replace("#", "s")
        out = CLIPS_DIR / f"{label}.wav"
        sf.write(out, y[i0:i1], sr)
        exported.append(ClipInfo(out, start, end, str(note)))

    return exported


def export_timbre_clips(audio_path: Path, timbre_segments: list, **kw) -> list[ClipInfo]:
    return export_segment_clips(audio_path, timbre_segments, prefix="timbre", **kw)


def format_clip_list(clips: list[ClipInfo]) -> str:
    if not clips:
        return "  (추출된 클립 없음)"
    lines = ["  집중 연습 클립 (clips/ 폴더):"]
    for c in clips:
        lines.append(f"    - {c.path.name}  ({c.start_sec:.1f}~{c.end_sec:.1f}s)")
    return "\n".join(lines)
