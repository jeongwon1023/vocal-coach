"""분석 대시보드 — 마이 페이지에서 호출 · 업로드 · 진행 · 결과."""

from __future__ import annotations

import io
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from ui.analysis_eta import format_eta, remaining_seconds
from ui.progress import make_callback, render_stepper
from ui.utils import render_safe_html


def _resolve_fast_mode() -> bool:
    """체크박스(fast_mode) + 정밀 전환 버튼(force_precision) 통합."""
    if st.session_state.get("force_precision"):
        return False
    return bool(st.session_state.get("fast_mode", True))


def _analysis_options() -> dict:
    song = (st.session_state.get("song_title") or "").strip()
    try:
        from song_hints import apply_song_hints

        apply_song_hints(song or None, st.session_state)
    except Exception:
        pass
    fast = _resolve_fast_mode()
    user_id = None
    try:
        from ui.auth import current_user_id

        user_id = current_user_id()
    except Exception:
        pass
    return {
        "song_title": song or None,
        "use_youtube": bool(st.session_state.get("use_youtube")) and bool(song),
        "use_gpt": bool(st.session_state.get("use_gpt", False)),
        "save_record": bool(st.session_state.get("save_record", True)),
        "compare": bool(st.session_state.get("compare", True)),
        "export_clips": bool(st.session_state.get("export_clips", False)),
        "growth_chart": bool(st.session_state.get("growth_chart", False)),
        "fast_mode": fast,
        "style_preset": st.session_state.get("style_preset", "auto"),
        "use_queue": bool(st.session_state.get("use_queue", True)),
        "user_id": user_id,
        "reference_path": st.session_state.get("midi_reference_path"),
    }


def is_analyzing() -> bool:
    return bool(st.session_state.get("pending_job_id") or st.session_state.get("sync_audio_path"))


def _mode_label(opts: dict) -> str:
    return "빠른 분석" if opts["fast_mode"] else "정밀 분석"


def _eta_kwargs(opts: dict) -> dict:
    return {
        "fast_mode": opts["fast_mode"],
        "use_gpt": opts["use_gpt"],
        "use_youtube": bool(opts.get("use_youtube")),
        "mr_likely": bool(st.session_state.get("upload_mr_likely")),
    }


def _eta_for_progress(pct: float, opts: dict) -> str:
    started = st.session_state.get("analysis_started_at")
    rem = remaining_seconds(pct, started_at=started, **_eta_kwargs(opts))
    return format_eta(rem)


def _mark_analysis_started(opts: dict) -> None:
    st.session_state["analysis_started_at"] = time.time()
    st.session_state["analysis_mode_fast"] = opts["fast_mode"]
    st.session_state["analysis_use_gpt"] = opts["use_gpt"]


def clear_analysis_state() -> None:
    for key in (
        "pending_job_id",
        "sync_audio_path",
        "analysis_started_at",
        "analysis_mode_fast",
        "analysis_use_gpt",
        "analysis_cancelled"
    ):
        st.session_state.pop(key, None)


def cancel_analysis() -> None:
    """분석 중단."""
    job_id = st.session_state.get("pending_job_id")
    if job_id:
        try:
            from analysis_queue import cancel_job

            cancel_job(job_id)
        except Exception:
            pass
    st.session_state["analysis_cancelled"] = True
    clear_analysis_state()


def _persist_session_cache(session: dict, opts: dict) -> None:
    user_id = opts.get("user_id")
    if not user_id:
        return
    try:
        from ui.session_cache import save_session_cache

        save_session_cache(user_id, session, session.get("record_path"))
    except Exception:
        pass


def _render_analyzing_panel_header(opts: dict) -> None:
    render_safe_html('<script>document.body.classList.add("vc-analyzing");</script>')
    mode = _mode_label(opts)
    title_col, cancel_col = st.columns([4.2, 1.3], vertical_alignment="center")
    with title_col:
        render_safe_html(f"""
            <div class="vc-analyze-panel-head">
                <p class="vc-analyze-panel-title">잠시만요 🎵</p>
                <p class="vc-analyze-panel-desc">선생님이 녹음을 듣고 있어요 · 창을 닫지 마세요</p>
                <p class="vc-analyzing-mode">{mode} 진행 중</p>
            </div>
            """
        )
    with cancel_col:
        from ui.analysis_overlay import render_cancel_button

        if render_cancel_button(key="btn_cancel_analysis_main"):
            cancel_analysis()
            from ui.analysis_overlay import clear_analyze_stage

            clear_analyze_stage()
            st.toast("분석을 취소했어요.")
            st.rerun()


def _render_analyzing_view(pct: float, message: str, opts: dict) -> None:
    mode = _mode_label(opts)
    eta = _eta_for_progress(pct, opts)
    with st.container(key="vc_analyze_panel"):
        _render_analyzing_panel_header(opts)
        render_stepper(pct, message, eta_label=eta, mode_label=mode)
    from ui.scroll import scroll_analyze_panel

    scroll_analyze_panel()


def _render_analyzing_view_with_placeholder(pct: float, message: str, opts: dict):
    """동기 분석 — stepper만 placeholder로 갱신."""
    mode = _mode_label(opts)
    eta = _eta_for_progress(pct, opts)
    with st.container(key="vc_analyze_panel"):
        _render_analyzing_panel_header(opts)
        stepper_ph = st.empty()
        with stepper_ph.container():
            render_stepper(pct, message, eta_label=eta, mode_label=mode)
    from ui.scroll import scroll_analyze_panel

    scroll_analyze_panel()
    return stepper_ph


def _poll_queue_job(job_id: str, opts: dict) -> str:
    from analysis_queue import JobStatus, get_job, load_session_for_job

    job = get_job(job_id)
    if not job:
        st.error("작업을 찾을 수 없습니다.")
        return "failed"

    pct = job.progress / 100.0
    eta = _eta_for_progress(pct, opts)
    mode = _mode_label(opts)
    render_stepper(pct, job.message, eta_label=eta, mode_label=mode)

    if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        if st.session_state.get("analysis_cancelled"):
            cancel_analysis()
            return "failed"
        return "running"

    if job.status == JobStatus.FAILED:
        err = job.error or "알 수 없는 오류"
        if "취소" not in err:
            st.error(f"분석 실패: {err}")
        return "failed"

    if job.status == JobStatus.DONE:
        session = load_session_for_job(job_id)
        if session:
            st.session_state["last_session"] = session
            _persist_session_cache(session, opts)
            st.session_state["mypage_show_result"] = True
            return "done"
        st.warning("결과를 불러오지 못했습니다. 다시 시도해 주세요.")
        return "failed"

    return "running"


@st.fragment(run_every=1.2)
def _analysis_queue_fragment(job_id: str) -> None:
    """큐 폴링 — fragment만 갱신해 전체 화면 깜빡임 방지."""
    opts = _analysis_options()
    with st.container(key="vc_analyze_panel"):
        _render_analyzing_panel_header(opts)
        result = _poll_queue_job(job_id, opts)
    from ui.scroll import scroll_analyze_panel

    scroll_analyze_panel()
    if result == "running":
        return

    from ui.analysis_overlay import clear_analyze_stage

    if result == "done":
        clear_analysis_state()
        st.session_state["scroll_analyze"] = True
        st.session_state.pop("scroll_analyze_ticks", None)
        st.session_state["scroll_result"] = True
        clear_analyze_stage()
        from ui.loading import clear_loading

        clear_loading()
        st.balloons()
        st.rerun()
    elif result == "failed":
        clear_analysis_state()
        st.session_state.pop("analysis_cancelled", None)
        clear_analyze_stage()
        from ui.loading import clear_loading

        clear_loading()
        st.rerun()


def _run_sync_analysis(audio_path: Path, opts: dict, stepper_ph) -> bool:
    started = st.session_state.get("analysis_started_at")
    mode = _mode_label(opts)
    base_cb = make_callback(st.empty(), stepper_ph, st.empty())

    def on_progress(pct: float, msg: str) -> None:
        eta = format_eta(
            remaining_seconds(pct, started_at=started, **_eta_kwargs(opts))
        )
        base_cb(pct, msg, eta_label=eta, mode_label=mode)

    try:
        from analysis import run_full_session

        buf = io.StringIO()
        with redirect_stdout(buf):
            ref = opts.get("reference_path")
            session = run_full_session(
                audio_path,
                song_title=opts["song_title"],
                use_youtube=opts["use_youtube"],
                use_gpt=opts["use_gpt"],
                save_record=opts["save_record"],
                compare=opts["compare"],
                export_clips=opts["export_clips"],
                growth_chart=opts["growth_chart"],
                save_plot=PROJECT_DIR / "pitch_result.png",
                fast_mode=opts["fast_mode"],
                style_preset=opts["style_preset"],
                user_id=opts["user_id"],
                reference_path=Path(ref) if ref else None,
                on_progress=on_progress
            )
        st.session_state["last_session"] = session
        st.session_state["last_log"] = buf.getvalue()
        _persist_session_cache(session, opts)
        st.session_state["mypage_show_result"] = True
        return True
    except Exception as exc:
        st.error(f"분석 실패: {exc}")
        return False


def _resolve_audio_source(
    *,
    recorded,
    uploaded,
    use_sample: bool,
    sample: Path,
    upload_dir: Path
) -> Path | None:
    """녹음 > 업로드 > 샘플 순으로 분석용 파일 경로 결정."""
    upload_dir.mkdir(parents=True, exist_ok=True)

    if recorded is not None:
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = upload_dir / f"recording_{ts}.wav"
        audio_path.write_bytes(recorded.getvalue())
        return audio_path

    if uploaded is not None:
        audio_path = upload_dir / uploaded.name
        audio_path.write_bytes(uploaded.getvalue())
        return audio_path

    if use_sample and sample.exists():
        return sample

    return None


def _maybe_auto_precision_on_mr(audio_path: Path, opts: dict) -> dict:
    """MR 감지 + 설정 켜짐이면 정밀 분석으로 전환."""
    if not opts.get("fast_mode", True):
        return opts
    if not st.session_state.get("auto_precision_on_mr", True):
        return opts
    likely = st.session_state.get("upload_mr_likely")
    if likely is None:
        likely = _quick_mr_check(audio_path)
        st.session_state["upload_mr_likely"] = likely
    if likely:
        st.session_state["force_precision"] = True
        opts = dict(opts)
        opts["fast_mode"] = False
    return opts


def _render_song_hint_banner() -> None:
    hint = st.session_state.get("_song_hint")
    if not hint:
        return
    genre = hint.get("genre_label") or ""
    genre_txt = f" · {genre}" if genre else ""
    yt_on = st.session_state.get("use_youtube")
    yt_line = " · 유튜브 가이드 ON" if yt_on else ""
    render_safe_html(
        f"""
        <div class="vc-song-hint-banner">
            <p class="vc-song-hint-title">🎵 {hint.get("artist", "")} — {hint.get("title", "")}{genre_txt}{yt_line}</p>
            <p class="vc-song-hint-body">인기곡 DB · 검색어·가창 스타일 자동 적용{"" if yt_on else " · 유튜브는 아래 버튼으로 켤 수 있어요"}</p>
        </div>
        """
    )
    if not yt_on and not st.session_state.get("auto_youtube_on_hint", True):
        if st.button("📺 유튜브 가이드 켜기", key="btn_enable_yt_from_hint", use_container_width=True):
            st.session_state["use_youtube"] = True
            st.rerun()


def _invalidate_mr_cache_on_new_upload(recorded, uploaded) -> None:
    sig = None
    if recorded is not None:
        sig = f"rec:{getattr(recorded, 'size', 0)}"
    elif uploaded is not None:
        sig = f"up:{uploaded.name}:{getattr(uploaded, 'size', 0)}"
    prev = st.session_state.get("_upload_file_sig")
    if sig != prev:
        st.session_state["_upload_file_sig"] = sig
        st.session_state.pop("upload_mr_likely", None)


def _quick_mr_check(audio_path: Path) -> bool:
    """앞 30초만 샘플링 — MR 포함 가능성."""
    try:
        import librosa
        from mr_detect import detect_mr_content

        y, sr = librosa.load(str(audio_path), sr=16000, mono=True, duration=30.0)
        return bool(detect_mr_content(y, sr).likely_mr)
    except Exception:
        return False


def _render_precision_recommendation(
    opts: dict,
    *,
    recorded,
    uploaded,
    use_sample: bool,
    sample: Path,
    upload_dir: Path
) -> None:
    """MR·믹스 녹음 시 정밀 분석 권장."""
    if not opts.get("fast_mode", True) or is_analyzing():
        return

    has_file = (
        recorded is not None
        or uploaded is not None
        or (use_sample and sample.exists())
    )
    if not has_file:
        return

    likely_mr = st.session_state.get("upload_mr_likely")
    if likely_mr is None and (recorded or uploaded):
        path = _resolve_audio_source(
            recorded=recorded,
            uploaded=uploaded,
            use_sample=False,
            sample=sample,
            upload_dir=upload_dir
        )
        if path and path.exists():
            likely_mr = _quick_mr_check(path)
            st.session_state["upload_mr_likely"] = likely_mr

    if likely_mr:
        render_safe_html(
            """
            <div class="vc-precision-recommend">
                <p class="vc-precision-recommend-title">🎧 반주가 함께 들려요</p>
                <p class="vc-precision-recommend-body">
                    MR·반주가 섞인 녹음이에요. 목소리만 또렷하게 듣고 피드백 받으려면
                    <b>정밀 분석</b>을 추천드려요.
                </p>
            </div>
            """
        )
        if st.button(
            "⚡ 정밀 분석으로 전환",
            key="btn_switch_precision_mode",
            use_container_width=True
        ):
            st.session_state["force_precision"] = True
            st.session_state.pop("upload_mr_likely", None)
            st.rerun()
    elif opts.get("fast_mode"):
        st.caption("💡 MR이 섞인 녹음이면 정밀 분석이 더 정확해요.")


def _render_upload_form(opts: dict, *, disabled: bool = False) -> None:
    from ui.audio_recorder import render_file_upload_fallback, render_live_recorder

    render_safe_html('<div id="vc-new-analysis"></div>')
    render_safe_html(
        """
        <div class="vc-app-card">
            <p class="vc-new-analysis-title">🎤 새 분석</p>
            <p class="vc-new-analysis-desc">녹음 → 점수 · 코치 DM까지 한 번에</p>
        </div>
        """
    )

    recorded = render_live_recorder(disabled=disabled, key="analysis_live_recorder")
    uploaded, use_sample = render_file_upload_fallback(disabled=disabled)
    _invalidate_mr_cache_on_new_upload(recorded, uploaded)
    _render_song_hint_banner()

    upload_dir = PROJECT_DIR / ".cache" / "uploads"
    sample = PROJECT_DIR / "sample.mp3"
    _render_precision_recommendation(
        opts,
        recorded=recorded,
        uploaded=uploaded,
        use_sample=use_sample,
        sample=sample,
        upload_dir=upload_dir
    )

    has_file = (
        recorded is not None
        or uploaded is not None
        or (use_sample and (PROJECT_DIR / "sample.mp3").exists())
    )

    if not has_file and not disabled:
        with st.expander("💡 Vocal Coach AI가 이렇게 도와드려요", expanded=False):
            from ui.welcome import render as render_welcome

            render_welcome()

    mode_label = _mode_label(opts)
    try:
        from usage_limits import check_analysis_allowed

        _, limit_msg, _, _ = check_analysis_allowed(opts.get("user_id"))
        if limit_msg:
            st.caption(limit_msg)
    except Exception:
        pass
    render_safe_html(
        f'<p class="vc-start-hint">설정: <b>{mode_label}</b> · 위 <b>분석 설정</b>에서 변경</p>'
    )

    analyzing_now = disabled or is_analyzing()

    if analyzing_now:
        st.button(
            "⏳ 분석 중… 잠시만 기다려 주세요",
            type="primary",
            use_container_width=True,
            key="btn_analyzing_status",
            disabled=True
        )
    elif st.button(
        f"🎤 {mode_label} 시작하기",
        type="primary",
        use_container_width=True,
        key="btn_start_analysis",
        disabled=not has_file
    ):
        upload_dir = PROJECT_DIR / ".cache" / "uploads"
        sample = PROJECT_DIR / "sample.mp3"
        audio_path = _resolve_audio_source(
            recorded=recorded,
            uploaded=uploaded,
            use_sample=use_sample,
            sample=sample,
            upload_dir=upload_dir
        )
        if audio_path is None:
            st.warning("녹음 또는 파일을 선택한 뒤 다시 시도해 주세요.")
            return

        try:
            from audio_normalize import ensure_normalized

            audio_path = ensure_normalized(audio_path)
        except Exception as exc:
            st.warning(f"오디오 정규화 건너뜀: {exc}")

        try:
            from audio_guardrails import AudioGuardrailError, validate_audio_file

            validate_audio_file(audio_path)
        except AudioGuardrailError as exc:
            st.error(exc.message)
            return
        except Exception as exc:
            st.error(f"⚠️ 오디오 검증 실패: {exc}")
            return

        opts = _maybe_auto_precision_on_mr(audio_path, opts)

        try:
            from usage_limits import check_analysis_allowed

            allowed, limit_msg, _, _ = check_analysis_allowed(opts.get("user_id"))
            if not allowed:
                st.error(limit_msg)
                return
        except Exception:
            pass

        _mark_analysis_started(opts)
        st.session_state["scroll_analyze"] = True
        from ui.loading import mark_loading

        mark_loading(message="분석을 시작합니다…")

        if opts["use_queue"]:
            from analysis_queue import submit_analysis

            job_id = submit_analysis(
                audio_path,
                song_title=opts["song_title"],
                use_youtube=opts["use_youtube"],
                use_gpt=opts["use_gpt"],
                save_record=opts["save_record"],
                compare=opts["compare"],
                export_clips=opts["export_clips"],
                growth_chart=opts["growth_chart"],
                fast_mode=opts["fast_mode"],
                style_preset=opts["style_preset"],
                user_id=opts["user_id"],
                reference_path=str(opts["reference_path"]) if opts.get("reference_path") else None
            )
            st.session_state["pending_job_id"] = job_id
            st.rerun()
            return

        st.session_state["sync_audio_path"] = str(audio_path)
        st.rerun()


def _maybe_scroll_to_analyzing() -> None:
    """분석 UI 렌더 후 상단 스크롤 (앵커 생성 이후)."""
    if not st.session_state.get("scroll_analyze"):
        return
    from ui.scroll import scroll_to_top

    scroll_to_top()
    ticks = int(st.session_state.get("scroll_analyze_ticks", 0)) + 1
    st.session_state["scroll_analyze_ticks"] = ticks
    if ticks >= 3:
        st.session_state.pop("scroll_analyze", None)
        st.session_state.pop("scroll_analyze_ticks", None)


def render_analysis_section(*, show_settings: bool = True) -> None:
    """마이 페이지 내 새 분석 — 설정(펼침) + 업로드 + 진행."""
    from ui.analysis_settings import render_analysis_settings_expander

    opts = _analysis_options()
    analyzing = is_analyzing()

    if show_settings and not analyzing:
        render_analysis_settings_expander(expanded=True)

    pending = st.session_state.get("pending_job_id")
    if pending:
        if not st.session_state.get("analysis_started_at"):
            _mark_analysis_started(opts)
        from ui.loading import mark_loading

        mark_loading(message="분석을 진행하고 있어요…")
        _maybe_scroll_to_analyzing()
        _analysis_queue_fragment(pending)
        return

    sync_path = st.session_state.get("sync_audio_path")
    if sync_path:
        if not st.session_state.get("analysis_started_at"):
            _mark_analysis_started(opts)
        stepper_ph = _render_analyzing_view_with_placeholder(0, "분석을 시작합니다…", opts)
        _maybe_scroll_to_analyzing()
        ok = _run_sync_analysis(Path(sync_path), opts, stepper_ph)
        st.session_state.pop("sync_audio_path", None)
        if ok:
            clear_analysis_state()
            from ui.analysis_overlay import clear_analyze_stage
            from ui.loading import clear_loading

            clear_analyze_stage()
            clear_loading()
            st.session_state["scroll_analyze"] = True
            st.session_state.pop("scroll_analyze_ticks", None)
            st.session_state["scroll_result"] = True
            st.balloons()
            st.rerun()
        else:
            clear_analysis_state()
            from ui.analysis_overlay import clear_analyze_stage
            from ui.loading import clear_loading

            clear_analyze_stage()
            clear_loading()
        return

    _render_upload_form(opts, disabled=False)


def render_crop_notice(session: dict) -> None:
    """완곡 자동 컷(150초) 안내 — 결과 화면 최상단."""
    from analysis import SMART_MAX_DURATION_SEC

    is_cropped = session.get("is_cropped") or getattr(
        session.get("report"), "is_cropped", False
    )
    if not is_cropped:
        return
    orig = session.get("original_duration_sec") or getattr(
        session.get("report"), "original_duration_sec", None
    )
    extra = ""
    if orig and float(orig) > SMART_MAX_DURATION_SEC:
        extra = f" (전체 {float(orig):.0f}초)"
    render_safe_html(
        f"""\
<div class="vc-crop-banner">
<span class="vc-crop-icon">💡</span>
<div>
<p class="vc-crop-title">1절(2분 30초) 구간만 우선 진단했습니다{extra}</p>
<p class="vc-crop-body">원활한 분석 환경을 위해 앞부분만 분석했어요. 완곡 정밀 분석은 곧 <b>프리미엄 서비스</b>로 오픈됩니다!</p>
</div>
</div>"""
    )


def render_results_view() -> None:
    from ui.coach_chat import render_coach_dm

    session = st.session_state["last_session"]
    render_crop_notice(session)
    render_coach_dm(session)


def render() -> None:
    """하위 호환 — 마이 페이지 분석 섹션."""
    render_analysis_section()
