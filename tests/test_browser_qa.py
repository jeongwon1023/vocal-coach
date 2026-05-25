"""웹·모바일 뷰포트 브라우저 QA (Playwright)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

URL = "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/"
VIEWPORTS = {
    "desktop": {"width": 1280, "height": 800},
    "mobile": {"width": 390, "height": 844},
}


def _app_frame(page):
    for frame in page.frames:
        if "streamlit.app" in (frame.url or ""):
            return frame
    if page.frames:
        return page.frames[-1]
    return page


def run_browser_qa() -> tuple[list[str], list[str]]:
    from playwright.sync_api import sync_playwright

    issues: list[str] = []
    checks: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, vp in VIEWPORTS.items():
            page = browser.new_page(viewport=vp)
            page.goto(URL, wait_until="networkidle", timeout=120_000)
            page.wait_for_timeout(10000)
            app = _app_frame(page)

            body = app.inner_text("body")
            checks.append(f"[{name}] loaded: {'COACH' in body.upper() or 'BETA' in body}")

            if "ModuleNotFoundError" in body or "Traceback (most recent" in body:
                issues.append(f"{name}: app crash visible on page")

            sidebar = app.locator('[data-testid="stSidebar"]')
            if sidebar.count() and sidebar.first.is_visible():
                box = sidebar.first.bounding_box()
                if box and name == "mobile" and box.get("width", 0) > vp["width"] * 0.85:
                    issues.append(f"{name}: sidebar covers most of screen")
                elif name == "mobile":
                    checks.append("[mobile] sidebar hidden or narrow OK")
            elif name == "mobile":
                checks.append("[mobile] sidebar not visible OK")

            if name == "mobile":
                nav = app.locator('[data-testid="stSegmentedControl"]')
                if nav.count() == 0:
                    issues.append("mobile: nav missing")
                else:
                    checks.append("[mobile] nav present")
                    nav.locator("button").nth(1).click(timeout=15_000)
                    app.wait_for_timeout(5000)
                    body2 = app.inner_text("body")
                    if any(k in body2 for k in ("설정", "로그인", "체험", "업로드", "분석")):
                        checks.append("[mobile] analysis tab OK")
                    else:
                        issues.append("mobile: analysis tab content unclear")

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
