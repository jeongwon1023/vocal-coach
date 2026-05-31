"""전역 에러 가드 · 자가 진단 · HTTP 재시도."""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_fixed

MAX_ERROR_LOGS = 50
MAX_PERSISTED_ERRORS = 200
_ERROR_LOG_PATH = Path(__file__).resolve().parent.parent / "records" / "errors" / "error_log.jsonl"


def oauth_callback_active() -> bool:
    """카카오 OAuth code 콜백 중 — 재시도 토스트·Pre-flight ping 억제."""
    if st.session_state.get("_oauth_in_progress"):
        return True
    try:
        code = st.query_params.get("code")
        if isinstance(code, list):
            code = code[0] if code else None
        if code:
            return True
    except Exception:
        pass
    return False


def clear_retry_ui_state() -> None:
    st.session_state.pop("_retry_in_progress", None)
    st.session_state.pop("_retry_attempt", None)


def _on_retry(retry_state: Any) -> None:
    if oauth_callback_active():
        return
    init_error_guard()
    st.session_state["_retry_in_progress"] = True
    st.session_state["_retry_attempt"] = retry_state.attempt_number


_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    reraise=True,
    before_sleep=_on_retry,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def init_error_guard() -> None:
    if "error_logs" not in st.session_state:
        st.session_state.error_logs = []
    if "_error_dialog_pending" not in st.session_state:
        st.session_state._error_dialog_pending = False
    if "_error_dialog_detail" not in st.session_state:
        st.session_state._error_dialog_detail = ""


def log_error(
    message: str,
    *,
    source: str = "app",
    exc: BaseException | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """에러 히스토리 누적 (관리자 분석용)."""
    init_error_guard()
    detail = str(exc) if exc else message
    if exc:
        detail = f"{message}\n{traceback.format_exc()}"

    entry = {
        "at": _now_iso(),
        "source": source,
        "message": message,
        "detail": detail,
        "extra": extra or {},
    }
    logs: list[dict[str, Any]] = st.session_state.error_logs
    logs.append(entry)
    st.session_state.error_logs = logs[-MAX_ERROR_LOGS:]
    _persist_error_entry(entry)


def _persist_error_entry(entry: dict[str, Any]) -> None:
    try:
        _ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _ERROR_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _trim_persisted_errors()
    except Exception:
        pass


def _trim_persisted_errors() -> None:
    if not _ERROR_LOG_PATH.exists():
        return
    try:
        lines = _ERROR_LOG_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) <= MAX_PERSISTED_ERRORS:
            return
        _ERROR_LOG_PATH.write_text(
            "\n".join(lines[-MAX_PERSISTED_ERRORS:]) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def _load_persisted_errors() -> list[dict[str, Any]]:
    if not _ERROR_LOG_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        for line in _ERROR_LOG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    except Exception:
        pass
    return entries


def get_error_logs(*, include_persisted: bool = True) -> list[dict[str, Any]]:
    """세션 + 디스크 에러 로그 (최신순)."""
    init_error_guard()
    merged: dict[str, dict[str, Any]] = {}
    if include_persisted:
        for entry in _load_persisted_errors():
            merged[_error_entry_key(entry)] = entry
    for entry in st.session_state.error_logs:
        merged[_error_entry_key(entry)] = entry
    logs = list(merged.values())
    logs.sort(key=lambda e: e.get("at", ""), reverse=True)
    return logs


def _error_entry_key(entry: dict[str, Any]) -> str:
    return f"{entry.get('at', '')}|{entry.get('source', '')}|{entry.get('message', '')}"


def clear_error_logs(*, clear_persisted: bool = False) -> None:
    init_error_guard()
    st.session_state.error_logs = []
    if clear_persisted and _ERROR_LOG_PATH.exists():
        try:
            _ERROR_LOG_PATH.unlink()
        except Exception:
            pass


def error_log_stats(logs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    logs = logs if logs is not None else get_error_logs()
    by_source: dict[str, int] = {}
    for entry in logs:
        source = str(entry.get("source") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
    return {
        "total": len(logs),
        "by_source": dict(sorted(by_source.items(), key=lambda x: (-x[1], x[0]))),
        "latest_at": logs[0].get("at") if logs else None,
    }


def queue_error_dialog(detail: str, *, source: str = "app") -> None:
    init_error_guard()
    st.session_state._error_dialog_pending = True
    st.session_state._error_dialog_detail = detail
    log_error("사용자-facing 에러 다이얼로그 표시", source=source, extra={"detail": detail[:500]})


def render_retry_indicator() -> None:
    """Discord-style 재연결 안내."""
    if oauth_callback_active():
        clear_retry_ui_state()
        return
    if not st.session_state.pop("_retry_in_progress", False):
        return
    attempt = int(st.session_state.pop("_retry_attempt", 1))
    st.toast(f"서버와 다시 연결 중입니다… ({attempt}/3)", icon="🔄")
    st.progress(min(attempt / 3, 1.0), text="네트워크 재시도 중…")


@st.dialog("앗, 서버와 연결이 끊어졌어요", width="small")
def _server_status_dialog() -> None:
    detail = st.session_state.get("_error_dialog_detail", "")
    st.markdown("### 🚨 잠시만요")
    st.markdown(
        "현재 **네트워크 지연**이 발생했습니다.\n\n"
        "**10초 뒤** 다시 시도해 주세요. "
        "문제가 계속되면 **체험 계정**으로 이용할 수 있습니다."
    )
    with st.expander("개발자용 에러 상세 로그 보기"):
        st.code(detail or "(상세 정보 없음)")


def render_error_dialog_if_needed() -> None:
    if st.session_state.get("_error_dialog_pending"):
        st.session_state._error_dialog_pending = False
        _server_status_dialog()


def handle_global_exception(exc: BaseException, *, source: str = "app.main") -> None:
    detail = traceback.format_exc()
    log_error(str(exc), source=source, exc=exc)
    queue_error_dialog(detail, source=source)
    try:
        _server_status_dialog()
    except Exception:
        st.warning("현재 일시적인 네트워크 지연이 발생했습니다. 잠시 후 다시 시도해 주세요.")
        with st.expander("상세 로그 보기"):
            st.code(detail)


@_RETRY
def httpx_get_with_retry(url: str, **kwargs: Any) -> httpx.Response:
    resp = httpx.get(url, **kwargs)
    resp.raise_for_status()
    return resp


@_RETRY
def httpx_post_with_retry(url: str, **kwargs: Any) -> httpx.Response:
    resp = httpx.post(url, **kwargs)
    resp.raise_for_status()
    return resp


def httpx_get_once(url: str, **kwargs: Any) -> httpx.Response:
    """Pre-flight · OAuth — 재시도 UI 없이 1회 요청."""
    resp = httpx.get(url, **kwargs)
    resp.raise_for_status()
    return resp


def httpx_post_once(url: str, **kwargs: Any) -> httpx.Response:
    resp = httpx.post(url, **kwargs)
    resp.raise_for_status()
    return resp


def _secret_or_env(name: str) -> str | None:
    import os

    try:
        if name in st.secrets:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass
    value = os.environ.get(name, "").strip()
    return value or None


def verify_system_health() -> dict[str, Any]:
    """Pre-flight — Secrets · Supabase · 카카오 설정 자가 진단."""
    from ui.supabase_client import is_supabase_key_format

    checks: dict[str, bool] = {}
    messages: list[str] = []

    kakao_key = _secret_or_env("KAKAO_REST_API_KEY") or ""
    kakao_direct = bool(kakao_key and len(kakao_key) >= 20 and not kakao_key.startswith("your-"))
    supabase_url = _secret_or_env("SUPABASE_URL")
    supabase_key = _secret_or_env("SUPABASE_KEY") or ""
    supabase_ready = bool(
        supabase_url and supabase_key and is_supabase_key_format(supabase_key)
    )

    streamlit_url = _secret_or_env("STREAMLIT_URL")
    checks["streamlit_url"] = bool(streamlit_url)
    if not streamlit_url:
        messages.append("STREAMLIT_URL 미설정")

    checks["kakao_rest_api_key"] = kakao_direct
    if not kakao_direct and (kakao_key or supabase_ready):
        if kakao_key and not checks["kakao_rest_api_key"]:
            messages.append("KAKAO_REST_API_KEY 형식 오류")

    if supabase_ready:
        checks["supabase_secrets"] = True
        try:
            httpx_get_once(
                f"{supabase_url.rstrip('/')}/auth/v1/settings",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                },
                timeout=10,
            )
            checks["supabase_ping"] = True
        except Exception as exc:
            checks["supabase_ping"] = False
            messages.append(f"Supabase 연결 실패: {exc}")
            log_error("Supabase pre-flight ping 실패", source="verify_system_health", exc=exc)
    else:
        checks["supabase_secrets"] = not bool(supabase_url and supabase_key)
        checks["supabase_ping"] = True

    if kakao_direct:
        login_ok = checks["kakao_rest_api_key"]
    elif supabase_ready:
        login_ok = checks.get("supabase_ping", False) and checks.get("supabase_secrets", False)
    else:
        login_ok = False
        if not messages:
            messages.append("KAKAO_REST_API_KEY 또는 Supabase OAuth 미설정")

    return {
        "ok": login_ok,
        "login_ok": login_ok,
        "login_message": "현재 점검 중입니다" if not login_ok else "",
        "checks": checks,
        "messages": messages,
        "checked_at": _now_iso(),
    }


def run_preflight() -> dict[str, Any]:
    """세션당 1회 pre-flight (실패 시 login 버튼 비활성)."""
    init_error_guard()
    cached = st.session_state.get("system_health")
    if cached:
        return cached

    try:
        health = verify_system_health()
    except Exception as exc:
        log_error("Pre-flight 검사 실패", source="run_preflight", exc=exc)
        health = {
            "ok": False,
            "login_ok": False,
            "login_message": "현재 점검 중입니다",
            "checks": {},
            "messages": [str(exc)],
            "checked_at": _now_iso(),
        }

    st.session_state.system_health = health
    if not health.get("login_ok") and health.get("messages"):
        log_error(
            "Pre-flight: 로그인 비활성",
            source="run_preflight",
            extra={"messages": health["messages"]},
        )
    return health


def get_system_health() -> dict[str, Any]:
    return st.session_state.get("system_health") or run_preflight()


def login_actions_enabled() -> bool:
    return bool(get_system_health().get("login_ok", True))


def login_disabled_tooltip() -> str:
    health = get_system_health()
    return health.get("login_message") or "현재 점검 중입니다"


def with_retry(fn: Callable[..., Any]) -> Callable[..., Any]:
    """임의 callable에 tenacity 재시도 적용."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True,
        before_sleep=_on_retry,
    )(fn)
