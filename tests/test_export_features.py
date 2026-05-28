"""report_pdf · song_hints JSON 로더 테스트."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_song_hints_json_load() -> None:
    from song_hints import DEFAULT_DB_PATH, all_song_hints, load_song_hints, reload_song_hints

    assert DEFAULT_DB_PATH.exists()
    hints = load_song_hints()
    assert len(hints) >= 35
    assert all_song_hints() == hints

    with tempfile.TemporaryDirectory() as tmp:
        custom = Path(tmp) / "custom.json"
        custom.write_text(
            json.dumps(
                {
                    "version": 1,
                    "songs": [
                        {
                            "title": "Test Song",
                            "artist": "Tester",
                            "youtube_query": "Tester Test Song MR",
                            "style_preset": "ballad",
                            "genre_label": "Test",
                            "aliases": ["테스트"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        loaded = load_song_hints(custom)
        assert len(loaded) == 1
        assert loaded[0].title == "Test Song"

    reload_song_hints()
    assert len(all_song_hints()) >= 35


def test_report_pdf_minimal() -> None:
    from report_pdf import generate_analysis_pdf

    class FakeStage:
        def __init__(self, stage, title, score, summary=""):
            self.stage = stage
            self.title = title
            self.score = score
            self.summary = summary
            self.coaching_blocks = []
            self.details = {}

    class FakeReport:
        overall_score = 78.0
        song_title = "테스트곡"
        stages = [
            FakeStage(1, "음정", 75, "음정 안정적"),
            FakeStage(2, "박자", 80),
            FakeStage(3, "호흡", 76),
            FakeStage(4, "종합", 78),
        ]
        pitch_deviation_segments = []
        analysis_engine = {"separation": "enhanced_hpss", "f0_method": "pyin"}

    session = {
        "report": FakeReport(),
        "full_record": {
            "song_title": "테스트곡",
            "recorded_at": "2026-05-25T12:00:00",
            "overall_score": 78,
            "stage_scores": {1: 75, 2: 80, 3: 76},
        },
    }

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test_report.pdf"
        path = generate_analysis_pdf(session, output_path=out)
        assert path is not None
        assert path.exists()
        assert path.stat().st_size > 500


if __name__ == "__main__":
    test_song_hints_json_load()
    test_report_pdf_minimal()
    print("export tests passed.")
