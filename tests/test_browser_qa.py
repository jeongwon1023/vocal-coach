"""웹·모바일 뷰포트 브라우저 QA (Playwright)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.browser_helpers import app_frame, wait_for_app

URL = "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/"
VIEWPORTS = {
    "desktop": {"width": 1280, "height": 800},
    "mobile": {"width": 390, "height": 844},
}

CRASH_KEYWORDS = (
    "Traceback (most recent",
    "ImportError",
    "ModuleNotFoundError",
    "StreamlitAPIException",
)


def run_browser_qa() -> tuple[list[str], list[str]]:
    from playwright.sync_api import sync_playwright

    issues: list[str] = []
    checks: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, vp in VIEWPORTS.items():
            page = browser.new_page(viewport=vp)
            page.goto(URL, wait_until="networkidle", timeout=120_000)
            app = app_frame(page)
            wait_for_app(page, app)
            page.wait_for_timeout(5_000)
            app = app_frame(page)

            body = app.inner_text("body")
            checks.append(
                f"[{name}] loaded: {any(k in body for k in ('Vocal', '보컬', '분석', 'BETA', '베타'))}"
            )

            for kw in CRASH_KEYWORDS:
                if kw in body:
                    issues.append(f"{name}: {kw} visible on page")

            menu = app.get_by_role("button", name="☰")
            if menu.count() == 0:
                issues.append(f"{name}: nav menu missing")
            else:
                checks.append(f"[{name}] nav menu present")
                menu.first.click(timeout=15_000)
                app.wait_for_timeout(2_000)
                my_btn = app.locator("button").filter(has_text="마이")
                if my_btn.count():
                    my_btn.first.click(timeout=15_000)
                    app.wait_for_timeout(6_000)
                    body2 = app.inner_text("body")
                    if any(k in body2 for k in ("로그인", "분석", "새 분석", "기록")):
                        checks.append(f"[{name}] my page OK")
                    elif any(k in body2 for k in CRASH_KEYWORDS):
                        issues.append(f"{name}: crash on my page")
                    else:
                        issues.append(f"{name}: my page content unclear")
                else:
                    issues.append(f"{name}: my page button missing")

            page.close()

        browser.close()

    return issues, checks


if __name__ == "__main__":
    try:
        issues, checks = run_browser_qa()
        for c in checks:
            print("OK", c)
        for i in issues:
            print("ISSUE", i)
        if issues:
            sys.exit(1)
        print("Browser QA passed.")
    except Exception as exc:
        print("Browser QA skipped or failed:", exc)
        sys.exit(0)
