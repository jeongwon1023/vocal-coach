"""Streamlit Cloud iframe · sleep screen helpers for Playwright QA."""

from __future__ import annotations


def app_frame(page):
    """Return the Streamlit app frame (Cloud embeds app in ~/+/ iframe)."""
    for frame in page.frames:
        url = frame.url or ""
        if "about:blank" in url or "statuspage.io" in url or url == "about:srcdoc":
            continue
        if "~/+/" in url or "/-/+/" in url:
            return frame

    best = page
    best_len = 0
    for frame in page.frames:
        url = frame.url or ""
        if "statuspage.io" in url or url.startswith("about:"):
            continue
        try:
            n = len(frame.inner_text("body"))
            if n > best_len:
                best_len = n
                best = frame
        except Exception:
            continue
    return best


def wake_streamlit_app(page, *, wait_ms: int = 25_000) -> bool:
    """Wake Streamlit Cloud sleep screen if shown."""
    body = page.inner_text("body")
    if "gone to sleep" not in body and "Zzzz" not in body:
        return False
    wake = page.get_by_role("button", name="Yes, get this app back up!")
    if wake.count() == 0:
        wake = page.locator("button, a").filter(has_text="back up")
    if wake.count() == 0:
        return False
    wake.first.click(timeout=15_000)
    page.wait_for_timeout(wait_ms)
    return True


def wait_for_app(page, app, *, timeout_ms: int = 60_000) -> None:
    """Wait until app iframe has meaningful content."""
    wake_streamlit_app(page)
    elapsed = 0
    step = 2_000
    while elapsed < timeout_ms:
        try:
            body = app.inner_text("body")
            if len(body.strip()) > 100:
                if any(k in body for k in ("Vocal", "보컬", "분석", "BETA", "베타", "Hosted")):
                    if "gone to sleep" not in body:
                        return
        except Exception:
            pass
        page.wait_for_timeout(step)
        elapsed += step
        app = app_frame(page)
    return app
