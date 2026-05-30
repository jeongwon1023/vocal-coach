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


def test_coach_stream_request_id() -> None:
    from ui.coach_chat import _stream_request_id

    class _State(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import ui.coach_chat as cc

    old = cc.st.session_state
    cc.st.session_state = _State({"coach_chat_fp": "abc123"})
    try:
        assert _stream_request_id([]) == ""
        assert _stream_request_id([{"role": "assistant", "content": "hi"}]) == ""
        msgs = [
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "질문"},
        ]
        rid = _stream_request_id(msgs)
        assert len(rid) == 16
        assert rid == _stream_request_id(msgs)
        msgs2 = msgs + [{"role": "assistant", "content": "답"}]
        assert _stream_request_id(msgs2) == ""
    finally:
        cc.st.session_state = old


def test_gpt_coach_stream_builders() -> None:
    from gpt_coach import _build_coach_chat_messages, _build_coach_opening_messages

    payload = {"overall_score": 70, "stage_scores": {}}
    chat_msgs = _build_coach_chat_messages(payload, [], "테스트 질문")
    assert chat_msgs[0]["role"] == "system"
    assert chat_msgs[-1]["content"] == "테스트 질문"
    opening_msgs = _build_coach_opening_messages(payload)
    assert len(opening_msgs) == 2
    assert opening_msgs[-1]["role"] == "user"


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


def test_weakest_stage_compact_json() -> None:
    from analysis import StageResult, weakest_stage_to_compact_json

    stages = [
        StageResult(stage=1, title="음정", score=72.0, summary="ok"),
        StageResult(stage=2, title="박자", score=55.0, summary="weak"),
        StageResult(stage=3, title="호흡", score=68.0, summary="ok"),
        StageResult(stage=4, title="종합", score=70.0, summary="ok"),
    ]
    payload = weakest_stage_to_compact_json(stages)
    assert payload["weakest_stage"]["stage"] == 2
    assert payload["weakest_stage"]["score"] == 55.0


def test_trim_silence_intervals() -> None:
    import numpy as np

    from analysis import _trim_silence_intervals

    sr = 16000
    y = np.zeros(sr * 3)
    y[sr: sr * 2] = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr, endpoint=False))
    trimmed = _trim_silence_intervals(y, sr, top_db=20.0)
    assert len(trimmed) < len(y)
    assert len(trimmed) >= int(0.5 * sr)


def test_song_hints_lookup() -> None:
    from song_hints import (
        all_song_hints,
        apply_song_hints,
        filter_song_hints,
        lookup_song_hint,
        search_song_hints,
    )

    assert len(all_song_hints()) >= 100

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

    filtered = filter_song_hints("아이유", genre="발라드", limit=10)
    assert filtered
    assert all("아이유" in h.artist for h in filtered)


def test_trainer_language_helpers() -> None:
    from coaching_vocab import derive_vocal_title, rhythm_summary
    from ui.text_format import sanitize_coach_text, solution_to_checklist
    from vocal_radar import build_vocal_radar_scores, radar_insight_text

    bad = rhythm_summary(208, 1.18)
    assert "지수" not in bad
    assert "208" not in bad

    title = derive_vocal_title(
        [
            type("S", (), {"stage": 1, "score": 82.0})(),
            type("S", (), {"stage": 2, "score": 52.0})(),
            type("S", (), {"stage": 3, "score": 70.0})(),
        ]
    )
    assert "감성 발라더" in title

    raw = "Superflux onset(논문 Böck 2013)으로 분석. 박 간격 들쭉날쭉 지수 1.18"
    clean = sanitize_coach_text(raw)
    assert "Superflux" not in clean
    assert "Böck" not in clean
    assert "1.18" not in clean

    from ui.text_format import format_coach_rich_html, normalize_checklist_markdown, normalize_markdown_noise, solution_to_checklist

    checklist = solution_to_checklist("① 메트로놈 70BPM ② 2마디 연습")
    assert "- [ ]" in checklist

    raw_gpt = "🎯 **박자를 개선해 보아요** ~~0~2초 구간~~ ① 메트로놈 70 ② 손뼉"
    rich = format_coach_rich_html(raw_gpt)
    assert "~~" not in rich
    assert "vc-coach-step" in rich
    assert "→ 1" in rich
    assert "vc-coach-sec-focus" in rich or "vc-coach-headline" in rich

    assert normalize_markdown_noise("0~2초") == "0–2초"

    checklist = normalize_checklist_markdown("- [ ] a - [ ] b")
    assert checklist.count("- [ ]") == 2
    assert "\n" in checklist

    class FakeStage:
        def __init__(self, stage, score, details=None):
            self.stage = stage
            self.score = score
            self.details = details or {}

    class FakeReport:
        stages = [
            FakeStage(1, 74),
            FakeStage(2, 45),
            FakeStage(3, 45, {"timbre_score": 50}),
            FakeStage(4, 70, {"dynamics_score": 72, "phrase_legato_score": 68}),
        ]
        dtw_result = None

    radar = build_vocal_radar_scores(FakeReport())
    assert set(radar.keys()) == {"음정", "박자", "호흡", "발성", "표현력"}
    assert len(radar_insight_text(radar)) > 10


def test_timestamp_and_guardrails() -> None:
    from coaching_vocab import format_mmss, time_range, timestamp_at

    assert format_mmss(75) == "01:15"
    assert timestamp_at(75) == "⏱ [01:15]"
    assert "01:15" in time_range(75, 82)

    from progress_chart import compute_practice_streak

    from datetime import date, datetime

    today = datetime.combine(date.today(), datetime.min.time()).isoformat()
    yesterday = datetime.combine(date.fromordinal(date.today().toordinal() - 1), datetime.min.time()).isoformat()
    streak = compute_practice_streak(
        [{"recorded_at": today}, {"recorded_at": yesterday}]
    )
    assert streak >= 2


def test_render_safe_html_dedent() -> None:
    from ui.utils import render_safe_html
    import textwrap

    class _Capture:
        calls: list[tuple] = []

    import ui.utils as u

    old = u.st.markdown
    u.st.markdown = lambda content, **kw: _Capture.calls.append((content, kw))
    try:
        render_safe_html(
            """
            <div class="x">
              <p>ok</p>
            </div>
            """
        )
        assert _Capture.calls
        body, kw = _Capture.calls[-1]
        assert kw.get("unsafe_allow_html") is True
        assert "<div class=\"x\">" in body
        assert body.startswith("<div")
        assert "  <p>ok</p>" not in body or textwrap.dedent(body) == body
    finally:
        u.st.markdown = old


if __name__ == "__main__":
    test_ui_imports()
    test_navigation_pages()
    test_auth_login_compact_accepts_prefix()
    test_load_session_for_job_missing()
    test_coach_chat_helpers()
    test_coach_stream_request_id()
    test_gpt_coach_stream_builders()
    test_analysis_eta()
    test_pitch_hz_ylim_empty()
    test_pitch_hz_ylim_with_data()
    test_beta_feedback_save()
    test_feedback_trainer()
    test_coach_rag()
    test_suggestion_pool()
    test_weakest_stage_compact_json()
    test_trim_silence_intervals()
    test_song_hints_lookup()
    test_trainer_language_helpers()
    test_timestamp_and_guardrails()
    test_render_safe_html_dedent()
    print("All UI smoke tests passed.")
