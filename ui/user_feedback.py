"""베타 피드백 — 사용자 의견 수집."""

from __future__ import annotations

import streamlit as st

from ui.navigation import current_page, go_to


def render_feedback_page() -> None:
    from feedback_store import feedback_stats, list_beta_feedback, save_beta_feedback
    from ui.auth import current_user, current_user_id, is_logged_in

    st.markdown(
        """
        <div class="vc-page-head">
            <h2 class="vc-page-title">💬 베타 피드백</h2>
            <p class="vc-page-desc">써 보시고 느낀 점을 알려 주세요. Vocal Coach AI를 함께 만들어 가요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats = feedback_stats()
    st.markdown(
        f"""
        <div class="vc-feedback-stats">
            <span class="vc-feedback-stat">📝 누적 {stats.get('beta', 0)}건</span>
            <span class="vc-feedback-stat">🙏 여러분 의견이 우선순위를 정해요</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("feedback_sent"):
        st.success("소중한 피드백 감사합니다! 더 나은 레슨실로 만들게요 🎤")
        if st.button("다른 의견 보내기", key="feedback_again"):
            st.session_state.pop("feedback_sent", None)
            st.rerun()
        _render_recent(list_beta_feedback(limit=5))
        return

    user = current_user() if is_logged_in() else None
    category = st.selectbox(
        "어떤 종류인가요?",
        options=["버그 / 오류", "분석 품질", "디자인 · UX", "기능 제안", "기타"],
        key="feedback_category",
    )
    rating = st.slider("전체 만족도 (1~5)", min_value=1, max_value=5, value=4, key="feedback_rating")
    message = st.text_area(
        "자유롭게 적어 주세요",
        placeholder="예: 모바일에서 분석 버튼이 잘 안 눌려요 / DM 코치가 좋았어요 / 이런 기능 있으면 좋겠어요",
        height=140,
        key="feedback_message",
    )
    contact = st.text_input(
        "연락처 (선택 · 답변 받고 싶을 때)",
        placeholder="이메일 또는 카카오 ID",
        key="feedback_contact",
    )

    if not is_logged_in():
        st.caption("로그인 없이도 보낼 수 있어요. 체험 계정으로 로그인하면 기록과 함께 저장됩니다.")

    if st.button("피드백 보내기", type="primary", use_container_width=True, key="feedback_submit"):
        if not (message or "").strip():
            st.warning("내용을 한 줄이라도 적어 주세요.")
        else:
            save_beta_feedback(
                message=message.strip(),
                category=category,
                rating=rating,
                user_id=current_user_id(),
                user_name=user.get("name") if user else None,
                page=current_page(),
                contact=contact.strip() or None,
            )
            st.session_state["feedback_sent"] = True
            st.rerun()

    st.divider()
    _render_recent(list_beta_feedback(limit=5))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎤 분석하러 가기", use_container_width=True, key="fb_go_analysis"):
            go_to("마이 페이지")
    with c2:
        if st.button("📈 마이 페이지", use_container_width=True, key="fb_go_mypage"):
            go_to("마이 페이지")


def _render_recent(items: list[dict]) -> None:
    if not items:
        return
    st.markdown("##### 최근 베타 의견 (익명 요약)")
    for item in items[:5]:
        cat = item.get("category", "기타")
        rating = item.get("rating")
        msg = (item.get("message") or "")[:120]
        stars = f"★ {rating}/5" if rating else ""
        st.markdown(
            f"""
            <div class="vc-feedback-card">
                <p class="vc-feedback-card-meta">{cat} · {stars}</p>
                <p class="vc-feedback-card-msg">{msg}{"…" if len(item.get("message") or "") > 120 else ""}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
