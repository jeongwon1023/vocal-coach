"""관리자 — 에러 히스토리 · 시스템 상태."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from ui.admin_auth import (
    admin_secret_configured,
    authenticate_admin,
    is_admin_authenticated,
    logout_admin,
)
from ui.error_guard import (
    clear_error_logs,
    error_log_stats,
    get_error_logs,
    get_system_health,
    run_preflight,
    verify_system_health,
)
from ui.utils import render_safe_html


def render_admin_page() -> None:
    render_safe_html(
        """
        <div class="vc-page-head">
            <h2 class="vc-page-title">🛡️ 관리자 · 에러 히스토리</h2>
            <p class="vc-page-desc">서비스 에러 로그와 Pre-flight 상태를 확인합니다.</p>
        </div>
        """
    )

    if not admin_secret_configured():
        st.warning(
            "관리자 접근 키가 설정되지 않았습니다. "
            "`.streamlit/secrets.toml` 또는 Streamlit Cloud Secrets에 "
            "**ADMIN_SECRET** 을 추가하세요."
        )
        st.code("ADMIN_SECRET = \"긴-랜덤-문자열\"", language="toml")
        return

    if not is_admin_authenticated():
        _render_admin_login()
        return

    _render_admin_toolbar()
    _render_qa_panel()
    _render_health_panel()
    _render_error_dashboard()


def _render_admin_login() -> None:
    with st.form("admin_login_form", clear_on_submit=False):
        st.caption("관리자 비밀번호 (ADMIN_SECRET)")
        token = st.text_input("비밀번호", type="password", label_visibility="collapsed")
        if st.form_submit_button("로그인", type="primary", use_container_width=True):
            if authenticate_admin(token):
                st.session_state.nav_page = "관리자"
                st.rerun()
            st.error("비밀번호가 올바르지 않습니다.")


def _render_admin_toolbar() -> None:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.caption("접속 URL: `?admin_token=ADMIN_SECRET` 으로 바로 진입 가능")
    with col2:
        if st.button("🤖 AI 자가 테스트", use_container_width=True):
            st.session_state["_admin_qa_run"] = True
            st.rerun()
    with col3:
        if st.button("🔄 Pre-flight 재검사", use_container_width=True):
            st.session_state.pop("system_health", None)
            run_preflight()
            st.rerun()
    with col4:
        if st.button("로그아웃", use_container_width=True):
            logout_admin()
            st.session_state.nav_page = "홈"
            st.rerun()


def _render_qa_panel() -> None:
    if not st.session_state.pop("_admin_qa_run", False):
        cached = st.session_state.get("_admin_qa_results")
        if not cached:
            return
        _display_qa_results(cached)
        return

    with st.spinner("AI 자가 테스트 실행 중…"):
        from test_app import log_qa_failures, qa_summary, run_app_qa

        results = run_app_qa()
        log_qa_failures(results)
        st.session_state["_admin_qa_results"] = results
    st.rerun()


def _display_qa_results(results: list[dict[str, Any]]) -> None:
    from test_app import qa_summary

    ok, label = qa_summary(results)
    color = "#22c55e" if ok and label.startswith("이상") else "#ef4444"
    if "Yellow" in label:
        color = "#f59e0b"
    st.subheader("AI 자가 테스트 결과")
    st.markdown(f"**종합:** <span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
    rows = [
        {
            "단계": r.get("step", "—"),
            "상태": {"pass": "✅ Pass", "fail": "❌ Fail", "warn": "⚠️ Warn"}.get(
                r.get("status", ""), r.get("status")
            ),
            "상세": r.get("detail", ""),
        }
        for r in results
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_health_panel() -> None:
    from auth_service import kakao_redirect_uri

    health = get_system_health()
    login_ok = health.get("login_ok", False)
    st.subheader("시스템 상태")

    c1, c2, c3 = st.columns(3)
    c1.metric("로그인 가능", "✅ 정상" if login_ok else "⛔ 점검 중")
    c2.metric("검사 시각", str(health.get("checked_at", "—"))[-8:] or "—")
    c3.metric("체크 항목", len(health.get("checks") or {}))

    if health.get("messages"):
        st.warning(" · ".join(health["messages"]))

    with st.expander("Pre-flight 상세", expanded=not login_ok):
        st.json(health)

        st.markdown("**카카오 Redirect URI (KOE006 시 콘솔에 등록)**")
        st.code(kakao_redirect_uri(), language=None)

        if st.button("즉시 전체 재진단 (네트워크 포함)"):
            st.session_state.system_health = verify_system_health()
            st.rerun()


def _render_error_dashboard() -> None:
    logs = get_error_logs()
    stats = error_log_stats(logs)

    st.subheader("에러 히스토리")
    m1, m2, m3 = st.columns(3)
    m1.metric("총 에러", stats["total"])
    m2.metric("소스 종류", len(stats["by_source"]))
    m3.metric("최근 발생", _short_time(stats.get("latest_at")))

    if stats["by_source"]:
        st.caption("소스별 건수")
        cols = st.columns(min(4, len(stats["by_source"])))
        for idx, (source, count) in enumerate(stats["by_source"].items()):
            cols[idx % len(cols)].metric(source, count)

    sources = sorted({str(e.get("source") or "unknown") for e in logs})
    filter_col, action_col1, action_col2 = st.columns([2, 1, 1])
    with filter_col:
        selected = st.selectbox(
            "소스 필터",
            options=["전체"] + sources,
            index=0,
            label_visibility="collapsed",
        )
    with action_col1:
        payload = json.dumps(logs, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 JSON 내보내기",
            data=payload,
            file_name="error_logs.json",
            mime="application/json",
            use_container_width=True,
        )
    with action_col2:
        if st.button("🗑️ 로그 비우기", use_container_width=True):
            st.session_state["_admin_clear_confirm"] = True

    if st.session_state.pop("_admin_clear_confirm", False):
        _confirm_clear_logs()

    filtered = logs if selected == "전체" else [e for e in logs if e.get("source") == selected]
    if not filtered:
        st.info("기록된 에러가 없습니다.")
        return

    for idx, entry in enumerate(filtered):
        _render_error_entry(entry, idx)


def _confirm_clear_logs() -> None:
    st.warning("세션 + 디스크에 저장된 에러 로그를 모두 삭제합니다.")
    c1, c2 = st.columns(2)
    if c1.button("삭제 확인", type="primary"):
        clear_error_logs(clear_persisted=True)
        st.success("에러 로그를 비웠습니다.")
        st.rerun()
    if c2.button("취소"):
        pass


def _render_error_entry(entry: dict[str, Any], idx: int) -> None:
    at = entry.get("at", "—")
    source = entry.get("source", "unknown")
    message = entry.get("message", "(메시지 없음)")
    title = f"{_short_time(at)} · {source} · {message[:80]}"
    with st.expander(title, expanded=idx == 0):
        st.markdown(f"**시각:** {at}")
        st.markdown(f"**소스:** `{source}`")
        st.markdown(f"**메시지:** {message}")
        extra = entry.get("extra") or {}
        if extra:
            st.markdown("**추가 정보**")
            st.json(extra)
        detail = entry.get("detail") or ""
        if detail:
            st.markdown("**상세 로그**")
            st.code(detail)


def _short_time(iso: str | None) -> str:
    if not iso:
        return "—"
    if "T" in iso:
        return iso.replace("T", " ")[:16]
    return iso[:16]
