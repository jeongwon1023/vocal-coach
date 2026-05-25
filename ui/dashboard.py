"""분석 대시보드 — 로그인 필수 · 친화형 진행 UI · 결과 화면."""

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
from ui.beta import render_beta_footer
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


def _is_analyzing() -> bool:
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


def _clear_analysis_state() -> None:
    for key in (
        "pending_job_id",
        "sync_audio_path",
        "analysis_started_at",
        "analysis_mode_fast",
        "analysis_use_gpt",
    ):
        st.session_state.pop(key, None)


def _render_login_gate() -> None:
    from ui.auth import start_demo

    st.markdown(
        """
        <div class="vc-login-gate">
            <div class="vc-chat-card vc-login-card">
                <div class="vc-chat-avatar">🔐</div>
                <div class="vc-chat-body">
                    <p class="vc-chat-name">Vocal Coach AI</p>
                    <p class="vc-chat-msg">분석을 시작하려면 로그인이 필요해요.<br>
                    카카오 · Google · 체험 계정 중 하나를 선택해 주세요.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✦ 체험 계정으로 시작", type="primary", use_container_width=True, key="gate_demo"):
            start_demo()
    with col2:
        st.markdown(
            '<p class="vc-gate-hint">또는 우측 상단<br><b>로그인 / 회원가입</b> 클릭</p>',
            unsafe_allow_html=True,
        )


def _render_settings_summary(opts: dict) -> None:
    """현재 설정 요약 + 설정 열기 버튼."""
    from ui.analysis_settings import render_settings_open_button

    mode = _mode_label(opts)
    yt = "ON" if opts["use_youtube"] else "OFF"
    gpt = "ON" if opts["use_gpt"] else "OFF"
    st.markdown(
        f"""
        <div class="vc-settings-pill-row">
            <span class="vc-settings-pill">⚡ {mode}</span>
            <span class="vc-settings-pill">📺 유튜브 {yt}</span>
            <span class="vc-settings-pill">🤖 GPT {gpt}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="vc-sidebar-hint-text">아래 <b>분석 설정</b> 버튼에서 정밀 분석 · 유튜브 · GPT를 바꿀 수 있어요</p>',
        unsafe_allow_html=True,
    )
    render_settings_open_button()


def _render_page_head(opts: dict) -> None:
    from ui.auth import current_user

    user = current_user()
    name = user.get("name", "학습자") if user else "학습자"
    st.markdown(
        f"""
        <div class="vc-page-head">
            <h2 class="vc-page-title">안녕하세요, {name}님 👋</h2>
            <p class="vc-page-desc">녹음 파일을 올리면 1분 안에 코칭 결과를 받아요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_settings_summary(opts)


def _render_analyzing_view(pct: float, message: str, opts: dict) -> tuple:
    """분석 중 전용 화면 — 채팅형 카드 + 남은 시간."""
    mode = _mode_label(opts)
    eta = _eta_for_progress(pct, opts)
    st.markdown(
        f"""
        <div class="vc-analyzing-header">
            <h2 class="vc-page-title">잠시만요 🎵</h2>
            <p class="vc-page-desc">선생님이 녹음을 듣고 있어요 · 창을 닫지 마세요</p>
            <p class="vc-analyzing-mode">{mode} 진행 중</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    stepper_ph = st.empty()
    with stepper_ph.container():
        render_stepper(pct, message, eta_label=eta, mode_label=mode)
    return stepper_ph


def _poll_queue_job(job_id: str, stepper_ph, opts: dict) -> str:
    from analysis_queue import JobStatus, get_job, load_session_for_job

    job = get_job(job_id)
    if not job:
        st.error("작업을 찾을 수 없습니다.")
        return "failed"

    pct = job.progress / 100.0
    eta = _eta_for_progress(pct, opts)
    mode = _mode_label(opts)
    with stepper_ph.container():
        render_stepper(pct, job.message, eta_label=eta, mode_label=mode)

    if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        time.sleep(1.0)
        st.rerun()

    if job.status == JobStatus.FAILED:
        st.error(f"분석 실패: {job.error or '알 수 없는 오류'}")
        return "failed"

    if job.status == JobStatus.DONE:
        session = load_session_for_job(job_id)
        if session:
            st.session_state["last_session"] = session
            return "done"
        st.warning("결과를 불러오지 못했습니다. 다시 시도해 주세요.")
        return "failed"

    return "running"


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
        return True
    except Exception as exc:
        st.error(f"분석 실패: {exc}")
        return False


def _render_results_view() -> None:
    render_coach_dm(st.session_state["last_session"])


def _render_upload_form(opts: dict, *, disabled: bool = False) -> None:
    if disabled:
        st.info("⏳ 분석이 끝날 때까지 아래 버튼은 잠시 쉬어요. 창을 닫지 마세요.")

    st.markdown(
        """
        <div class="vc-upload-card">
            <p class="vc-upload-emoji">🎙️</p>
            <p class="vc-upload-title">녹음 파일 올리기</p>
            <p class="vc-upload-desc">MP3 · WAV · M4A · 유튜브 MR도 OK</p>
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
        value=uploaded is None and sample.exists() and not disabled,
        key="use_sample_check",
        disabled=disabled,
    )

    if uploaded is None and not use_sample and not disabled:
        from ui.help_guide import render_youtube_guide_inline
        from ui.welcome import render as render_welcome

        render_youtube_guide_inline()
        render_welcome()
        return

    if uploaded is not None and not disabled:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        st.audio(uploaded.getvalue(), format=f"audio/{ext}")

    mode_label = _mode_label(opts)
    st.markdown(
        f'<p class="vc-start-hint">설정: <b>{mode_label}</b> · <b>분석 설정</b> 버튼에서 변경</p>',
        unsafe_allow_html=True,
    )
    if st.button(
        f"🎤 {mode_label} 시작하기",
        type="primary",
        use_container_width=True,
        key="btn_start_analysis",
        disabled=disabled,
    ):
        upload_dir = PROJECT_DIR / ".cache" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        if uploaded is not None:
            audio_path = upload_dir / uploaded.name
            audio_path.write_bytes(uploaded.getvalue())
        elif use_sample and sample.exists():
            audio_path = sample
        else:
            st.warning("녹음 파일을 선택하거나 샘플 테스트를 켜 주세요.")
            return

        try:
            from audio_normalize import ensure_normalized

            audio_path = ensure_normalized(audio_path)
        except Exception as exc:
            st.warning(f"오디오 정규화 건너뜀: {exc}")

        _mark_analysis_started(opts)

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


def render() -> None:
    from ui.auth import is_logged_in

    if not is_logged_in():
        _render_login_gate()
        return

    opts = _analysis_options()
    analyzing = _is_analyzing()

    if st.session_state.get("last_session") and not analyzing:
        _render_results_view()
        render_beta_footer()
        return

    _render_page_head(opts)

    pending = st.session_state.get("pending_job_id")
    if pending:
        if not st.session_state.get("analysis_started_at"):
            _mark_analysis_started(opts)
        stepper_ph = _render_analyzing_view(0, "분석 준비 중…", opts)
        result = _poll_queue_job(pending, stepper_ph, opts)
        if result == "done":
            _clear_analysis_state()
            st.balloons()
            st.rerun()
        elif result == "failed":
            _clear_analysis_state()
        _render_upload_form(opts, disabled=True)
        return

    sync_path = st.session_state.get("sync_audio_path")
    if sync_path:
        if not st.session_state.get("analysis_started_at"):
            _mark_analysis_started(opts)
        stepper_ph = _render_analyzing_view(0, "분석을 시작합니다…", opts)
        ok = _run_sync_analysis(Path(sync_path), opts, stepper_ph)
        st.session_state.pop("sync_audio_path", None)
        if ok:
            _clear_analysis_state()
            st.balloons()
            st.rerun()
        else:
            _clear_analysis_state()
        _render_upload_form(opts, disabled=True)
        return

    _render_upload_form(opts, disabled=False)
    render_beta_footer()
