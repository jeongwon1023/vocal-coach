"""Local browser flow QA — demo login, analysis settings, sample toggle."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.browser_helpers import app_frame

LOCAL = "http://localhost:8501/"
CRASH_KEYWORDS = (
    "Traceback (most recent",
    "ImportError",
    "ModuleNotFoundError",
    "StreamlitAPIException",
)


def _has_crash(text: str) -> bool:
    return any(k in text for k in CRASH_KEYWORDS)


def run_flow_qa() -> tuple[list[str], list[str]]:
    from playwright.sync_api import sync_playwright

    issues: list[str] = []
    checks: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(LOCAL, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(6_000)
            app = app_frame(page)

            app.get_by_role("button", name="☰").first.click(timeout=10_000)
            app.wait_for_timeout(1_500)
            app.locator("button").filter(has_text="마이").first.click(timeout=10_000)
            app.wait_for_timeout(4_000)

            demo = app.get_by_role("button").filter(has_text="체험")
            if demo.count() == 0:
                issues.append("demo login button missing on my page gate")
            else:
                clicked = False
                for i in range(demo.count()):
                    btn = demo.nth(i)
                    if btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        btn.click(timeout=15_000)
                        clicked = True
                        break
                if not clicked:
                    demo.first.scroll_into_view_if_needed()
                    demo.first.click(force=True, timeout=15_000)
                app.wait_for_timeout(5_000)
                body = app.inner_text("body")
                if _has_crash(body):
                    issues.append("crash after demo login")
                elif "새 분석" not in body and "분석" not in body:
                    issues.append(f"hub not shown after demo login: {body[:200]!r}")
                else:
                    checks.append("demo login → my page hub OK")

            expander = app.locator("summary").filter(has_text="분석 설정")
            if expander.count() == 0:
                issues.append("analysis settings expander missing after login")
            else:
                if not expander.first.is_visible():
                    expander.first.click(timeout=10_000)
                    app.wait_for_timeout(2_000)
                settings_body = app.inner_text("body")
                if "빠른 분석" not in settings_body:
                    issues.append("fast_mode not visible in settings")
                elif _has_crash(settings_body):
                    issues.append("crash in analysis settings")
                else:
                    checks.append("analysis settings expander OK")

            upload_exp = app.locator("summary").filter(has_text="녹음 파일")
            if upload_exp.count():
                upload_exp.first.scroll_into_view_if_needed()
                upload_exp.first.click(timeout=10_000)
                app.wait_for_timeout(1_500)

            sample = app.locator("label").filter(has_text="샘플")
            if sample.count():
                sample.first.scroll_into_view_if_needed()
                sample.first.click(timeout=10_000)
                app.wait_for_timeout(1_000)
                checks.append("sample toggle OK")
            else:
                issues.append("sample toggle missing")

            analyze = app.locator("button").filter(has_text="분석 시작")
            if analyze.count():
                checks.append("analyze button present")
            else:
                issues.append("analyze button missing")

            back = app.locator("button").filter(has_text="Vocal Coach")
            if back.count():
                back.first.click(timeout=10_000)
                app.wait_for_timeout(3_000)
                if any(k in app.inner_text("body") for k in ("점수", "Vocal", "무료")):
                    checks.append("home navigation OK")

            app.get_by_role("button", name="☰").first.click(timeout=10_000)
            app.wait_for_timeout(1_500)
            fb_btn = app.get_by_role("button", name="💬 피드백")
            if fb_btn.count() == 0:
                fb_btn = app.locator("button").filter(has_text="피드백")
            fb_btn.first.click(timeout=10_000)
            app.wait_for_timeout(3_000)
            fb = app.inner_text("body")
            if _has_crash(fb):
                issues.append("crash on feedback page")
            elif not any(k in fb for k in ("피드백", "의견", "평가")):
                issues.append("feedback page content unclear")
            else:
                checks.append("feedback page OK")

        except Exception as exc:
            if "ERR_CONNECTION_REFUSED" in str(exc):
                checks.append("local server not running (skipped)")
            else:
                issues.append(str(exc))
        finally:
            page.close()
            browser.close()

    return issues, checks


if __name__ == "__main__":
    issues, checks = run_flow_qa()
    for c in checks:
        print("OK", c)
    for i in issues:
        print("ISSUE", i)
    sys.exit(1 if issues else 0)
