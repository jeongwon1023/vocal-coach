"""weekly_summary 단위 테스트."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_weekly_summary_counts() -> None:
    import weekly_summary as ws

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        def fake_user_records_dir(user_id: str | None = None) -> Path:
            if user_id:
                d = base / "records" / "users" / user_id
                d.mkdir(parents=True, exist_ok=True)
                return d
            d = base / "records"
            d.mkdir(parents=True, exist_ok=True)
            return d

        ws.user_records_dir = fake_user_records_dir
        records_dir = fake_user_records_dir("u1")

        now = datetime.now(timezone.utc).astimezone()
        for i, days_ago in enumerate((1, 3, 10, 20)):
            rec = {
                "recorded_at": (now - timedelta(days=days_ago)).isoformat(timespec="seconds"),
                "overall_score": 70 + i * 3,
                "stage_scores": {1: 65 + i, 2: 70 + i, 3: 72 + i},
                "song_title": "테스트곡" if i < 2 else "다른곡",
            }
            path = records_dir / f"record_{i:02d}.json"
            path.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")

        summary = ws.compute_weekly_summary("u1")
        assert summary["count"] == 2
        assert summary["prev_count"] == 1
        assert summary["total_records"] == 4
        assert summary["top_song"] == "테스트곡"
        assert summary["delta"] is not None
        assert summary["message"]


if __name__ == "__main__":
    test_weekly_summary_counts()
    print("weekly_summary tests passed.")
