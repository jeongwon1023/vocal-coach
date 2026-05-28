"""UI 모듈 import · 기본 smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_ui_imports() -> None:
    from ui import analysis_settings, audio_recorder, auth, beta, coach_chat, dashboard, landing, my_page, navbar, navigation, progress, styles

    assert callable(analysis_settings.open_analysis_settings_dialog)
    assert callable(audio_recorder.render_live_recorder)
    assert callable(audio_recorder.render_file_upload_fallback)

    assert callable(auth.render_login_compact)
    assert callable(auth.render_menu_auth)
    assert callable(beta.render_beta_banner)
    assert callable(coach_chat.render_coach_dm)
    assert callable(dashboard.render)
    assert callable(navigation.go_to)
    assert callable(styles.apply)

    import pitch_estimator
    import vocal_separation

    assert callable(pitch_estimator.extract_pitch_ensemble)
    assert callable(vocal_separation.prepare_vocal_signal)

    import pitch_heatmap

    assert callable(pitch_heatmap.plot_note_heatmap)


def test_analysis_eta() -> None:
    from ui.analysis_eta import default_total_seconds, format_eta, remaining_seconds

    assert default_total_seconds(fast_mode=True) == 55
    assert default_total_seconds(fast_mode=False) == 150
    assert "초" in format_eta(30) or "분" in format_eta(30)
    assert remaining_seconds(0.5, fast_mode=True, started_at=None) >= 0


def test_navigation_pages() -> None:
    from ui.navigation import NAV_PAGES, PAGES

    assert "홈" in PAGES
    assert "마이 페이지" in PAGES
    assert "피드백" in PAGES
    assert "분석" not in PAGES
    assert "피드백" not in NAV_PAGES
    assert len(NAV_PAGES) == 2


def test_auth_login_compact_accepts_prefix() -> None:
    import inspect

    from ui.auth import render_login_compact

    sig = inspect.signature(render_login_compact)
    assert "key_prefix" in sig.parameters


def test_load_session_for_job_missing() -> None:
    from analysis_queue import load_session_for_job

    assert load_session_for_job("nonexistent-job-id-xyz") is None


def test_coach_chat_helpers() -> None:
    from ui.coach_chat import _normalize_chat_markdown, _rule_opening, _rule_suggested_questions
    from ui.text_format import format_step_lines

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
    assert _normalize_chat_markdown("~~취소선~~ 테스트") == "취소선 테스트"
    assert "---" not in _normalize_chat_markdown("안녕\n---\n테스트")
    assert "🌟" in _normalize_chat_markdown("안녕\n🌟 **잘한 점**")
    steps = format_step_lines("① 첫째 ② 둘째 ③ 셋째")
    assert steps.count("①") == 1
    assert "\n\n②" in steps


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


def test_feedback_trainer() -> None:
    import tempfile
    from pathlib import Path

    import feedback_store
    import feedback_trainer

    tmp = Path(tempfile.mkdtemp())
    feedback_store.FEEDBACK_DIR = tmp / "feedback"
    feedback_trainer.CALIBRATION_PATH = tmp / "scoring_calibration.json"

    for i in range(3):
        feedback_store.save_feedback(agrees=True, overall_score=70 + i)
    cal = feedback_trainer.train_from_feedback()
    assert cal.samples_agree == 3
    assert not cal.min_samples_met

    for i in range(3):
        feedback_store.save_feedback(
            agrees=False,
            overall_score=55,
            stage_scores={"1": 40, "2": 50, "3": 45},
            comment="점수가 너무 낮아요",
        )
    cal = feedback_trainer.train_from_feedback()
    assert cal.min_samples_met
    assert cal.overall_bias > 0
    assert cal.generosity >= 1.0

    class Stage:
        def __init__(self, stage, score):
            self.stage = stage
            self.score = score

    class Report:
        stages = [Stage(1, 60), Stage(2, 55), Stage(3, 50), Stage(4, 58)]
        overall_score = 58

    report = Report()
    before = report.overall_score
    feedback_trainer.apply_calibration_to_report(report)
    assert report.overall_score >= before


def test_coach_rag() -> None:
    import coach_rag

    stats = coach_rag.build_index(force=True)
    assert stats["chunks"] >= 4

    hits = coach_rag.retrieve("음정 0.5배속 구간 루프", k=2)
    assert hits
    assert any("음정" in h.text or "pitch" in h.source.lower() for h in hits)

    bundle = coach_rag.retrieve_for_coaching(
        "10분 루틴 짜 주세요",
        {"stage_scores": {"1": 55, "2": 70, "3": 65}},
    )
    assert bundle.prompt_block
    assert bundle.source_labels

    status = coach_rag.rag_status()
    assert status["ready"]


def test_suggestion_pool() -> None:
    from ui.coach_chat import _pill_key, _suggestion_pool

    class FakeStage:
        def __init__(self, stage, score):
            self.stage = stage
            self.title = "t"
            self.score = score
            self.details = {}

    class FakeReport:
        overall_score = 70.0
        stages = [FakeStage(1, 60), FakeStage(2, 55), FakeStage(3, 50)]
        pitch_deviation_segments = []

    pool = _suggestion_pool({"report": FakeReport(), "full_record": {}})
    assert len(pool) >= 3
    assert len(set(pool)) == len(pool)
    assert len(_pill_key("테스트 질문")) == 10


def test_song_hints_lookup() -> None:
    from song_hints import (
        all_song_hints,
        apply_song_hints,
        lookup_song_hint,
        search_song_hints,
    )

    assert len(all_song_hints()) >= 65

    hint = lookup_song_hint("아이유 밤편지")
    assert hint is not None
    assert hint.title == "밤편지"
    assert hint.style_preset == "ballad"

    assert lookup_song_hint("Ditto").title == "Ditto"
    assert lookup_song_hint("눈코입").title == "Eyes, Nose, Lips"

    session: dict = {"style_preset": "auto"}
    applied = apply_song_hints("NewJeans Ditto", session)
    assert applied is not None
    assert session["style_preset"] == "hiphop"
    assert session["_song_hint"]["youtube_query"]
    assert session["use_youtube"] is True

    session2: dict = {"style_preset": "auto", "auto_youtube_on_hint": False}
    apply_song_hints("NewJeans Ditto", session2)
    assert "use_youtube" not in session2 or session2.get("use_youtube") is not True

    hits = search_song_hints("아이유")
    assert len(hits) >= 2
    assert all("아이유" in h.artist for h in hits)

    assert lookup_song_hint("없는곡제목xyz") is None


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
    test_feedback_trainer()
    test_coach_rag()
    test_suggestion_pool()
    test_song_hints_lookup()
    print("All UI smoke tests passed.")
