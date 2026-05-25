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
from ui.coach_chat import render_coach_dm
from ui.progress import make_callback, render_stepper


def _analysis_options() -> dict:
    song = (st.session_state.get("song_title") or "").strip()
    fast = bool(st.session_state.get("fast_mode", True))
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
    }


def is_analyzing() -> bool:
    return bool(st.session_state.get("pending_job_id") or st.session_state.get("sync_audio_path"))


def _mode_label(opts: dict) -> str:
    return "빠른 분석" if opts["fast_mode"] else "정밀 분석"


def _eta_for_progress(pct: float, opts: dict) -> str:
    started = st.session_state.get("analysis_started_at")
    rem = remaining_seconds(
        pct,
        fast_mode=opts["fast_mode"],
        started_at=started,
        use_gpt=opts["use_gpt"],
    )
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
        "analysis_cancelled",
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
    mode = _mode_label(opts)
    title_col, cancel_col = st.columns([4.2, 1.3], vertical_alignment="center")
    with title_col:
        st.markdown(
            f"""
            <div class="vc-analyze-panel-head">
                <p class="vc-analyze-panel-title">잠시만요 🎵</p>
                <p class="vc-analyze-panel-desc">선생님이 녹음을 듣고 있어요 · 창을 닫지 마세요</p>
                <p class="vc-analyzing-mode">{mode} 진행 중</p>
            </div>
            """,
            unsafe_allow_html=True,
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
    st.markdown('<div id="vc-analyzing-anchor"></div>', unsafe_allow_html=True)
    with st.container(key="vc_analyze_panel"):
        _render_analyzing_panel_header(opts)
        render_stepper(pct, message, eta_label=eta, mode_label=mode)
    from ui.scroll import scroll_analyze_panel

    scroll_analyze_panel()


def _render_analyzing_view_with_placeholder(pct: float, message: str, opts: dict):
    """동기 분석 — stepper만 placeholder로 갱신."""
    mode = _mode_label(opts)
    eta = _eta_for_progress(pct, opts)
    st.markdown('<div id="vc-analyzing-anchor"></div>', unsafe_allow_html=True)
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
    mode = _mode_label(opts)
    st.markdown('<div id="vc-analyzing-anchor"></div>', unsafe_allow_html=True)
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
            remaining_seconds(
                pct,
                fast_mode=opts["fast_mode"],
                started_at=started,
                use_gpt=opts["use_gpt"],
            )
        )
        base_cb(pct, msg, eta_label=eta, mode_label=mode)

    try:
        from analysis import run_full_session

        buf = io.StringIO()
        with redirect_stdout(buf):
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
                on_progress=on_progress,
            )
        st.session_state["last_session"] = session
        st.session_state["last_log"] = buf.getvalue()
        _persist_session_cache(session, opts)
        st.session_state["mypage_show_result"] = True
        return True
    except Exception as exc:
        st.error(f"분석 실패: {exc}")
        return False


def _render_upload_form(opts: dict, *, disabled: bool = False) -> None:
    st.markdown(
        """
        <div class="vc-upload-card">
            <p class="vc-upload-emoji">🎙️</p>
            <p class="vc-upload-title">녹음 파일을 올려 주세요</p>
            <p class="vc-upload-desc">MP3 · WAV · M4A · 핸드폰 녹음도 OK</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "녹음 파일",
        type=["mp3", "wav", "m4a", "flac", "ogg"],
        label_visibility="collapsed",
        key="analysis_uploader",
        disabled=disabled,
    )

    sample = PROJECT_DIR / "sample.mp3"
    use_sample = st.toggle(
        "샘플(sample.mp3)으로 테스트",
        value=False,
        key="use_sample_check",
        disabled=disabled,
    )

    has_file = uploaded is not None or (use_sample and sample.exists())

    if uploaded is not None and not disabled:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        st.audio(uploaded.getvalue(), format=f"audio/{ext}")

    if not has_file and not disabled:
        st.markdown(
            """
            <div class="vc-upload-hint">
                <span class="vc-upload-hint-icon">📎</span>
                <p class="vc-upload-hint-text">
                    아직 녹음 파일이 없어요.<br>
                    <span>위에서 파일을 선택하면 분석을 시작할 수 있어요.</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        from ui.welcome import render as render_welcome

        render_welcome()

    mode_label = _mode_label(opts)
    st.markdown(
        f'<p class="vc-start-hint">설정: <b>{mode_label}</b> · 위 <b>분석 설정</b>에서 변경</p>',
        unsafe_allow_html=True,
    )

    analyzing_now = disabled or is_analyzing()

    if analyzing_now:
        st.button(
            "⏳ 분석 중… 잠시만 기다려 주세요",
            type="primary",
            use_container_width=True,
            key="btn_analyzing_status",
            disabled=True,
        )
    elif st.button(
        f"🎤 {mode_label} 시작하기",
        type="primary",
        use_container_width=True,
        key="btn_start_analysis",
        disabled=not has_file,
    ):
        upload_dir = PROJECT_DIR / ".cache" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        if uploaded is not None:
            audio_path = upload_dir / uploaded.name
            audio_path.write_bytes(uploaded.getvalue())
        elif use_sample and sample.exists():
            audio_path = sample
        else:
            st.warning("녹음 파일을 업로드하지 않았어요. 파일을 선택한 뒤 다시 시도해 주세요.")
            return

        try:
            from audio_normalize import ensure_normalized

            audio_path = ensure_normalized(audio_path)
        except Exception as exc:
            st.warning(f"오디오 정규화 건너뜀: {exc}")

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


def render_results_view() -> None:
    render_coach_dm(st.session_state["last_session"])


def clear_results_state() -> None:
    for key in (
        "last_session",
        "last_log",
        "coach_chat_fp",
        "coach_chat_messages",
        "coach_suggested_questions",
        "coach_gpt_enhanced",
        "mypage_show_result",
        "coach_show_typing",
        "coach_generating",
        "coach_pending_message",
        "coach_used_suggestions",
        "coach_scroll_tick",
    ):
        st.session_state.pop(key, None)


def render() -> None:
    """하위 호환 — 마이 페이지 분석 섹션."""
    render_analysis_section()
