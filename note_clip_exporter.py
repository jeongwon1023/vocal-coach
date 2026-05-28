"""노트 구간 클립 — 히트맵 드릴다운용."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parent
NOTE_CLIPS_DIR = PROJECT_DIR / "clips" / "notes"


@dataclass
class NoteClipInfo:
    path: Path
    start_sec: float
    end_sec: float
    label: str
    mean_cents: float
    hit: bool


def export_note_miss_clips(
    audio_path: Path,
    note_segments: list[dict],
    *,
    max_clips: int = 5,
    pad_sec: float = 0.2,
    sr: int = 22050,
) -> list[NoteClipInfo]:
    if not audio_path.exists() or not note_segments:
        return []

    misses = [s for s in note_segments if not s.get("hit", True)]
    misses.sort(key=lambda s: float(s.get("mean_cents_error", 0)), reverse=True)
    if not misses:
        misses = sorted(
            note_segments,
            key=lambda s: float(s.get("mean_cents_error", 0)),
            reverse=True,
        )[:max_clips]

    NOTE_CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    dur = len(y) / sr
    exported: list[NoteClipInfo] = []

    for i, seg in enumerate(misses[:max_clips], 1):
        t0 = max(0.0, float(seg["start_sec"]) - pad_sec)
        t1 = min(dur, float(seg["end_sec"]) + pad_sec)
        if t1 - t0 < 0.12:
            continue
        midi = seg.get("midi_median", 0)
        err = float(seg.get("mean_cents_error", 0))
        try:
            note = librosa.midi_to_note(int(round(midi)), unicode=False)
        except Exception:
            note = f"M{midi:.0f}"
        fname = f"note_{i:02d}_{t0:.1f}s_{note.replace('#', 's')}.wav"
        out = NOTE_CLIPS_DIR / fname
        sf.write(out, y[int(t0 * sr) : int(t1 * sr)], sr)
        exported.append(
            NoteClipInfo(
                path=out,
                start_sec=t0,
                end_sec=t1,
                label=note,
                mean_cents=err,
                hit=bool(seg.get("hit")),
            )
        )
    return exported


def export_single_note_clip(
    audio_path: Path,
    segment: dict,
    *,
    pad_sec: float = 0.2,
    sr: int = 22050,
) -> NoteClipInfo | None:
    """단일 노트 구간 클립 — 히트맵 피커용."""
    clips = export_note_miss_clips(
        audio_path,
        [segment],
        max_clips=1,
        pad_sec=pad_sec,
        sr=sr,
    )
    return clips[0] if clips else None
