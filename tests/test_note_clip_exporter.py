"""note_clip_exporter 단위 테스트."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_export_note_miss_clips() -> None:
    from note_clip_exporter import export_note_miss_clips, export_single_note_clip

    sr = 22050
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    y = 0.3 * np.sin(2 * np.pi * 440 * t)

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "test.wav"
        sf.write(wav, y, sr)

        segments = [
            {
                "start_sec": 0.2,
                "end_sec": 0.6,
                "midi_median": 69,
                "mean_cents_error": 28.0,
                "hit": False,
            },
            {
                "start_sec": 1.0,
                "end_sec": 1.4,
                "midi_median": 72,
                "mean_cents_error": 3.0,
                "hit": True,
            },
        ]

        clips = export_note_miss_clips(wav, segments, max_clips=2)
        assert len(clips) >= 1
        assert clips[0].path.exists()
        assert clips[0].label

        single = export_single_note_clip(wav, segments[0])
        assert single is not None
        assert single.path.exists()


if __name__ == "__main__":
    test_export_note_miss_clips()
    print("note_clip_exporter tests passed.")
