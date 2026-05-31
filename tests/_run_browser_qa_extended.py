"""Extended browser QA — cloud + local, navigation, crash detection."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.browser_helpers import app_frame, wait_for_app

URLS = [
    ("cloud", "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/"),
    ("local", "http://localhost:8501/"),
]

CRASH_KEYWORDS = (
    "Traceback (most recent",
    "ImportError",
    "ModuleNotFoundError",
    "StreamlitAPIException",
    "AttributeError",
    "NameError",
    "KeyError:",
)

CONTENT_KEYWORDS = ("Vocal", "보컬", "분석", "홈", "마이", "피드백", "BETA", "베타")
MY_PAGE_KEYWORDS = ("로그인", "분석", "Google", "카카오", "기록", "새 분석")
FEEDBACK_KEYWORDS = ("피드백", "의견", "평가", "남기", "베타")


def _app_frame(page):
    return app_frame(page)


def _has_crash(text: str) -> str | None:
    for kw in CRASH_KEYWORDS:
        if kw in text:
            return kw
    return None


def run_extended_qa() -> tuple[list[str], list[str]]:
    from playwright.sync_api import sync_playwright

    issues: list[str] = []
    checks: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for label, url in URLS:
            for vp_name, vp in (
                ("desktop", {"width": 1280, "height": 800}),
                ("mobile", {"width": 390, "height": 844}),
            ):
                page = browser.new_page(viewport=vp)
                tag = f"{label}/{vp_name}"
                try:
                    page.goto(url, wait_until="networkidle", timeout=90_000)
                    app = _app_frame(page)
                    wait_for_app(page, app)
                    page.wait_for_timeout(5_000)
                    app = _app_frame(page)
                    body = app.inner_text("body")
                    html = app.content()

                    crash = _has_crash(body) or _has_crash(html)
                    if crash:
                        issues.append(f"{tag}: {crash} visible on page")

                    if not any(k in body for k in CONTENT_KEYWORDS):
                        issues.append(f"{tag}: expected content not found")
                    else:
                        checks.append(f"{tag}: page loaded ({len(body)} chars)")

                    menu = app.get_by_role("button", name="☰")
                    if menu.count() == 0:
                        issues.append(f"{tag}: hamburger menu missing")
                    else:
                        checks.append(f"{tag}: hamburger menu present")
                        menu.first.click(timeout=10_000)
                        page.wait_for_timeout(2_000)
                        menu_body = app.inner_text("body")
                        if not any(k in menu_body for k in ("마이", "홈", "피드백", "메뉴")):
                            issues.append(f"{tag}: menu items not visible")
                        else:
                            checks.append(f"{tag}: menu opens OK")

                        my_btn = app.get_by_role("button", name="📈 마이")
                        if my_btn.count() == 0:
                            my_btn = app.locator("button").filter(has_text="마이")
                        if my_btn.count():
                            my_btn.first.click(timeout=10_000)
                            page.wait_for_timeout(5_000)
                            my_body = app.inner_text("body")
                            my_crash = _has_crash(my_body)
                            if my_crash:
                                issues.append(f"{tag}: {my_crash} on my page")
                            elif not any(k in my_body for k in MY_PAGE_KEYWORDS):
                                issues.append(f"{tag}: my page unclear: {my_body[:180]!r}")
                            else:
                                checks.append(f"{tag}: my page OK")
                        else:
                            issues.append(f"{tag}: my page button missing")

                    brand = app.get_by_role("button", name="🎤 Vocal Coach")
                    if brand.count():
                        brand.first.click(timeout=10_000)
                        page.wait_for_timeout(3_000)

                    menu = app.get_by_role("button", name="☰")
                    if menu.count():
                        menu.first.click(timeout=10_000)
                        page.wait_for_timeout(1_500)
                        fb = app.get_by_role("button", name="💬 피드백")
                        if fb.count() == 0:
                            fb = app.locator("button").filter(has_text="피드백")
                        if fb.count():
                            fb.first.click(timeout=10_000)
                            page.wait_for_timeout(4_000)
                            fb_body = app.inner_text("body")
                            fb_crash = _has_crash(fb_body)
                            if fb_crash:
                                issues.append(f"{tag}: {fb_crash} on feedback page")
                            elif not any(k in fb_body for k in FEEDBACK_KEYWORDS):
                                issues.append(f"{tag}: feedback page unclear")
                            else:
                                checks.append(f"{tag}: feedback page OK")

                    out = ROOT / "tests" / f"_qa_{label}_{vp_name}.png"
                    page.screenshot(path=str(out), full_page=True)
                except Exception as exc:
                    if label == "local" and "ERR_CONNECTION_REFUSED" in str(exc):
                        checks.append(f"{tag}: local server not running (skipped)")
                    else:
                        issues.append(f"{tag}: {exc}")
                finally:
                    page.close()

        browser.close()

    return issues, checks


if __name__ == "__main__":
    issues, checks = run_extended_qa()
    for c in checks:
        print("OK", c)
    for i in issues:
        print("ISSUE", i)
    if issues:
        sys.exit(1)
    print("Extended browser QA passed.")
