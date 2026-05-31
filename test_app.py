"""Streamlit AppTest 기반 자가 QA — 관리자 페이지에서 실행."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP_PATH = ROOT / "app.py"

CRASH_MARKERS = (
    "Traceback (most recent call last)",
    "StreamlitAPIException",
    "ModuleNotFoundError",
    "ImportError",
)


def _page_text(block: Any) -> str:
    try:
        if isinstance(block, str):
            return block
        if isinstance(block, list):
            return "\n".join(str(x) for x in block)
        value = getattr(block, "value", None)
        if value is not None:
            if isinstance(value, list):
                return "\n".join(str(x) for x in value)
            return str(value)
        return str(block)
    except Exception:
        return ""


def _collect_text(at: Any) -> str:
    parts: list[str] = []
    for attr in ("markdown", "title", "caption", "text", "button", "info", "warning", "error"):
        try:
            blocks = getattr(at, attr, None)
            if blocks is None:
                continue
            if not isinstance(blocks, list):
                blocks = [blocks]
            for block in blocks:
                text = _page_text(block)
                if text:
                    parts.append(text)
        except Exception:
            continue
    return "\n".join(parts)


def _check_no_crash(text: str, step: str) -> dict[str, Any]:
    for marker in CRASH_MARKERS:
        if marker in text:
            return {"step": step, "status": "fail", "detail": f"HTML/Traceback 노출: {marker}"}
    return {"step": step, "status": "pass", "detail": "크래시 징후 없음"}


def run_app_qa(*, timeout: int = 120) -> list[dict[str, Any]]:
    """가상 유저 플로우 — 홈 → 마이 페이지 → (분석 UI 존재 확인)."""
    results: list[dict[str, Any]] = []

    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        return [
            {
                "step": "AppTest import",
                "status": "fail",
                "detail": "streamlit.testing.v1.AppTest 미지원 — Streamlit 1.46+ 필요",
            }
        ]

    if not APP_PATH.exists():
        return [{"step": "app.py", "status": "fail", "detail": f"앱 파일 없음: {APP_PATH}"}]

    try:
        at = AppTest.from_file(str(APP_PATH), default_timeout=timeout)
        at.run(timeout=timeout)
    except Exception as exc:
        return [{"step": "앱 기동", "status": "fail", "detail": str(exc)}]

    body = _collect_text(at)
    results.append(_check_no_crash(body, "메인 화면 진입"))

    hero_ok = any(
        kw in body
        for kw in ("무료로 내 보컬 분석", "프로 보컬 코치", "Vocal Coach", "보컬")
    )
    results.append(
        {
            "step": "랜딩 히어로",
            "status": "pass" if hero_ok else "fail",
            "detail": "히어로 CTA 확인" if hero_ok else "랜딩 문구 미탐지",
        }
    )

    try:
        cta = at.button(key="landing_hero_cta")
        if cta is None:
            for btn in at.button:
                label = getattr(btn, "label", "") or ""
                if "분석" in str(label):
                    cta = btn
                    break
        if cta is not None:
            cta.click().run(timeout=timeout)
            body2 = _collect_text(at)
            results.append(_check_no_crash(body2, "무료 분석 CTA 클릭"))
            my_ok = any(kw in body2 for kw in ("마이 페이지", "분석", "녹음", "업로드"))
            results.append(
                {
                    "step": "마이 페이지 이동",
                    "status": "pass" if my_ok else "warn",
                    "detail": "분석 UI 탐지" if my_ok else "마이 페이지 콘텐츠 불명확",
                }
            )
        else:
            results.append(
                {
                    "step": "무료 분석 CTA",
                    "status": "warn",
                    "detail": "landing_hero_cta 버튼 미탐지 (키 변경 가능)",
                }
            )
    except Exception as exc:
        results.append({"step": "CTA 클릭", "status": "fail", "detail": str(exc)})

    oauth_ok = "oauth_callback_active" in open(ROOT / "ui" / "error_guard.py", encoding="utf-8").read()
    results.append(
        {
            "step": "OAuth 재시도 가드",
            "status": "pass" if oauth_ok else "fail",
            "detail": "error_guard.oauth_callback_active 존재",
        }
    )

    restore_ok = "_restore_result_session" in open(ROOT / "ui" / "my_page.py", encoding="utf-8").read()
    results.append(
        {
            "step": "분석 후 결과 복원",
            "status": "pass" if restore_ok else "fail",
            "detail": "my_page._restore_result_session 존재",
        }
    )

    return results


def qa_summary(results: list[dict[str, Any]]) -> tuple[bool, str]:
    fails = [r for r in results if r.get("status") == "fail"]
    if fails:
        return False, "오류 발견 (Red)"
    warns = [r for r in results if r.get("status") == "warn"]
    if warns:
        return True, "주의 항목 있음 (Yellow)"
    return True, "이상 없음 (Green)"


def log_qa_failures(results: list[dict[str, Any]]) -> None:
    """실패 시 error_logs에 기록 (관리자 페이지 rerun 시)."""
    try:
        import streamlit as st
        from ui.error_guard import init_error_guard, log_error

        init_error_guard()
        for row in results:
            if row.get("status") == "fail":
                log_error(
                    f"QA 자동 테스트 실패: {row.get('step')}",
                    source="test_app",
                    extra={"detail": row.get("detail")},
                )
    except Exception:
        pass


if __name__ == "__main__":
    rows = run_app_qa()
    ok, label = qa_summary(rows)
    for row in rows:
        icon = {"pass": "✅", "fail": "❌", "warn": "⚠️"}.get(row["status"], "·")
        print(f"{icon} {row['step']}: {row['detail']}")
    print(label)
    sys.exit(0 if ok else 1)
