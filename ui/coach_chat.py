"""Instagram / 카카오톡 스타일 AI 보컬 코치 채팅."""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from typing import Any

import streamlit as st

from coaching_vocab import STAGE_NAMES
from ui.coach_insights import build_focus_items, build_strength_items
from ui.utils import render_safe_html
from ui.text_format import format_readable_paragraphs, normalize_markdown_noise


def _session_fingerprint(session: dict[str, Any]) -> str:
    report = session["report"]
    try:
        from ui.auth import current_user_id

        uid = current_user_id() or ""
    except Exception:
        uid = ""
    record = str(session.get("record_path") or session.get("record_id") or "")
    song = str(session.get("song_title") or "")
    blob = f"{uid}:{record}:{song}:{report.overall_score}:{len(report.stages)}"
    return hashlib.md5(blob.encode()).hexdigest()[:12]


def _analysis_payload(session: dict[str, Any]) -> dict[str, Any]:
    from analysis import report_to_coach_chat_payload

    return report_to_coach_chat_payload(session["report"])


def _md_to_html(text: str) -> str:
    esc = html.escape(text or "")
    esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
    return esc.replace("\n", "<br>")


def _sanitize_chat_content(text: str) -> str:
    """GPT·저장 메시지에 섞인 HTML 태그 제거 (말풍선 깨짐 방지)."""
    if not text:
        return ""
    cleaned = text.strip()
    if re.search(r"</?(div|span|p|br|html|body|del)\b", cleaned, re.I):
        cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.I)
        cleaned = re.sub(r"</?p>", "\n", cleaned, flags=re.I)
        cleaned = re.sub(r"</?del>", "", cleaned, flags=re.I)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return cleaned.strip()


def _normalize_chat_markdown(text: str) -> str:
    """마크다운 깨짐(취소선·구분선) 보정 + 읽기 쉬운 줄바꿈."""
    cleaned = _sanitize_chat_content(text)
    if not cleaned:
        return ""
    cleaned = normalize_markdown_noise(cleaned)
    return format_readable_paragraphs(cleaned)


def _rule_opening(session: dict[str, Any]) -> str:
    report = session["report"]
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
    weakest = min(stages, key=lambda s: s.score) if stages else None
    wlabel = STAGE_NAMES.get(weakest.stage, "음정") if weakest else "음정"

    lines = [
        f"{name}님, 분석을 마쳤습니다 🎤",
        "",
        f"**종합 {overall:.0f}점** — 오늘은 **{wlabel}**부터 같이 잡아볼까요?",
        "",
        "아래 버튼을 누르거나, 궁금한 걸 편하게 물어보세요.",
        "（긴 코칭은 버튼을 누를 때마다 이어서 알려드릴게요 😊）",
    ]
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
    if weakest.stage == 1:
        qs.append("이 구간만 집중해서 연습할래요")
    elif weakest.stage == 2:
        qs.append("박자 잡는 메트로놈 연습법")
    else:
        qs.append("호흡·목소리 톤 예쁘게 하는 법")

    devs = report.pitch_deviation_segments[:1]
    if devs:
        from coaching_vocab import time_range

        d = devs[0]
        if isinstance(d, (tuple, list)) and len(d) >= 2:
            qs.append(f"{time_range(float(d[0]), float(d[1]))}만 연습법")
        else:
            qs.append(f"{time_range(d.start_sec, d.end_sec)}만 연습법")
    else:
        qs.append("오늘 10분 루틴 짜 주세요")

    qs.append("잘한 점 더 칭찬해 주세요")
    return qs[:3]


_EXTRA_SUGGESTIONS = (
    "오늘 10분 루틴 짜 주세요",
    "점수를 더 올리려면 뭐부터 할까요?",
    "약한 영역만 0.5배속으로 연습하려면?",
    "복식호흡부터 할까요?",
    "고음 구간만 따로 연습법 알려주세요",
    "다음 녹음 전 체크리스트 3가지",
    "메트로놈 BPM은 몇부터 시작할까요?",
    "롱톤 연습 순서 알려주세요"
)


def _suggestion_pool(session: dict[str, Any]) -> list[str]:
    pool: list[str] = []
    seen: set[str] = set()
    for q in _rule_suggested_questions(session) + list(_EXTRA_SUGGESTIONS):
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            pool.append(q)
    return pool


def _rotate_suggestion(used: str, session: dict[str, Any]) -> None:
    """사용한 pill 제거 → 풀에서 새 질문으로 3개 유지."""
    used = used.strip()
    if not used:
        return
    used_list: list[str] = list(st.session_state.get("coach_used_suggestions") or [])
    if used not in used_list:
        used_list.append(used)
    st.session_state.coach_used_suggestions = used_list
    used_set = set(used_list)

    current = [q for q in (st.session_state.get("coach_suggested_questions") or []) if q.strip() != used]
    pool = _suggestion_pool(session)
    for q in pool:
        if len(current) >= 3:
            break
        if q not in used_set and q not in current:
            current.append(q)
    while len(current) < 3:
        added = False
        for q in pool:
            if q not in current:
                current.append(q)
                added = True
                break
        if not added:
            break
    st.session_state.coach_suggested_questions = current[:3]


def _pill_key(question: str) -> str:
    return hashlib.md5(question.encode()).hexdigest()[:10]


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


def _fetch_rag(user_text: str, session: dict[str, Any]) -> str:
    """RAG 검색 → GPT 프롬프트 블록 (UI에는 출처 미표시)."""
    try:
        from coach_rag import retrieve_for_coaching

        payload = _analysis_payload(session)
        bundle = retrieve_for_coaching(user_text, payload)
        return bundle.prompt_block
    except Exception:
        return ""


def _append_user_message(text: str) -> None:
    """사용자 메시지 추가."""
    normalized = _normalize_chat_markdown(text)
    if not normalized:
        return
    messages: list[dict[str, str]] = st.session_state.coach_chat_messages
    messages.append({"role": "user", "content": normalized})


def _on_pill_click(question: str) -> None:
    st.session_state["coach_pending_message"] = question


def _stream_request_id(messages: list[dict[str, str]]) -> str:
    """사용자 메시지 1건당 고유 ID — 중복 API 호출 방지."""
    if not messages or messages[-1].get("role") != "user":
        return ""
    fp = str(st.session_state.get("coach_chat_fp") or "")
    last_user = messages[-1].get("content") or ""
    blob = f"{fp}:{len(messages)}:{last_user}"
    return hashlib.md5(blob.encode()).hexdigest()[:16]


def _has_openai_key() -> bool:
    import os

    return bool(os.environ.get("OPENAI_API_KEY"))


def _maybe_fetch_gpt_suggestions(session: dict[str, Any]) -> None:
    if st.session_state.get("coach_gpt_suggestions_done"):
        return
    st.session_state.coach_gpt_suggestions_done = True
    if not _has_openai_key():
        return
    try:
        from gpt_coach import generate_suggested_questions_gpt

        payload = _analysis_payload(session)
        gpt_qs = generate_suggested_questions_gpt(payload)
        if gpt_qs:
            st.session_state.coach_suggested_questions = gpt_qs[:3]
    except Exception:
        pass


def _run_stream(gen_func):
    """st.write_stream + 구버전 Streamlit 폴백."""
    if hasattr(st, "write_stream"):
        try:
            return st.write_stream(gen_func)
        except Exception:
            pass
    text = "".join(gen_func())
    if text:
        render_safe_html(text)
    return text


def _stream_opening_safe(session: dict[str, Any]) -> str:
    """첫 DM — st.write_stream + 실패 시 규칙 기반 폴백."""

    def _gen():
        rule = _rule_opening(session)
        if not _has_openai_key():
            yield rule
            return
        try:
            from gpt_coach import stream_coach_opening

            payload = _analysis_payload(session)
            rag_block = _fetch_rag("분석 직후 첫 코칭", session)
            got = False
            for chunk in stream_coach_opening(payload, rag_block=rag_block or None):
                got = True
                yield chunk
            if not got:
                yield rule
        except Exception:
            yield rule

    return _run_stream(_gen)


def _stream_reply_safe(session: dict[str, Any]) -> str:
    """후속 DM — st.write_stream + 실패 시 규칙 기반 폴백."""
    messages: list[dict[str, str]] = st.session_state.coach_chat_messages
    user_text = messages[-1]["content"] if messages else ""

    def _gen():
        fallback = _rule_reply(session, user_text)
        if not _has_openai_key():
            yield fallback
            return
        try:
            from gpt_coach import stream_coach_chat_reply

            payload = _analysis_payload(session)
            rag_block = _fetch_rag(user_text, session)
            history = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]
            got = False
            for chunk in stream_coach_chat_reply(
                payload, history, user_text, rag_block=rag_block or None
            ):
                got = True
                yield chunk
            if not got:
                yield fallback
        except Exception:
            yield fallback

    return _run_stream(_gen)


def _append_rule_reply(session: dict[str, Any]) -> None:
    """중단·중복 rerun 시 API 재호출 없이 규칙 답변."""
    messages: list[dict[str, str]] = list(st.session_state.coach_chat_messages or [])
    if not messages or messages[-1].get("role") != "user":
        return
    rid = _stream_request_id(messages)
    user_text = messages[-1]["content"]
    messages.append(
        {"role": "assistant", "content": _normalize_chat_markdown(_rule_reply(session, user_text))}
    )
    st.session_state.coach_chat_messages = messages
    st.session_state["coach_stream_completed_id"] = rid
    st.session_state.pop("coach_stream_inflight_id", None)
    if not st.session_state.get("coach_suggested_questions"):
        st.session_state.coach_suggested_questions = _rule_suggested_questions(session)[:3]
    st.session_state["coach_scroll_tick"] = int(st.session_state.get("coach_scroll_tick") or 0) + 1


def _append_assistant_reply(session: dict[str, Any], raw_text: str, *, request_id: str) -> None:
    normalized = _normalize_chat_markdown(raw_text or "")
    if not normalized:
        _append_rule_reply(session)
        return
    messages: list[dict[str, str]] = list(st.session_state.coach_chat_messages or [])
    messages.append({"role": "assistant", "content": normalized})
    st.session_state.coach_chat_messages = messages
    st.session_state["coach_stream_completed_id"] = request_id
    st.session_state.pop("coach_stream_inflight_id", None)
    if not st.session_state.get("coach_suggested_questions"):
        st.session_state.coach_suggested_questions = _rule_suggested_questions(session)[:3]
    st.session_state["coach_scroll_tick"] = int(st.session_state.get("coach_scroll_tick") or 0) + 1


def _generate_reply(session: dict[str, Any]) -> str:
    messages: list[dict[str, str]] = st.session_state.coach_chat_messages
    user_text = messages[-1]["content"] if messages else ""
    rag_block = _fetch_rag(user_text, session)
    try:
        from gpt_coach import generate_coach_chat_reply

        payload = _analysis_payload(session)
        history = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]
        reply = generate_coach_chat_reply(
            payload, history, user_text, rag_block=rag_block or None
        )
        if reply and reply.strip():
            return reply.strip()
    except Exception:
        pass
    return _rule_reply(session, user_text)


def _opening_is_rich(text: str) -> bool:
    """GPT 첫 메시지가 DM 형식(섹션·분량)을 갖췄는지."""
    t = text or ""
    has_sections = "🌟" in t and ("🎯" in t or "잘한" in t) and ("📋" in t or "루틴" in t)
    return has_sections and len(t) >= 280


def _mark_chat_scroll() -> None:
    st.session_state["coach_scroll_tick"] = int(st.session_state.get("coach_scroll_tick") or 0) + 1


def _maybe_scroll_chat() -> None:
    tick = int(st.session_state.get("coach_scroll_tick") or 0)
    applied = int(st.session_state.get("coach_scroll_applied_tick") or -1)
    if tick == applied:
        return
    from ui.chat_scroll import scroll_chat_to_bottom

    scroll_chat_to_bottom(force=True)
    st.session_state["coach_scroll_applied_tick"] = tick


def _init_chat(session: dict[str, Any]) -> None:
    fp = _session_fingerprint(session)
    existing = st.session_state.get("coach_chat_messages") or []
    if st.session_state.get("coach_chat_fp") == fp and existing:
        for msg in existing:
            msg["content"] = _normalize_chat_markdown(msg.get("content", ""))
        st.session_state.coach_chat_messages = existing
        return

    rule_opening = _rule_opening(session)
    suggestions = _rule_suggested_questions(session)

    st.session_state.coach_chat_fp = fp
    st.session_state.coach_chat_messages = [
        {"role": "assistant", "content": _normalize_chat_markdown(rule_opening)}
    ]
    st.session_state.coach_suggested_questions = suggestions[:3]
    st.session_state.coach_used_suggestions = []
    st.session_state.coach_chat_ready = True
    st.session_state.coach_gpt_enhanced = False
    st.session_state.coach_gpt_suggestions_done = False
    st.session_state.pop("coach_stream_completed_id", None)
    st.session_state.pop("coach_stream_inflight_id", None)
    st.session_state["coach_opening_stream"] = _has_openai_key()
    _mark_chat_scroll()


def _render_result_hero(session: dict[str, Any]) -> None:
    from coaching_vocab import derive_vocal_title
    from ui.auth import current_user

    report = session["report"]
    full_record = session.get("full_record") or {}
    user = current_user()
    name = user.get("name", "학습자") if user else "학습자"
    overall = report.overall_score
    vocal_title = full_record.get("vocal_title") or derive_vocal_title(report.stages)

    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D"
    grade_color = "#22c55e" if overall >= 85 else "#6366f1" if overall >= 70 else "#b45309"

    render_safe_html(
        f"""\
<div class="vc-result-hero">
<div class="vc-result-hero-glow"></div>
<div class="vc-result-hero-inner">
<div class="vc-result-hero-left">
<span class="vc-result-badge">레슨 완료 ✓</span>
<p class="vc-vocal-mbti-badge">👑 당신의 보컬 타입: {html.escape(vocal_title)}</p>
<h2 class="vc-result-hero-title">{html.escape(name)}님, 수고했어요!</h2>
<p class="vc-result-hero-focus">위 <b>탭</b>으로 진단서를 확인하고, 아래 AI 코치와 대화하세요</p>
</div>
<div class="vc-result-hero-score">
<span class="vc-result-grade" style="color:{grade_color}">{grade}</span>
<span class="vc-result-overall">{overall:.0f}</span>
<span class="vc-result-overall-label">종합 점수</span>
</div>
</div>
</div>"""
    )


def _render_recording_player(session: dict[str, Any]) -> None:
    """분석된 녹음 — 차트·코칭과 함께 바로 들어보기."""
    audio_path = session.get("audio_path")
    if not audio_path or not Path(audio_path).exists():
        return
    st.markdown(
        '<p class="vc-audio-player-label">🎧 내가 부른 녹음 · 아래 코칭의 ⏱ 구간으로 이동해 들어보세요</p>'
    )
    st.markdown('<div class="vc-audio-player-wrap">')
    st.audio(str(audio_path))
    render_safe_html("</div>")


def _render_score_strip(session: dict[str, Any]) -> None:
    report = session["report"]
    chips = [
        f'<span class="vc-score-chip vc-score-overall">{report.overall_score:.0f}<small>종합</small></span>'
    ]
    for s in report.stages[:3]:
        label = STAGE_NAMES.get(s.stage, str(s.stage))
        chips.append(
            f'<span class="vc-score-chip">{s.score:.0f}<small>{html.escape(label)}</small></span>'
        )
    render_safe_html(f'<div class="vc-score-strip">{"".join(chips)}</div>'
    )


def _render_chat_message(msg: dict[str, str]) -> None:
    content = _normalize_chat_markdown(msg.get("content", ""))
    if not content:
        return
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🎤"):
            st.markdown(content)
    else:
        with st.chat_message("user", avatar="🙂"):
            st.markdown(content)


def _render_dm_thread(
    messages: list[dict[str, str]],
    session: dict[str, Any],
    *,
    stream_opening: bool = False,
    stream_reply_id: str = ""
) -> None:
    """Streamlit chat_message — 스트리밍·일반 렌더."""
    if stream_opening:
        if st.session_state.get("coach_gpt_enhanced"):
            st.session_state["coach_opening_stream"] = False
            for msg in messages:
                _render_chat_message(msg)
            return
        if st.session_state.get("coach_opening_inflight"):
            with st.chat_message("assistant", avatar="🎤"):
                st.caption("코칭 메시지 준비 중…")
            return
        st.session_state["coach_opening_inflight"] = True
        try:
            with st.chat_message("assistant", avatar="🎤"):
                full_text = _stream_opening_safe(session)
            messages = list(st.session_state.get("coach_chat_messages") or messages)
            if full_text and full_text.strip() and _opening_is_rich(full_text):
                messages[0]["content"] = _normalize_chat_markdown(full_text.strip())
                st.session_state.coach_gpt_enhanced = True
            elif messages:
                messages[0]["content"] = _normalize_chat_markdown(
                    messages[0].get("content") or _rule_opening(session)
                )
            st.session_state.coach_chat_messages = messages
            st.session_state["coach_opening_stream"] = False
            _maybe_fetch_gpt_suggestions(session)
            _mark_chat_scroll()
        finally:
            st.session_state.pop("coach_opening_inflight", None)
        return

    completed_id = str(st.session_state.get("coach_stream_completed_id") or "")
    need_reply = bool(
        stream_reply_id
        and messages
        and messages[-1].get("role") == "user"
        and stream_reply_id != completed_id
    )

    render_upto = len(messages) - 1 if need_reply else len(messages)
    for msg in messages[:render_upto]:
        _render_chat_message(msg)

    if not need_reply:
        return

    _render_chat_message(messages[-1])

    inflight = str(st.session_state.get("coach_stream_inflight_id") or "")
    live_messages = list(st.session_state.get("coach_chat_messages") or messages)
    if inflight == stream_reply_id:
        if live_messages and live_messages[-1].get("role") == "assistant":
            st.session_state["coach_stream_completed_id"] = stream_reply_id
            st.session_state.pop("coach_stream_inflight_id", None)
            _render_chat_message(live_messages[-1])
        else:
            with st.chat_message("assistant", avatar="🎤"):
                st.caption("답변 준비 중…")
        return

    if live_messages and live_messages[-1].get("role") == "assistant":
        st.session_state["coach_stream_completed_id"] = stream_reply_id
        return

    st.session_state["coach_stream_inflight_id"] = stream_reply_id
    try:
        with st.chat_message("assistant", avatar="🎤"):
            full_text = _stream_reply_safe(session)
        _append_assistant_reply(session, full_text, request_id=stream_reply_id)
    except Exception:
        st.session_state.pop("coach_stream_inflight_id", None)
        _append_rule_reply(session)
        _render_chat_message(st.session_state.coach_chat_messages[-1])


def _pill_label(q: str) -> str:
    q = q.strip()
    if len(q) <= 18:
        return q
    return q[:17] + "…"


def _render_dm_composer(session: dict[str, Any], user_name: str, *, disabled: bool) -> None:
    """Gemini 스타일 — 추천 pill + 하단 chat_input."""
    suggestions = st.session_state.get("coach_suggested_questions") or []

    st.markdown('<div class="vc-dm-composer">')

    if suggestions and not disabled:
        render_safe_html('<div class="vc-dm-pill-row">')
        for q in suggestions[:3]:
            st.button(
                f"+ {_pill_label(q)}",
                key=f"coach_pill_{_pill_key(q)}",
                use_container_width=False,
                on_click=_on_pill_click,
                args=(q,)
            )
        render_safe_html("</div>")

    prompt = st.chat_input(
        "보컬 코치에게 물어보기",
        key="coach_chat_input",
        disabled=disabled
    )
    if prompt and prompt.strip():
        st.session_state["coach_pending_message"] = prompt.strip()
        st.rerun(scope="fragment")

    render_safe_html("</div>")


def _render_dm_panel(
    session: dict[str, Any],
    user_name: str,
    messages: list[dict[str, str]],
    *,
    stream_opening: bool = False,
    stream_reply_id: str = ""
) -> None:
    with st.container(key="vc_dm_panel"):
        render_safe_html("""
            <div class="vc-dm-header vc-dm-header-attached">
                <div class="vc-dm-header-inner">
                    <span class="vc-dm-avatar">🎤</span>
                    <div>
                        <p class="vc-dm-title">보컬 코치 선생님</p>
                        <p class="vc-dm-status">● 코칭 대화 중</p>
                    </div>
                </div>
            </div>
            """
        )
        with st.container(key="vc_dm_thread"):
            _render_dm_thread(
                messages,
                session,
                stream_opening=stream_opening,
                stream_reply_id=stream_reply_id
            )
        messages_after = list(st.session_state.get("coach_chat_messages") or messages)
        still_opening = bool(
            st.session_state.get("coach_opening_stream")
            and not st.session_state.get("coach_gpt_enhanced")
        )
        reply_after = _stream_request_id(messages_after)
        completed = str(st.session_state.get("coach_stream_completed_id") or "")
        still_reply = bool(reply_after and reply_after != completed)
        _render_dm_composer(
            session,
            user_name,
            disabled=still_opening or still_reply
        )


@st.fragment
def _coach_chat_fragment(session: dict[str, Any], user_name: str) -> None:
    """채팅 fragment — 스트리밍 응답 · 중복 API 호출 방지."""
    _init_chat(session)

    pending = st.session_state.pop("coach_pending_message", None)
    if pending:
        _append_user_message(pending)
        _rotate_suggestion(pending, session)
        st.session_state.pop("coach_stream_completed_id", None)
        st.session_state.pop("coach_stream_inflight_id", None)
        st.session_state["coach_scroll_tick"] = int(st.session_state.get("coach_scroll_tick") or 0) + 1

    messages = list(st.session_state.get("coach_chat_messages") or [])
    stream_opening = bool(
        st.session_state.get("coach_opening_stream") and not st.session_state.get("coach_gpt_enhanced")
    )
    reply_id = _stream_request_id(messages)
    need_reply = bool(
        reply_id and reply_id != str(st.session_state.get("coach_stream_completed_id") or "")
    )

    _render_dm_panel(
        session,
        user_name,
        messages,
        stream_opening=stream_opening,
        stream_reply_id=reply_id if need_reply else ""
    )

    _maybe_scroll_chat()


def render_coach_dm(session: dict[str, Any]) -> None:
    """분석 후 DM 코치 + 리포트."""
    from ui.analysis_overlay import clear_analyze_stage
    from ui.loading import clear_loading

    clear_analyze_stage()
    clear_loading()

    from ui.auth import current_user

    user = current_user()
    user_name = user.get("name", "나") if user else "나"

    st.markdown('<div id="vc-result-top"></div>')
    render_safe_html('<script>document.body.classList.add("vc-show-result");</script>')

    render_safe_html('<div class="vc-result-shell vc-layout-bound">')
    _render_result_hero(session)
    _render_recording_player(session)
    _render_score_strip(session)
    render_safe_html("</div>")

    from ui.components import render_session_results

    render_session_results(session)

    from ui.chat_scroll import install_chat_auto_scroll

    install_chat_auto_scroll()

    _coach_chat_fragment(session, user_name)

    st.divider()
    if st.button("💬 피드백 남기기", use_container_width=True, key="btn_coach_feedback"):
        from ui.navigation import go_to

        go_to("피드백")
    if st.button("🎤 다른 곡 분석하기", use_container_width=True, key="btn_new_analysis"):
        from ui.session_reset import reset_user_session_state

        reset_user_session_state()
        st.rerun()
