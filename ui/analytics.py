"""GA4 · 서비스 트래킹 (선택)."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def _ga_id() -> str | None:
    try:
        if "GA_MEASUREMENT_ID" in st.secrets:
            v = str(st.secrets["GA_MEASUREMENT_ID"]).strip()
            if v and v.startswith("G-"):
                return v
    except Exception:
        pass
    import os

    v = os.environ.get("GA_MEASUREMENT_ID", "").strip()
    return v if v.startswith("G-") else None


def inject_ga4() -> None:
    """Google Analytics 4 — Secrets에 GA_MEASUREMENT_ID=G-XXXX."""
    gid = _ga_id()
    if not gid:
        return
    components.html(
        f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>
        <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{gid}');
        </script>
        """,
        height=0,
        width=0,
    )
