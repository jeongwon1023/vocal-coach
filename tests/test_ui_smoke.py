"""UI 모듈 import · 기본 smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_ui_imports() -> None:
    from ui import analysis_settings, auth, beta, coach_chat, dashboard, landing, my_page, navbar, navigation, progress, styles

    assert callable(analysis_settings.open_analysis_settings_dialog)

    assert callable(auth.render_login_compact)
    assert callable(beta.render_beta_banner)
    assert callable(coach_chat.render_coach_dm)
    assert callable(dashboard.render)
    assert callable(navigation.go_to)
    assert callable(styles.apply)


def test_analysis_eta() -> None:
    from ui.analysis_eta import default_total_seconds, format_eta, remaining_seconds

    assert default_total_seconds(fast_mode=True) == 55
    assert default_total_seconds(fast_mode=False) == 150
    assert "초" in format_eta(30) or "분" in format_eta(30)
    assert remaining_seconds(0.5, fast_mode=True, started_at=None) >= 0


def test_navigation_pages() -> None:
    from ui.navigation import PAGES

    assert "홈" in PAGES
    assert "분석" in PAGES
    assert "마이 페이지" in PAGES
    assert "피드백" in PAGES


def test_auth_login_compact_accepts_prefix() -> None:
    import inspect

    from ui.auth import render_login_compact

    sig = inspect.signature(render_login_compact)
    assert "key_prefix" in sig.parameters


def test_load_session_for_job_missing() -> None:
    from analysis_queue import load_session_for_job

    assert load_session_for_job("nonexistent-job-id-xyz") is None


def test_coach_chat_helpers() -> None:
    from ui.coach_chat import _rule_opening, _rule_suggested_questions

    class FakeStage:
        def __init__(self, stage, title, score):
            self.stage = stage
            self.title = title
            self.score = score
            self.details = {}

    class FakeReport:
        overall_score = 72.0
        stages = [
            FakeStage(1, "음정", 65),
            FakeStage(2, "박자", 70),
            FakeStage(3, "호흡", 80),
            FakeStage(4, "종합", 72),
        ]
        pitch_deviation_segments = []

    session = {"report": FakeReport(), "full_record": {}}
    opening = _rule_opening(session)
    assert "분석" in opening or "들어봤" in opening
    qs = _rule_suggested_questions(session)
    assert len(qs) == 3


def test_pitch_hz_ylim_empty() -> None:
    import numpy as np

    from analysis import _pitch_hz_ylim

    f0 = np.array([np.nan, np.nan])
    ref = np.array([np.nan])
    lo, hi = _pitch_hz_ylim(f0, ref)
    assert lo == 80.0 and hi == 800.0
    assert np.isfinite(lo) and np.isfinite(hi)


def test_pitch_hz_ylim_with_data() -> None:
    import numpy as np

    from analysis import _pitch_hz_ylim

    f0 = np.array([220.0, 440.0, np.nan])
    ref = np.array([np.nan, 330.0])
    lo, hi = _pitch_hz_ylim(f0, ref)
    assert lo > 0 and hi > lo
    assert np.isfinite(lo) and np.isfinite(hi)


def test_beta_feedback_save() -> None:
    import tempfile
    from pathlib import Path

    import feedback_store

    tmp = Path(tempfile.mkdtemp())
    feedback_store.FEEDBACK_DIR = tmp
    path = feedback_store.save_beta_feedback(
        message="테스트 피드백",
        category="기능 제안",
        rating=5,
        user_name="tester",
    )
    assert path.exists()
    items = feedback_store.list_beta_feedback()
    assert len(items) == 1
    assert items[0]["message"] == "테스트 피드백"


if __name__ == "__main__":
    test_ui_imports()
    test_navigation_pages()
    test_auth_login_compact_accepts_prefix()
    test_load_session_for_job_missing()
    test_coach_chat_helpers()
    test_analysis_eta()
    test_pitch_hz_ylim_empty()
    test_pitch_hz_ylim_with_data()
    test_beta_feedback_save()
    print("All UI smoke tests passed.")
