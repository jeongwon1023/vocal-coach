"""Instagram DM 스타일 AI 보컬 코치 채팅 — Codeit inspired."""

from __future__ import annotations

import hashlib
from typing import Any

import streamlit as st

from coaching_vocab import STAGE_NAMES


def _session_fingerprint(session: dict[str, Any]) -> str:
    report = session["report"]
    blob = f"{report.overall_score}:{len(report.stages)}:{session.get('record_path', '')}"
    return hashlib.md5(blob.encode()).hexdigest()[:12]


def _analysis_payload(session: dict[str, Any]) -> dict[str, Any]:
    from analysis import report_to_gpt_payload

    return report_to_gpt_payload(session["report"])


def _rule_opening(session: dict[str, Any]) -> str:
    report = session["report"]
    full = session.get("full_record") or {}
    name = "학습자"
    try:
        from ui.auth import current_user

        u = current_user()
        if u:
            name = u.get("name", name)
    except Exception:
        pass

    overall = report.overall_score
    stages = report.stages[:3]
    lines = [f"{name}님, 분석 끝났어요! 선생님이 들어봤어요 🎤", ""]

    s4 = next((s for s in report.stages if s.stage == 4), None)
    strengths = (s4.details.get("teacher_strengths") if s4 else None) or []
    if strengths:
        lines.append("🌟 **오늘 특히 좋았던 점**")
        for s in strengths[:2]:
            lines.append(f"· {s}")
        lines.append("")

    if stages:
        lines.append("📊 **영역별 점수**")
        for s in stages:
            label = STAGE_NAMES.get(s.stage, s.title)
            lines.append(f"· {label} **{s.score:.0f}점**")
        lines.append("")

    weakest = min(stages, key=lambda s: s.score) if stages else None
    if weakest:
        label = STAGE_NAMES.get(weakest.stage, weakest.title)
        lines.append(
            f"🎯 **먼저 같이 볼 부분**은 {label}({weakest.score:.0f}점)이에요. "
            f"여기만 10분 연습해도 전체 느낌이 확 달라져요."
        )
    else:
        lines.append(f"🎯 종합 **{overall:.0f}점** — 꾸준히 연습하면 더 올라갈 거예요.")

    actions = full.get("priority_actions") or []
    if actions and isinstance(actions[0], dict):
        act = actions[0].get("action") or actions[0].get("title") or ""
        if act:
            lines.append(f"\n💡 오늘 추천: {act}")

    lines.append("\n궁금한 거 편하게 물어보세요. 선생님이 DM처럼 답해 드릴게요 😊")
    return "\n".join(lines)


def _rule_suggested_questions(session: dict[str, Any]) -> list[str]:
    report = session["report"]
    stages = report.stages[:3]
    qs: list[str] = []

    if not stages:
        return [
            "오늘 연습은 뭐부터 하면 좋을까요?",
            "음정을 더 안정적으로 부르려면?",
            "10분 루틴 짜 주세요",
        ]

    weakest = min(stages, key=lambda s: s.score)
    label = STAGE_NAMES.get(weakest.stage, "이 부분")

    if weakest.stage == 1:
        qs.append("음정이 틀린 구간만 집중해서 연습하려면 어떻게 해요?")
    elif weakest.stage == 2:
        qs.append("박자가 밀릴 때 메트로놈으로 어떻게 잡으면 좋을까요?")
    else:
        qs.append("호흡이나 목소리 톤을 더 예쁘게 하려면요?")

    devs = report.pitch_deviation_segments[:1]
    if devs:
        d = devs[0]
        qs.append(f"{d.start_sec:.0f}~{d.end_sec:.0f}초 구간을 어떻게 연습하면 좋을까요?")
    else:
        qs.append("오늘 10~15분 연습 루틴 짜 주세요")

    qs.append("다음 녹음 때 체크할 포인트 3가지만 알려주세요")
    return qs[:3]


def _rule_reply(session: dict[str, Any], user_message: str) -> str:
    report = session["report"]
    stages = report.stages[:3]
    weakest = min(stages, key=lambda s: s.score) if stages else None
    msg = user_message.lower()

    if any(k in msg for k in ("10분", "15분", "루틴", "연습")):
        wlabel = STAGE_NAMES.get(weakest.stage, "기본") if weakest else "음정"
        return (
            f"좋아요, 오늘 **10분 루틴**이에요.\n\n"
            f"① 2분 — 복식호흡 4-4-8 (코로 들이마시고 천천히 내쉬기)\n"
            f"② 4분 — {wlabel} 약한 구간만 0.5배속 구간 루프\n"
            f"③ 3분 — 원곡 MR 80% 속도로 한 번 통으로\n"
            f"④ 1분 — 오늘 잘된 한 마디만 느리게 롱톤\n\n"
            f"내일 같은 곡 다시 녹음해서 점수 비교해 봐요!"
        )
    if any(k in msg for k in ("음정", "피치", "톤")):
        return (
            "음정은 **귀 + 작은 소리**로 잡는 게 제일 빨라요.\n"
            "틀린 구간만 피아노·가이드 멜로디랑 같이 0.5배속으로 5번씩.\n"
            "큰 소리보다 **작게, 정확하게** 반복하는 게 포인트예요."
        )
    if any(k in msg for k in ("박", "리듬", "박자")):
        return (
            "박자는 발로 탭하면서 MR 70% 속도로 연습해 보세요.\n"
            "박이 밀리면 **호흡을 미리 준비**하는 습관이 중요해요.\n"
            "프레이즈 시작 전에 1박 쉬고 들어가면 안정돼요."
        )
    if any(k in msg for k in ("호흡", "브레스", "다이내믹")):
        return (
            "호흡은 '크게 마시기'보다 **천천히, 깊게**가 핵심이에요.\n"
            "복식호흡으로 4초 들이마시고 8초 내쉬기 — 하루 5분만 해도 달라져요.\n"
            "고음 직전에 어깨 힘 빼는 것도 꼭 기억하세요."
        )

    score = report.overall_score
    return (
        f"좋은 질문이에요! 종합 {score:.0f}점 기준으로 보면, "
        f"{'음정·박자·호흡 중 하나씩' if stages else '꾸준한'} "
        f"짧게라도 매일 연습하는 게 제일 효과적이에요.\n"
        f"더 구체적으로 「몇 초 구간」이나 「어떤 부분」인지 알려주시면 "
        f"딱 맞는 연습법 드릴게요 😊"
    )


def _init_chat(session: dict[str, Any]) -> None:
    fp = _session_fingerprint(session)
    existing = st.session_state.get("coach_chat_messages") or []
    if st.session_state.get("coach_chat_fp") == fp and existing:
        return

    opening = session.get("gpt_text") or _rule_opening(session)
    suggestions = _rule_suggested_questions(session)

    st.session_state.coach_chat_fp = fp
    st.session_state.coach_chat_messages = [{"role": "assistant", "content": opening}]
    st.session_state.coach_suggested_questions = suggestions[:3]
    st.session_state.coach_chat_ready = True
    st.session_state.coach_gpt_enhanced = bool(session.get("gpt_text"))

    if session.get("gpt_text"):
        return

    try:
        import os

        if not os.environ.get("OPENAI_API_KEY"):
            return
        from gpt_coach import generate_coach_opening, generate_suggested_questions_gpt

        payload = _analysis_payload(session)
        with st.spinner("선생님이 코칭 메시지 작성 중…"):
            gpt_opening = generate_coach_opening(payload)
            if gpt_opening and gpt_opening.strip():
                st.session_state.coach_chat_messages[0]["content"] = gpt_opening.strip()
            gpt_qs = generate_suggested_questions_gpt(payload)
            if gpt_qs:
                st.session_state.coach_suggested_questions = gpt_qs[:3]
        st.session_state.coach_gpt_enhanced = True
    except Exception:
        pass


def _append_and_reply(session: dict[str, Any], user_text: str) -> None:
    messages: list[dict[str, str]] = st.session_state.coach_chat_messages
    messages.append({"role": "user", "content": user_text})

    payload = _analysis_payload(session)
    reply = ""
    try:
        from gpt_coach import generate_coach_chat_reply

        history = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]
        reply = generate_coach_chat_reply(payload, history, user_text)
    except Exception:
        reply = _rule_reply(session, user_text)

    messages.append({"role": "assistant", "content": reply})


def _render_result_hero(session: dict[str, Any]) -> None:
    """분석 완료 배너 — 점수 · 강점 · 다음 포커스."""
    from ui.auth import current_user

    report = session["report"]
    user = current_user()
    name = user.get("name", "학습자") if user else "학습자"
    stages = report.stages[:3]
    overall = report.overall_score

    s4 = next((s for s in report.stages if s.stage == 4), None)
    strengths = (s4.details.get("teacher_strengths") if s4 else None) or []
    strength_line = strengths[0] if strengths else "오늘도 연습하러 와 줘서 고마워요"

    weakest = min(stages, key=lambda s: s.score) if stages else None
    focus_line = ""
    if weakest:
        wlabel = STAGE_NAMES.get(weakest.stage, weakest.title)
        focus_line = f"다음 포커스 · {wlabel} {weakest.score:.0f}점"

    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D"
    grade_color = "#22c55e" if overall >= 85 else "#6366f1" if overall >= 70 else "#f59e0b"

    st.markdown(
        f"""
        <div class="vc-result-hero">
            <div class="vc-result-hero-glow"></div>
            <div class="vc-result-hero-inner">
                <div class="vc-result-hero-left">
                    <span class="vc-result-badge">레슨 완료 ✓</span>
                    <h2 class="vc-result-hero-title">{name}님, 수고했어요!</h2>
                    <p class="vc-result-hero-strength">🌟 {strength_line}</p>
                    <p class="vc-result-hero-focus">{focus_line}</p>
                </div>
                <div class="vc-result-hero-score">
                    <span class="vc-result-grade" style="color:{grade_color}">{grade}</span>
                    <span class="vc-result-overall">{overall:.0f}</span>
                    <span class="vc-result-overall-label">종합 점수</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_score_strip(session: dict[str, Any]) -> None:
    report = session["report"]
    chips = [
        f'<span class="vc-score-chip vc-score-overall">{report.overall_score:.0f}<small>종합</small></span>'
    ]
    for s in report.stages[:3]:
        label = STAGE_NAMES.get(s.stage, str(s.stage))
        chips.append(
            f'<span class="vc-score-chip">{s.score:.0f}<small>{label}</small></span>'
        )
    st.markdown(
        f'<div class="vc-score-strip">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


def render_coach_dm(session: dict[str, Any]) -> None:
    """분석 후 DM 코치 화면."""
    _init_chat(session)

    from ui.auth import current_user

    user = current_user()
    user_name = user.get("name", "나") if user else "나"

    _render_result_hero(session)
    _render_score_strip(session)

    st.markdown(
        """
        <div class="vc-dm-header">
            <div class="vc-dm-header-inner">
                <span class="vc-dm-avatar">🎤</span>
                <div>
                    <p class="vc-dm-title">보컬 코치 선생님</p>
                    <p class="vc-dm-status">● 코칭 대화 중</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    messages = st.session_state.get("coach_chat_messages") or []
    if not messages:
        st.session_state.coach_chat_messages = [
            {"role": "assistant", "content": _rule_opening(session)},
        ]
        messages = st.session_state.coach_chat_messages

    for msg in messages:
        role = msg["role"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="🎤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user", avatar="🙂"):
                st.markdown(msg["content"])

    suggestions = st.session_state.get("coach_suggested_questions") or []
    if suggestions:
        st.markdown('<p class="vc-dm-suggest-label">💬 이런 것도 물어보세요</p>', unsafe_allow_html=True)
        s_cols = st.columns(min(len(suggestions), 3))
        for i, q in enumerate(suggestions):
            with s_cols[i]:
                if st.button(q, key=f"coach_suggest_{i}", use_container_width=True):
                    _append_and_reply(session, q)
                    st.session_state.coach_suggested_questions = []
                    st.rerun()

    prompt = st.chat_input(f"{user_name}님, 궁금한 점을 입력하세요…", key="coach_chat_input")
    if prompt:
        _append_and_reply(session, prompt.strip())
        st.session_state.coach_suggested_questions = []
        st.rerun()

    with st.expander("📊 상세 분석 리포트 · 그래프 · 다운로드", expanded=False):
        from ui.components import render_session_results

        render_session_results(session)

    st.divider()
    from ui.analysis_settings import render_settings_open_button

    render_settings_open_button(key="btn_open_analysis_settings_results")
    if st.button("🎤 다른 곡 분석하기", use_container_width=True, key="btn_new_analysis"):
        for key in (
            "last_session",
            "last_log",
            "coach_chat_fp",
            "coach_chat_messages",
            "coach_suggested_questions",
            "coach_gpt_enhanced",
        ):
            st.session_state.pop(key, None)
        st.rerun()
