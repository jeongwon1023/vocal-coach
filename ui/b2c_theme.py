"""Codeit/Toss 스타일 B2C — CSS 확장 · 랜딩 FX · 플로팅 CTA."""

from __future__ import annotations

import streamlit as st

from ui.navigation import go_to
from ui.utils import render_safe_html


def page_slug(page: str) -> str:
    return {"홈": "home", "마이 페이지": "mypage", "피드백": "feedback"}.get(page, "other")


def inject_page_marker(page: str) -> None:
    slug = page_slug(page)
    render_safe_html(
        f"""
        <div id="vc-page-root" data-vc-page="{slug}" aria-hidden="true"></div>
        <script>document.body.setAttribute("data-vc-page", "{slug}");</script>
        """
    )


def css_extension(page: str) -> str:
    slug = page_slug(page)
    return f"""
        /* ── B2C Design System (Codeit/Toss) ── */
        :root {{
            --vc-radius: 12px;
            --vc-radius-lg: 16px;
            --vc-shadow-sm: 0 1px 3px rgba(28, 21, 40, 0.06);
            --vc-shadow-md: 0 4px 16px rgba(28, 21, 40, 0.08);
            --vc-shadow-lg: 0 8px 28px rgba(99, 102, 241, 0.12);
            --vc-black: #1c1528;
            --vc-header-h: 64px;
        }}

        header[data-testid="stHeader"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
        }}

        .block-container {{
            padding-top: calc(var(--vc-header-h) + 12px) !important;
            padding-bottom: 5.5rem !important;
            max-width: 768px !important;
            padding-left: 24px !important;
            padding-right: 24px !important;
        }}

        body[data-vc-page="home"] .block-container {{
            padding-bottom: 6.5rem !important;
        }}

        /* Fixed navbar row */
        .vc-navbar-marker + [data-testid="stHorizontalBlock"] {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 999 !important;
            max-width: 100% !important;
            margin: 0 !important;
            border-radius: 0 !important;
            border-left: none !important;
            border-right: none !important;
            border-top: none !important;
            padding: 0.45rem 1rem !important;
            min-height: var(--vc-header-h);
            box-shadow: var(--vc-shadow-md) !important;
            background: rgba(255, 255, 255, 0.92) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
        }}

        .vc-fixed-header-brand {{
            display: none !important;
        }}

        /* Card UI — expander, tabs, bordered containers */
        [data-testid="stExpander"],
        [data-testid="stTabs"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--vc-card) !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: var(--vc-radius) !important;
            box-shadow: var(--vc-shadow-sm) !important;
            overflow: hidden;
        }}
        [data-testid="stExpander"] details {{
            border: none !important;
            background: transparent !important;
        }}
        [data-testid="stExpander"] summary {{
            padding: 0.85rem 1rem !important;
            font-weight: 700 !important;
        }}
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            background: var(--vc-surface) !important;
            border-bottom: 1px solid var(--vc-border) !important;
            gap: 0.25rem !important;
            padding: 0.35rem 0.5rem 0 !important;
        }}
        [data-testid="stTabs"] [data-baseweb="tab"] {{
            border-radius: 10px 10px 0 0 !important;
            font-weight: 600 !important;
        }}
        [data-testid="stTabs"] [aria-selected="true"] {{
            background: var(--vc-card) !important;
            color: var(--vc-accent) !important;
        }}

        .stButton > button {{
            border-radius: var(--vc-radius) !important;
            font-weight: 700 !important;
            min-height: 2.75rem !important;
            box-shadow: var(--vc-shadow-sm) !important;
        }}
        .stButton > button[kind="primary"] {{
            box-shadow: var(--vc-shadow-lg) !important;
        }}

        .vc-app-card {{
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius-lg);
            box-shadow: var(--vc-shadow-md);
            padding: 1.15rem 1.2rem;
            margin: 0.65rem 0 1rem;
        }}
        .card-container {{
            background: #ffffff;
            border: 1px solid var(--vc-border);
            border-radius: 16px;
            box-shadow: var(--vc-shadow-md);
            padding: 1.15rem 1.25rem 1.25rem;
            margin-bottom: 24px;
            overflow: visible;
        }}
        .vc-card-heading {{
            margin: 0 0 0.85rem;
            font-size: 1.12rem;
            font-weight: 800;
            color: var(--vc-black);
            letter-spacing: -0.02em;
        }}
        .vc-coach-stage-title {{
            margin: 0.75rem 0 0.35rem;
            font-size: 1rem;
            font-weight: 800;
            color: var(--vc-black);
        }}
        .vc-vocal-mbti-badge {{
            display: inline-block;
            margin: 0 0 0.65rem;
            padding: 12px 20px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.14), rgba(168, 85, 247, 0.12));
            color: #4338ca;
            font-size: 0.95rem;
            font-weight: 800;
            line-height: 1.5;
            max-width: 100%;
            box-sizing: border-box;
            overflow-wrap: break-word;
        }}
        .vc-app-card-title {{
            margin: 0 0 0.35rem;
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--vc-black);
        }}
        .vc-record-hero-badge {{
            display: inline-block;
            margin-top: 0.5rem;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            background: rgba(99, 102, 241, 0.1);
            color: var(--vc-accent);
            font-size: 0.78rem;
            font-weight: 700;
        }}

        .vc-result-shell,
        .vc-graph-frame,
        .vc-sparkline-frame {{
            background: var(--vc-card) !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: var(--vc-radius-lg) !important;
            box-shadow: var(--vc-shadow-md) !important;
            padding: 0.75rem !important;
            margin: 0.5rem 0 1rem !important;
            overflow: hidden;
        }}
        .vc-result-shell img,
        .vc-graph-frame img {{
            border-radius: calc(var(--vc-radius) - 2px) !important;
        }}

        .st-key-vc_dm_panel {{
            background: var(--vc-card) !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: var(--vc-radius-lg) !important;
            box-shadow: var(--vc-shadow-lg) !important;
            padding: 0.5rem 0.65rem 0.75rem !important;
            margin: 0.75rem 0 1rem !important;
        }}

        /* Floating CTA — Hero 지나면 표시 (JS 없으면 항상 표시) */
        .st-key-vc_floating_cta {{
            position: fixed !important;
            bottom: max(12px, env(safe-area-inset-bottom)) !important;
            left: 12px !important;
            right: 12px !important;
            z-index: 997 !important;
            max-width: 520px !important;
            margin: 0 auto !important;
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
            transition: opacity 0.35s ease, transform 0.35s ease;
        }}
        body[data-vc-page="home"][data-vc-float-ready="0"] .st-key-vc_floating_cta {{
            opacity: 0;
            transform: translateY(16px);
            pointer-events: none;
        }}
        body[data-vc-page="home"] .st-key-vc_floating_cta.vc-float-visible,
        body[data-vc-float-ready="1"] .st-key-vc_floating_cta {{
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }}
        .st-key-vc_floating_cta_mypage {{
            position: fixed !important;
            bottom: max(12px, env(safe-area-inset-bottom)) !important;
            left: 12px !important;
            right: 12px !important;
            z-index: 997 !important;
            max-width: 520px !important;
            margin: 0 auto !important;
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }}
        .st-key-vc_floating_cta > div,
        .st-key-vc_floating_cta_mypage > div {{
            width: 100% !important;
        }}
        .st-key-vc_floating_cta button,
        .st-key-vc_floating_cta_mypage button {{
            width: 100% !important;
            border-radius: var(--vc-radius) !important;
            min-height: 3.25rem !important;
            font-size: 1rem !important;
            box-shadow: 0 8px 28px rgba(99, 102, 241, 0.35) !important;
        }}

        body[data-vc-page="mypage"] .st-key-vc_floating_cta,
        body[data-vc-page="feedback"] .st-key-vc_floating_cta,
        body.vc-analyzing .st-key-vc_floating_cta,
        body.vc-analyzing .st-key-vc_floating_cta_mypage,
        body.vc-show-result .st-key-vc_floating_cta_mypage {{
            display: none !important;
        }}

        /* Landing — 콘텐츠는 항상 표시 (Streamlit은 markdown script 미실행) */
        .fade-in-up {{
            opacity: 1 !important;
            transform: none !important;
        }}
        .fade-in-up.is-visible {{
            animation: vc-fade-up 0.55s ease-out;
        }}
        @keyframes vc-fade-up {{
            from {{ opacity: 0.4; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .vc-count-up {{
            font-variant-numeric: tabular-nums;
        }}

        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 0.85rem !important;
                padding-right: 0.85rem !important;
            }}
            .vc-navbar-marker + [data-testid="stHorizontalBlock"] {{
                padding: 0.4rem 0.75rem !important;
            }}
            .vc-pain-grid, .vc-tech-grid {{
                grid-template-columns: 1fr !important;
            }}
            .vc-trust-row {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
        }}
    """


def landing_scroll_script() -> str:
    return """
    <script>
    (function () {
        const root = document.getElementById('vc-page-root');
        const isHome = root && root.getAttribute('data-vc-page') === 'home';

        function revealAll() {
            document.querySelectorAll('.fade-in-up:not(.is-visible)').forEach(function (el) {
                el.classList.add('is-visible');
            });
        }

        if (isHome) {
            const obs = new IntersectionObserver(function (entries) {
                entries.forEach(function (e) {
                    if (e.isIntersecting) e.target.classList.add('is-visible');
                });
            }, { threshold: 0.08 });
            document.querySelectorAll('.fade-in-up').forEach(function (el) { obs.observe(el); });

            const hero = document.getElementById('vc-landing-hero');
            const floatBtn = document.querySelector('.st-key-vc_floating_cta');
            if (hero && floatBtn) {
                document.body.setAttribute('data-vc-float-ready', '0');
                const floatObs = new IntersectionObserver(function (entries) {
                    if (entries[0] && !entries[0].isIntersecting) {
                        floatBtn.classList.add('vc-float-visible');
                    } else {
                        floatBtn.classList.remove('vc-float-visible');
                    }
                }, { threshold: 0 });
                floatObs.observe(hero);
            } else if (floatBtn) {
                document.body.setAttribute('data-vc-float-ready', '1');
            }
        }

        document.querySelectorAll('.vc-count-up').forEach(function (el) {
            const target = parseFloat(el.getAttribute('data-target') || '0');
            const suffix = el.getAttribute('data-suffix') || '';
            const prefix = el.getAttribute('data-prefix') || '';
            const decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
            let start = 0;
            const dur = 900;
            const t0 = performance.now();
            function tick(now) {
                const p = Math.min(1, (now - t0) / dur);
                const val = start + (target - start) * (1 - Math.pow(1 - p, 3));
                el.textContent = prefix + val.toFixed(decimals) + suffix;
                if (p < 1) requestAnimationFrame(tick);
            }
            const io = new IntersectionObserver(function (entries) {
                if (entries[0].isIntersecting) {
                    requestAnimationFrame(tick);
                    io.disconnect();
                }
            }, { threshold: 0.3 });
            io.observe(el);
        });
    })();
    </script>
    """


def render_floating_cta(*, variant: str = "landing") -> None:
    """variant: landing | mypage | hidden"""
    if variant == "hidden":
        return
    if variant == "landing":
        if st.button(
            "🎤 무료로 내 보컬 분석하기",
            type="primary",
            use_container_width=True,
            key="vc_floating_cta"
        ):
            go_to("마이 페이지")
        return
    if variant == "mypage":
        if st.button(
            "🎵 새로운 분석하기",
            type="primary",
            use_container_width=True,
            key="vc_floating_cta_mypage"
        ):
            from ui.scroll import scroll_to_top

            scroll_to_top(anchor_id="vc-new-analysis")
            st.rerun()
