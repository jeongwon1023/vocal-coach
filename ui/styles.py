"""Streamlit — Yousician · Moises · Smule · SingSharp · Simply Sing inspired theme."""

from __future__ import annotations

import streamlit as st


def apply(page: str = "홈") -> None:
    sidebar_css = """
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarNav"],
        button[data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarHeader"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            overflow: hidden !important;
        }
        [data-testid="stAppViewContainer"] > section.main {
            margin-left: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        .block-container {
            max-width: 960px !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
        @media (max-width: 768px) {
            .block-container {
                max-width: 100% !important;
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }
        }
    """

    st.markdown(
        """
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {
            --vc-bg: #f4f2f8;
            --vc-surface: #faf9fd;
            --vc-card: #ffffff;
            --vc-border: #e0dce8;
            --vc-text: #1c1528;
            --vc-muted: #6e667d;
            --vc-accent: #6366f1;
            --vc-accent-2: #8b5cf6;
            --vc-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            --vc-gradient-soft: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(248,246,255,0.96) 100%);
            --vc-gradient-card: linear-gradient(155deg, #ffffff 0%, #f8f6ff 48%, #f0ebff 100%);
            --vc-gradient-mesh:
                radial-gradient(ellipse 100% 65% at 50% -18%, rgba(129,140,248,0.14), transparent 58%),
                radial-gradient(ellipse 55% 45% at -5% 45%, rgba(168,85,247,0.08), transparent 52%),
                radial-gradient(ellipse 50% 40% at 105% 70%, rgba(99,102,241,0.06), transparent 50%),
                linear-gradient(180deg, #faf8ff 0%, #f4f2f8 45%, #efeaf8 100%);
            --vc-glow: rgba(99, 102, 241, 0.22);
            --vc-kakao: #FEE500;
            --vc-kakao-text: #191919;
            --vc-radius: 14px;
            --vc-radius-lg: 20px;
        }

        html, body {
            background: var(--vc-bg) !important;
            color-scheme: light;
        }

        html, body, [class*="css"] {
            font-family: 'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        * {
            -webkit-tap-highlight-color: transparent;
        }

        .stApp {
            min-height: 100vh;
            background: var(--vc-gradient-mesh) !important;
            background-color: var(--vc-bg) !important;
            background-attachment: fixed !important;
            color: var(--vc-text);
        }

        #MainMenu, footer, [data-testid="stToolbar"], .stAppDeployButton {
            visibility: hidden !important;
            display: none !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        .block-container {
            padding-top: 0.5rem !important;
            max-width: 1100px !important;
        }

        /* ── Header bar — 클릭 방해 없음 ── */
        .vc-header-shell {
            pointer-events: none !important;
        }
        .vc-navbar-marker + [data-testid="stHorizontalBlock"] {
            position: relative;
            z-index: 200;
            background: linear-gradient(165deg, rgba(255,255,255,0.94) 0%, rgba(248,246,255,0.97) 100%);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(99,102,241,0.14);
            border-radius: 18px;
            padding: 0.5rem 0.7rem !important;
            margin: -0.25rem 0 0.5rem !important;
            box-shadow: 0 8px 32px rgba(99,102,241,0.08), inset 0 1px 0 rgba(255,255,255,0.8);
        }
        .vc-navbar-marker + [data-testid="stHorizontalBlock"] > div {
            align-items: center !important;
            flex-wrap: nowrap !important;
        }
        .vc-navbar-marker + [data-testid="stHorizontalBlock"] [data-testid="column"] {
            min-width: 0 !important;
        }
        .vc-nav-menu-title {
            margin: 0 0 0.55rem;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #6e667d !important;
        }
        .st-key-nav_mobile_menu,
        .st-key-nav_menu {
            position: relative;
            z-index: 201;
        }
        .st-key-nav_mobile_menu > div > button,
        .st-key-nav_menu > div > button {
            background: rgba(99,102,241,0.1) !important;
            border: 1px solid rgba(99,102,241,0.22) !important;
            color: #4338ca !important;
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            min-height: 2.65rem !important;
            min-width: 2.65rem !important;
            padding: 0.35rem 0.5rem !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }
        .st-key-nav_mobile_menu > div > button:hover,
        .st-key-nav_menu > div > button:hover {
            background: rgba(99,102,241,0.16) !important;
            border-color: rgba(99,102,241,0.35) !important;
            color: #4f46e5 !important;
        }
        [data-testid="stPopoverBody"]:has(.st-key-nav_menu_btn_홈),
        [data-testid="stPopoverBody"]:has([class*="st-key-nav_menu_btn_"]) {
            min-width: min(88vw, 280px) !important;
            padding: 0.85rem 0.75rem !important;
        }
        [class*="st-key-nav_menu_btn_"] button {
            font-size: 0.92rem !important;
            font-weight: 700 !important;
            min-height: 2.75rem !important;
            border-radius: 12px !important;
        }
        .st-key-nav_brand_home button {
            background: rgba(99,102,241,0.08) !important;
            border: 1px solid rgba(129,140,248,0.2) !important;
            color: #1c1528 !important;
            font-weight: 800 !important;
            font-size: 0.88rem !important;
            letter-spacing: -0.02em !important;
            text-align: left !important;
            padding: 0.45rem 0.65rem !important;
            justify-content: flex-start !important;
            border-radius: 12px !important;
            min-height: 2.65rem !important;
        }
        .st-key-nav_brand_home button:hover {
            color: #4f46e5 !important;
            background: rgba(99,102,241,0.14) !important;
        }
        [class*="st-key-nav_menu_btn_"] button[kind="primary"] {
            background: var(--vc-gradient) !important;
            border: none !important;
            color: #fff !important;
            box-shadow: 0 2px 14px var(--vc-glow) !important;
        }
        [class*="st-key-nav_menu_btn_"] button[kind="secondary"] {
            background: rgba(99,102,241,0.06) !important;
            border: 1px solid rgba(99,102,241,0.12) !important;
            color: #52525b !important;
        }
        .st-key-nav_brand_home {
            position: relative;
            z-index: 201;
        }
        .vc-beta-banner {
            pointer-events: none;
        }
        .vc-beta-banner * {
            pointer-events: none;
        }
        .vc-header-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }
        .vc-header-logo {
            width: 40px; height: 40px;
            border-radius: 11px;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.15rem;
            box-shadow: 0 4px 14px var(--vc-glow);
            flex-shrink: 0;
        }
        .vc-header-titles {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .vc-header-name {
            display: block;
            font-size: 0.92rem;
            font-weight: 800;
            color: #fafafa !important;
            letter-spacing: -0.03em;
            line-height: 1.2;
        }
        .vc-header-tag {
            display: block;
            font-size: 0.68rem;
            color: #a1a1aa !important;
            font-weight: 500;
        }

        /* Segmented nav (Simply Sing / iOS style) */
        .st-key-nav_segment [data-testid="stSegmentedControl"],
        .st-key-nav_segment [role="radiogroup"] {
            background: var(--vc-card) !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: 12px !important;
            padding: 3px !important;
            gap: 2px !important;
        }
        .st-key-nav_segment button,
        .st-key-nav_segment [role="radio"] {
            color: var(--vc-muted) !important;
            font-weight: 600 !important;
            font-size: 0.78rem !important;
            border-radius: 9px !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0.35rem 0.25rem !important;
        }
        .st-key-nav_segment button[aria-checked="true"],
        .st-key-nav_segment button[data-checked="true"],
        .st-key-nav_segment [role="radio"][aria-checked="true"] {
            background: var(--vc-gradient) !important;
            color: #fff !important;
            box-shadow: 0 2px 8px var(--vc-glow) !important;
        }
        .st-key-nav_segment button:hover:not([aria-checked="true"]) {
            color: var(--vc-text) !important;
            background: rgba(255,255,255,0.05) !important;
        }

        /* Auth popover (top-right) */
        .st-key-top_auth_popover,
        .st-key-top_auth_user {
            margin-left: auto;
            max-width: 200px;
        }
        .st-key-top_auth_popover > div > button,
        .st-key-top_auth_user > div > button {
            background: linear-gradient(135deg, rgba(99,102,241,0.35), rgba(168,85,247,0.25)) !important;
            color: #f5f3ff !important;
            border: 1px solid rgba(167,139,250,0.45) !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.8rem !important;
            padding: 0.48rem 0.75rem !important;
            min-height: 2.5rem !important;
            box-shadow: 0 2px 12px rgba(99,102,241,0.2) !important;
            filter: none !important;
        }
        .st-key-top_auth_popover > div > button:hover,
        .st-key-top_auth_user > div > button:hover {
            border-color: #a78bfa !important;
            background: linear-gradient(135deg, rgba(99,102,241,0.5), rgba(168,85,247,0.35)) !important;
            color: #fff !important;
        }
        .st-key-top_auth_popover .stButton > button,
        .st-key-top_auth_user .stButton > button {
            background: var(--vc-card) !important;
            color: var(--vc-text) !important;
            border: 1px solid var(--vc-border) !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: var(--vc-surface) !important;
            border-right: 1px solid var(--vc-border) !important;
        }
        [data-testid="stSidebar"] * {
            color: #e4e4e7;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #d4d4d8 !important;
        }
        .vc-sidebar-title {
            color: #fafafa !important;
            font-weight: 800;
            font-size: 0.75rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 1rem;
        }
        .vc-sidebar-label {
            color: #71717a !important;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: 0 0 0.35rem;
        }
        .vc-sidebar-hint {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius);
            padding: 1rem;
            font-size: 0.88rem;
            color: var(--vc-muted);
            line-height: 1.65;
        }
        .vc-sidebar-hint b { color: var(--vc-text); }
        [data-testid="stSidebar"] .stButton > button {
            background: var(--vc-card) !important;
            color: #e4e4e7 !important;
            border: 1px solid var(--vc-border) !important;
        }

        /* 곡 제목 · 유튜브 가이드 안내 */
        .vc-guide-box {
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%);
            border: 1px solid rgba(99,102,241,0.18);
            border-radius: 12px;
            padding: 0.85rem 0.9rem;
            margin-bottom: 0.65rem;
            font-size: 0.82rem;
            line-height: 1.55;
        }
        .vc-guide-title {
            margin: 0 0 0.4rem;
            font-weight: 700;
            color: #4338ca !important;
            font-size: 0.84rem;
        }
        .vc-guide-body {
            margin: 0 0 0.5rem;
            color: #52525b !important;
        }
        .vc-guide-body b { color: #1c1528 !important; }
        .vc-guide-steps {
            margin: 0 0 0.25rem;
            font-size: 0.75rem;
            color: #6366f1 !important;
        }
        .vc-guide-list {
            margin: 0 0 0.5rem;
            padding-left: 1.1rem;
            color: #3f3f46 !important;
        }
        .vc-guide-list li { margin-bottom: 0.2rem; }
        .vc-guide-ex {
            color: #71717a !important;
            font-size: 0.75rem;
        }
        .vc-guide-note {
            margin: 0;
            font-size: 0.72rem;
            color: #71717a !important;
        }

        /* page-specific */
        .vc-hero-main {
            position: relative;
            padding: 2.75rem 2rem;
            margin-bottom: 1.25rem;
            border-radius: var(--vc-radius-lg);
            background:
                radial-gradient(ellipse 80% 60% at 20% 0%, rgba(99,102,241,0.28), transparent),
                radial-gradient(ellipse 60% 50% at 90% 20%, rgba(168,85,247,0.18), transparent),
                linear-gradient(160deg, #ddd6fe 0%, #ede9fe 42%, #f5f3ff 100%);
            border: 1px solid rgba(99,102,241,0.28);
            box-shadow: 0 8px 32px rgba(99,102,241,0.12);
            overflow: hidden;
            animation: vc-fade-in 0.5s ease-out;
        }
        @keyframes vc-fade-in {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .vc-hero-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.25rem;
        }
        .vc-hero-pill {
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.1);
            color: #4f46e5;
            border: 1px solid rgba(99,102,241,0.18);
        }
        .vc-hero-pill-live {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .vc-live-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 6px #22c55e;
            animation: vc-pulse 2s infinite;
        }
        @keyframes vc-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .vc-hero-h1 {
            font-size: clamp(2.1rem, 6vw, 3.4rem);
            font-weight: 900;
            letter-spacing: -0.04em;
            line-height: 1.08;
            color: #1c1528 !important;
            margin: 0 0 1rem;
        }
        .vc-gradient-text {
            background: var(--vc-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .vc-hero-lead {
            font-size: clamp(0.95rem, 2.5vw, 1.08rem);
            color: #6e667d !important;
            line-height: 1.7;
            max-width: 580px;
            margin: 0 0 1.75rem;
        }
        .vc-hero-lead b {
            color: #4338ca !important;
            font-weight: 700;
        }
        .vc-section-eyebrow {
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            color: #6366f1 !important;
            margin: 2rem 0 0.5rem;
        }
        .vc-trust-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            padding-top: 1.25rem;
            border-top: 1px solid rgba(99,102,241,0.14);
        }
        @media (max-width: 640px) {
            .vc-trust-row { grid-template-columns: repeat(2, 1fr); }
            .vc-hero-main { padding: 1.75rem 1.25rem; }
        }
        .vc-trust-item {
            text-align: center;
        }
        .vc-trust-item strong {
            display: block;
            font-size: 1.5rem;
            font-weight: 800;
            color: #4338ca !important;
        }
        .vc-trust-item span {
            font-size: 0.72rem;
            color: #6e667d !important;
            font-weight: 500;
        }

        /* Landing sections */
        .vc-section-h2 {
            font-size: clamp(1.3rem, 4vw, 1.75rem);
            font-weight: 800;
            color: #1c1528 !important;
            letter-spacing: -0.03em;
            margin: 0 0 1.25rem;
        }
        .vc-section-sub {
            color: #52525b !important;
            font-size: 0.95rem;
            line-height: 1.65;
            margin: -0.5rem 0 1.5rem;
        }
        .vc-pain-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.65rem;
            margin-bottom: 0.75rem;
        }
        @media (max-width: 768px) {
            .vc-pain-grid { grid-template-columns: 1fr; }
        }
        .vc-pain-card {
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%);
            border: 1px solid rgba(99,102,241,0.18);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            font-size: 0.88rem;
            color: #3f3f46 !important;
            line-height: 1.5;
        }
        .vc-tech-card-accent {
            border-color: rgba(99,102,241,0.35) !important;
            background: linear-gradient(135deg, #ede9fe 0%, #faf9fd 100%) !important;
        }
        .vc-tech-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.85rem;
            margin-bottom: 2rem;
        }
        @media (max-width: 640px) {
            .vc-tech-grid { grid-template-columns: 1fr; }
        }
        .vc-tech-card {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius);
            padding: 1.25rem;
            transition: border-color 0.2s, transform 0.2s;
        }
        .vc-tech-card:hover {
            border-color: #3f3f46;
            transform: translateY(-2px);
        }
        .vc-tech-icon { font-size: 1.5rem; display: block; margin-bottom: 0.5rem; }
        .vc-tech-card h3 {
            margin: 0 0 0.4rem;
            font-size: 1rem;
            font-weight: 700;
            color: #1c1528 !important;
        }
        .vc-tech-card p {
            margin: 0;
            font-size: 0.85rem;
            color: #52525b !important;
            line-height: 1.55;
        }
        .vc-steps-row {
            display: flex;
            align-items: stretch;
            gap: 0.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .vc-step-card {
            flex: 1;
            min-width: 140px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius);
            padding: 1.15rem;
        }
        .vc-step-num {
            font-size: 0.72rem;
            font-weight: 800;
            color: var(--vc-accent) !important;
            letter-spacing: 0.06em;
        }
        .vc-step-card strong {
            display: block;
            margin: 0.35rem 0 0.2rem;
            color: #1c1528 !important;
            font-size: 0.95rem;
        }
        .vc-step-card small { color: #6e667d !important; font-size: 0.78rem; }
        .vc-step-arrow {
            display: flex;
            align-items: center;
            color: #52525b;
            font-size: 1.2rem;
            padding: 0 0.15rem;
        }
        @media (max-width: 640px) { .vc-step-arrow { display: none; } }

        .vc-featured-card {
            background: linear-gradient(135deg, #ddd6fe 0%, #ede9fe 50%, #f5f3ff 100%);
            border: 1px solid rgba(99,102,241,0.28);
            border-radius: var(--vc-radius-lg);
            padding: 1.5rem 1.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 6px 24px rgba(99,102,241,0.1);
        }
        .vc-featured-tag {
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #6366f1 !important;
        }
        .vc-featured-card h3 {
            margin: 0.5rem 0 0.4rem;
            font-size: 1.15rem;
            color: #1c1528 !important;
        }
        .vc-featured-card p {
            margin: 0;
            color: #52525b !important;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        .vc-testimonial {
            margin: 2rem 0;
            padding: 1.25rem 1.5rem;
            border-left: 3px solid var(--vc-accent);
            background: linear-gradient(90deg, #f3f0ff 0%, #faf9fd 100%);
            border-radius: 0 var(--vc-radius) var(--vc-radius) 0;
        }
        .vc-testimonial p {
            margin: 0;
            color: #3f3f46 !important;
            line-height: 1.65;
            font-size: 0.95rem;
        }
        .vc-testimonial cite {
            display: block;
            margin-top: 0.5rem;
            font-size: 0.78rem;
            color: #71717a !important;
            font-style: normal;
        }
        .vc-footer {
            margin-top: 2.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--vc-border);
            text-align: center;
        }
        .vc-footer p { margin: 0; color: #71717a !important; font-size: 0.85rem; }
        .vc-footer-sub { margin-top: 0.3rem !important; font-size: 0.75rem !important; }

        /* ── Analysis page ── */
        .vc-page-head {
            margin-bottom: 1.25rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--vc-border);
        }
        .vc-page-badge {
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #c4b5fd !important;
            background: rgba(99,102,241,0.15);
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
        }
        .vc-page-title {
            font-size: clamp(1.35rem, 4vw, 1.65rem);
            font-weight: 800;
            color: #fafafa !important;
            margin: 0.65rem 0 0.35rem;
            letter-spacing: -0.03em;
        }
        .vc-page-desc {
            margin: 0;
            color: #a1a1aa !important;
            font-size: 0.92rem;
        }
        .vc-upload-zone {
            background: var(--vc-card);
            border: 1px dashed rgba(129,140,248,0.35);
            border-radius: var(--vc-radius-lg);
            padding: 1.25rem 1.5rem;
            margin-bottom: 0.75rem;
        }
        .vc-upload-title {
            margin: 0;
            font-weight: 700;
            font-size: 1rem;
            color: #fafafa !important;
        }
        .vc-upload-desc {
            margin: 0.25rem 0 0;
            font-size: 0.82rem;
            color: #71717a !important;
        }

        /* ── Buttons ── */
        .st-key-btn_start_analysis .stButton > button,
        .st-key-landing_cta .stButton > button,
        .st-key-landing_cta_bottom .stButton > button {
            background: var(--vc-gradient) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.75rem 1.25rem !important;
            box-shadow: 0 4px 20px var(--vc-glow) !important;
            transition: filter 0.15s, transform 0.15s !important;
        }
        .st-key-btn_start_analysis .stButton > button:hover,
        .st-key-landing_cta .stButton > button:hover,
        .st-key-landing_cta_bottom .stButton > button:hover {
            filter: brightness(1.1) !important;
            transform: translateY(-1px) !important;
        }
        .st-key-landing_my .stButton > button {
            background: var(--vc-card) !important;
            color: var(--vc-muted) !important;
            border: 1px solid var(--vc-border) !important;
            font-weight: 600 !important;
        }
        .st-key-landing_my .stButton > button:hover {
            color: var(--vc-text) !important;
            border-color: var(--vc-accent) !important;
        }

        /* ── Login (카카오 · 인스타 스타일) ── */
        .vc-login-wrap { max-width: 420px; margin: 2rem auto 1rem; }
        .vc-login-hero {
            text-align: center;
            padding: 1.5rem 1rem 1.25rem;
            max-width: 400px;
            margin: 0 auto;
        }
        .vc-login-hero-compact {
            padding: 0.75rem 0.5rem 1rem;
        }
        .vc-login-logo-ring {
            width: 72px;
            height: 72px;
            margin: 0 auto 1rem;
            border-radius: 22px;
            background: var(--vc-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            box-shadow: 0 8px 32px var(--vc-glow);
        }
        .vc-login-hero-compact .vc-login-logo-ring {
            width: 56px;
            height: 56px;
            font-size: 1.5rem;
            border-radius: 18px;
            margin-bottom: 0.75rem;
        }
        .vc-login-brand-title {
            margin: 0;
            font-size: clamp(1.35rem, 5vw, 1.75rem);
            font-weight: 800;
            color: #fafafa !important;
            letter-spacing: -0.03em;
            line-height: 1.25;
        }
        .vc-login-hero-compact .vc-login-brand-title {
            font-size: 1.15rem;
        }
        .vc-login-brand-tag {
            margin: 0.45rem 0 0;
            font-size: 0.88rem;
            color: var(--vc-muted) !important;
            line-height: 1.5;
        }
        .vc-login-benefits {
            list-style: none;
            padding: 0;
            margin: 1.25rem 0 0;
            text-align: left;
            display: inline-block;
        }
        .vc-login-benefits li {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-size: 0.88rem;
            color: #d4d4d8 !important;
            padding: 0.35rem 0;
        }
        .vc-login-benefits li span {
            font-size: 1.1rem;
        }
        .vc-login-card-panel {
            max-width: 400px;
            margin: 0 auto 1.5rem;
            padding: 1.25rem 1.15rem 1.1rem;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 20px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.35);
        }
        .vc-login-card-marker + [data-testid="stVerticalBlockBorderWrapper"] {
            max-width: 400px !important;
            margin: 0 auto 1.25rem !important;
            background: linear-gradient(165deg, #ffffff 0%, #faf8ff 100%) !important;
            border: 1px solid rgba(99,102,241,0.16) !important;
            border-radius: 20px !important;
            box-shadow: 0 10px 32px rgba(99,102,241,0.08) !important;
            padding: 0.35rem 0.5rem !important;
        }
        .vc-login-card-marker + [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0.65rem 0.55rem 0.75rem !important;
        }
        .vc-login-card-heading {
            margin: 0 0 1rem;
            font-size: 0.95rem;
            font-weight: 700;
            color: #e4e4e7 !important;
            text-align: center;
        }
        .vc-login-footnote {
            margin: 0.85rem 0 0;
            font-size: 0.75rem;
            color: #71717a !important;
            text-align: center;
            line-height: 1.45;
        }
        .vc-auth-stack {
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
        }
        .vc-auth-divider {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.35rem 0 0.15rem;
            color: var(--vc-muted);
            font-size: 0.78rem;
        }
        .vc-auth-divider::before,
        .vc-auth-divider::after {
            content: "";
            flex: 1;
            height: 1px;
            background: var(--vc-border);
        }
        .vc-auth-divider span {
            flex-shrink: 0;
            padding: 0 0.15rem;
        }
        .vc-auth-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.45rem;
            width: 100%;
            min-height: 48px;
            padding: 0.75rem 1rem;
            margin-bottom: 0;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.95rem;
            text-align: center;
            text-decoration: none;
            box-sizing: border-box;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }
        .vc-auth-btn:active {
            transform: scale(0.98);
        }
        .vc-auth-btn-icon {
            font-size: 1.05rem;
            line-height: 1;
        }
        .vc-auth-g-icon {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 0.95rem;
            width: 1.25rem;
            text-align: center;
        }
        .vc-auth-google {
            background: #fff;
            color: #1f2937;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .vc-auth-kakao {
            background: var(--vc-kakao);
            color: var(--vc-kakao-text);
            border: none;
            box-shadow: 0 2px 8px rgba(254,229,0,0.25);
        }
        .vc-auth-sm {
            min-height: 44px !important;
            padding: 0.6rem 0.85rem !important;
            font-size: 0.88rem !important;
        }
        .vc-auth-disabled {
            background: var(--vc-card);
            color: var(--vc-muted);
            border: 1px solid var(--vc-border);
            opacity: 0.65;
            cursor: not-allowed;
        }
        [class*="st-key-page_login_demo"] button,
        [class*="st-key-mypage_gate_demo"] button,
        [class*="st-key-landing_auth_demo"] button,
        [class*="st-key-auth_pop_demo"] button {
            min-height: 48px !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            margin-top: 0.25rem !important;
        }
        [class*="st-key-page_login_demo"] button {
            background: var(--vc-gradient) !important;
            border: none !important;
            color: #fff !important;
        }
        [class*="st-key-mypage_gate_demo"] button {
            background: var(--vc-gradient) !important;
            border: none !important;
            color: #fff !important;
        }

        /* ── Alerts & info (dark-friendly) ── */
        [data-testid="stAlert"],
        .stAlert {
            background: rgba(99,102,241,0.1) !important;
            border: 1px solid rgba(99,102,241,0.25) !important;
            border-radius: 12px !important;
            color: #c7d2fe !important;
        }
        [data-testid="stAlert"] p,
        .stAlert p { color: #c7d2fe !important; }

        /* ── Widgets ── */
        [data-testid="stFileUploader"] section {
            border: 2px dashed var(--vc-border) !important;
            background: var(--vc-surface) !important;
            border-radius: var(--vc-radius) !important;
        }
        [data-testid="stFileUploader"] section:hover {
            border-color: rgba(129,140,248,0.5) !important;
        }
        [data-testid="stFileUploader"] button {
            background: var(--vc-gradient) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMetric"] {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius);
            padding: 0.5rem;
        }
        div[data-testid="stMetric"] label { color: var(--vc-muted) !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--vc-text) !important; }

        .stTabs [data-baseweb="tab-list"] {
            background: var(--vc-surface);
            border: 1px solid var(--vc-border);
            border-radius: 12px;
        }
        .stTabs [aria-selected="true"] {
            background: var(--vc-gradient) !important;
            color: #fff !important;
        }
        .stProgress > div > div {
            background: var(--vc-gradient) !important;
        }

        .vc-user-chip {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 10px;
            padding: 0.65rem 0.85rem;
            color: var(--vc-text);
        }
        .tip-box {
            background: rgba(99,102,241,0.1);
            border: 1px solid rgba(99,102,241,0.25);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            color: #c7d2fe !important;
            font-size: 0.85rem;
        }
        .score-card, .vc-feature, .vc-stepper, .vc-info-box, .action-card {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: var(--vc-radius);
        }
        .vc-stepper {
            padding: 1rem 1.15rem;
            margin-top: 0.5rem;
        }
        .vc-step-msg {
            margin: 0 0 0.75rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: #e4e4e7 !important;
        }
        .vc-step {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.35rem 0;
            font-size: 0.85rem;
            color: #71717a !important;
        }
        .vc-step-done { color: #a1a1aa !important; }
        .vc-step-active { color: #c4b5fd !important; font-weight: 600; }
        .vc-step-pending { color: #52525b !important; }
        .vc-step-icon { width: 1.1rem; text-align: center; }

        .vc-analyzing-panel {
            background: linear-gradient(135deg, rgba(30,27,75,0.7) 0%, var(--vc-card) 100%);
            border: 1px solid rgba(129,140,248,0.3);
            border-radius: var(--vc-radius-lg);
            padding: 1.35rem 1.5rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        .vc-analyzing-title {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: #fafafa !important;
        }
        .vc-analyzing-sub {
            margin: 0.35rem 0 0;
            font-size: 0.82rem;
            color: #71717a !important;
        }

        /* 카카오톡·인스타 친화 채팅 카드 */
        .vc-chat-card {
            display: flex;
            gap: 0.75rem;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1rem;
            max-width: 520px;
        }
        .vc-login-card { margin: 0 auto 1rem; max-width: 480px; }
        .vc-chat-avatar {
            width: 42px; height: 42px;
            border-radius: 50%;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        .vc-chat-body { flex: 1; min-width: 0; }
        .vc-chat-name {
            margin: 0 0 0.25rem;
            font-size: 0.78rem;
            font-weight: 700;
            color: #6366f1 !important;
        }
        .vc-chat-msg {
            margin: 0 0 0.65rem;
            font-size: 0.92rem;
            color: #3f3f46 !important;
            line-height: 1.55;
        }
        .vc-chat-progress {
            height: 6px;
            background: #27272a;
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 0.35rem;
        }
        .vc-chat-progress-fill {
            height: 100%;
            background: var(--vc-gradient);
            border-radius: 999px;
            transition: width 0.3s ease;
        }
        .vc-chat-pct {
            margin: 0 0 0.65rem;
            font-size: 0.75rem;
            font-weight: 700;
            color: #c4b5fd !important;
        }
        .vc-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
        }
        .vc-chip {
            font-size: 0.68rem;
            padding: 0.25rem 0.5rem;
            border-radius: 999px;
            border: 1px solid var(--vc-border);
            white-space: nowrap;
        }
        .vc-chip-done {
            background: rgba(99,102,241,0.15);
            color: #c4b5fd !important;
            border-color: rgba(129,140,248,0.3);
        }
        .vc-chip-active {
            background: var(--vc-gradient);
            color: #fff !important;
            border-color: transparent;
            font-weight: 600;
        }
        .vc-chip-pending {
            background: transparent;
            color: #52525b !important;
        }
        .vc-chip-tip {
            position: relative;
            cursor: help;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .vc-chip-tip:hover {
            transform: translateY(-1px);
            z-index: 20;
        }
        .vc-chip-tip::after {
            content: attr(data-tip);
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%) translateY(4px);
            opacity: 0;
            pointer-events: none;
            background: #27272a;
            color: #f4f4f5 !important;
            border: 1px solid rgba(129, 140, 248, 0.45);
            border-radius: 10px;
            padding: 0.45rem 0.6rem;
            font-size: 0.68rem;
            font-weight: 500;
            line-height: 1.45;
            white-space: normal;
            width: max-content;
            max-width: 240px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
            transition: opacity 0.15s ease, transform 0.15s ease;
            z-index: 9999;
        }
        .vc-chip-tip:hover::after {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        .vc-loading-banner {
            position: fixed;
            bottom: 1.25rem;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 0.55rem;
            padding: 0.55rem 1.05rem;
            background: rgba(24, 24, 27, 0.94);
            border: 1px solid rgba(129, 140, 248, 0.42);
            border-radius: 999px;
            color: #e4e4e7 !important;
            font-size: 0.82rem;
            font-weight: 600;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
            pointer-events: none;
        }
        .vc-loading-spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(129, 140, 248, 0.28);
            border-top-color: #818cf8;
            border-radius: 50%;
            animation: vc-spin 0.7s linear infinite;
            flex-shrink: 0;
        }
        @keyframes vc-spin {
            to { transform: rotate(360deg); }
        }
        .vc-msg-user-marker { display: none !important; }

        .vc-settings-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.5rem 0 0.35rem;
        }
        .vc-settings-pill {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            color: #d4d4d8 !important;
        }
        .vc-sidebar-hint-text {
            font-size: 0.78rem;
            color: #71717a !important;
            margin: 0 0 1rem;
        }
        .vc-gate-hint {
            font-size: 0.85rem;
            color: #a1a1aa !important;
            text-align: center;
            padding-top: 0.5rem;
            line-height: 1.5;
        }
        .vc-upload-card {
            text-align: center;
            background: var(--vc-card);
            border: 2px dashed rgba(129,140,248,0.35);
            border-radius: 20px;
            padding: 1.75rem 1rem;
            margin-bottom: 0.75rem;
        }
        .vc-upload-emoji { font-size: 2rem; margin: 0; }
        .vc-upload-title {
            margin: 0.35rem 0 0;
            font-weight: 700;
            font-size: 1.05rem;
            color: #fafafa !important;
        }
        .vc-upload-desc {
            margin: 0.25rem 0 0;
            font-size: 0.82rem;
            color: #71717a !important;
        }
        .vc-upload-card-inline {
            margin-bottom: 0.65rem;
        }
        /* ── 실시간 녹음 (히어로 + 위젯) ── */
        .vc-new-analysis-head {
            margin-bottom: 0.85rem;
        }
        .vc-new-analysis-title {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            color: #1c1528 !important;
        }
        .vc-new-analysis-desc {
            margin: 0.2rem 0 0;
            font-size: 0.82rem;
            color: #6e667d !important;
        }
        .vc-record-hero {
            padding: 1.25rem 1.15rem;
            margin-bottom: 0.85rem;
            border-radius: 18px;
            background:
                radial-gradient(ellipse 70% 80% at 10% 0%, rgba(99,102,241,0.28), transparent),
                linear-gradient(155deg, #ddd6fe 0%, #ede9fe 45%, #f5f3ff 100%);
            border: 1px solid rgba(99,102,241,0.28);
            box-shadow: 0 8px 28px rgba(99,102,241,0.12);
        }
        .vc-record-hero-badge {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            padding: 0.22rem 0.55rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.18);
            color: #4338ca !important;
            margin-bottom: 0.45rem;
        }
        .vc-record-hero-title {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 900;
            color: #1c1528 !important;
            letter-spacing: -0.02em;
        }
        .vc-record-hero-lead {
            margin: 0.45rem 0 0.75rem;
            font-size: 0.88rem;
            color: #52525b !important;
            line-height: 1.55;
        }
        .vc-record-hero-lead b { color: #4338ca !important; }
        .vc-record-steps {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.35rem;
        }
        .vc-record-step {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.85);
            color: #4338ca !important;
            border: 1px solid rgba(99,102,241,0.2);
        }
        .vc-record-step-arrow {
            font-size: 0.75rem;
            color: #6366f1 !important;
            font-weight: 700;
        }
        .vc-record-panel-label {
            margin: 0 0 0.35rem;
            font-size: 0.88rem;
            font-weight: 700;
            color: #4338ca !important;
            text-align: center;
        }
        .vc-record-card {
            text-align: center;
            background: linear-gradient(145deg, #ffffff 0%, #ede9fe 100%);
            border: 2px solid rgba(99,102,241,0.22);
            border-radius: 20px;
            padding: 1.35rem 1rem 1rem;
            margin-bottom: 0.65rem;
        }
        .vc-record-title {
            margin: 0;
            font-weight: 800;
            font-size: 1.05rem;
            color: #1c1528 !important;
        }
        .vc-record-desc {
            margin: 0.35rem 0 0;
            font-size: 0.82rem;
            color: #52525b !important;
            line-height: 1.5;
        }
        .vc-record-hint {
            margin: 0.5rem 0 0.25rem;
            font-size: 0.78rem;
            color: #6e667d !important;
            text-align: center;
            line-height: 1.5;
        }
        .vc-record-hint b { color: #4338ca !important; }
        .vc-record-done {
            margin: 0.5rem 0 0.25rem;
            font-size: 0.82rem;
            color: #4338ca !important;
            text-align: center;
            font-weight: 600;
        }
        .vc-record-done b { color: #1c1528 !important; }
        [data-testid="stAudioInput"] {
            margin: 0.25rem 0 0.5rem;
            padding: 0.85rem 0.75rem;
            border-radius: 16px;
            background: linear-gradient(145deg, #ffffff 0%, #faf8ff 100%);
            border: 2px dashed rgba(99,102,241,0.35);
        }
        [data-testid="stAudioInput"] label,
        [data-testid="stAudioInput"] [data-testid="stWidgetLabel"] p {
            color: #1c1528 !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            text-align: center !important;
        }
        [data-testid="stAudioInput"] button {
            display: block !important;
            margin: 0.5rem auto 0 !important;
            min-width: 220px !important;
            background: var(--vc-gradient) !important;
            border: none !important;
            color: #fff !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            min-height: 3.25rem !important;
            box-shadow: 0 6px 22px var(--vc-glow) !important;
        }
        [data-testid="stAudioInput"] button:hover {
            filter: brightness(1.06) !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stAudioInput"]) {
            border-color: rgba(99,102,241,0.22) !important;
            background: #ffffff !important;
            border-radius: 16px !important;
            padding: 0.5rem !important;
            margin-bottom: 0.65rem !important;
        }
        .vc-upload-hint {
            display: flex;
            align-items: flex-start;
            gap: 0.65rem;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0 1rem;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, #f3f0ff 100%);
            border: 1px solid rgba(99,102,241,0.2);
        }
        .vc-upload-hint-icon { font-size: 1.1rem; line-height: 1.4; opacity: 0.9; }
        .vc-upload-hint-text {
            margin: 0;
            font-size: 0.88rem;
            color: #3f3f46 !important;
            line-height: 1.5;
        }
        .vc-upload-hint-text span {
            font-size: 0.8rem;
            color: #6e667d !important;
        }
        .vc-welcome-lead {
            font-size: 0.82rem;
            color: #6366f1 !important;
            font-weight: 700;
            margin: 0.5rem 0 0.65rem;
            letter-spacing: 0.01em;
        }
        .vc-feature-grid {
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
            margin-bottom: 1rem;
        }
        .vc-feature-card {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%);
            border: 1px solid rgba(99,102,241,0.16);
        }
        .vc-feature-icon {
            font-size: 1.25rem;
            line-height: 1;
            flex-shrink: 0;
            margin-top: 0.1rem;
        }
        .vc-feature-title {
            margin: 0 0 0.2rem;
            font-size: 0.9rem;
            font-weight: 700;
            color: #1c1528 !important;
        }
        .vc-feature-desc {
            margin: 0;
            font-size: 0.8rem;
            color: #52525b !important;
            line-height: 1.45;
        }
        .vc-tip-soft {
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%);
            border: 1px solid rgba(99,102,241,0.16);
            height: 100%;
        }
        .vc-tip-soft-title {
            margin: 0 0 0.35rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: #4338ca !important;
        }
        .vc-tip-soft-body {
            margin: 0;
            font-size: 0.78rem;
            color: #52525b !important;
            line-height: 1.5;
        }
        .vc-analyze-stage {
            position: relative;
            z-index: 995;
            min-height: 0;
            padding: 0;
        }
        .stApp:has(#vc-analyzing-anchor)::before {
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(9, 9, 11, 0.82);
            z-index: 900;
            pointer-events: none;
        }
        .st-key-vc_analyze_panel {
            position: sticky;
            top: 0.35rem;
            z-index: 960 !important;
            pointer-events: auto;
            margin-bottom: 1rem;
        }
        .st-key-vc_analyze_panel [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
        }
        .vc-analyze-panel-head {
            text-align: left;
            margin-bottom: 0.35rem;
            padding: 0 0.15rem;
        }
        .vc-analyze-panel-title {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 800;
            color: #fafafa !important;
        }
        .vc-analyze-panel-desc {
            margin: 0.2rem 0 0;
            font-size: 0.8rem;
            color: #a1a1aa !important;
        }
        .st-key-vc_analyze_panel .vc-analyze-progress-card,
        .st-key-vc_analyze_panel .vc-chat-card {
            background: #18181b !important;
            filter: none !important;
            opacity: 1 !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55);
            border: 1px solid rgba(129, 140, 248, 0.38) !important;
            max-width: 100% !important;
            margin: 0.35rem 0 0 !important;
        }
        .st-key-vc_analyze_panel [data-testid="stHorizontalBlock"],
        .st-key-vc_analyze_panel .st-key-btn_cancel_analysis_main,
        .st-key-vc_analyze_panel .vc-chip-row {
            position: relative;
            z-index: 961;
            pointer-events: auto;
        }
        .vc-analyze-stage::before {
            display: none;
        }
        .st-key-btn_cancel_analysis_main {
            position: relative;
            z-index: 2;
            margin-top: 0.35rem;
        }
        .st-key-btn_cancel_analysis_main button {
            background: var(--vc-card) !important;
            color: #e4e4e7 !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            min-height: 2.45rem !important;
        }
        .st-key-btn_cancel_analysis_main button:hover {
            border-color: rgba(129,140,248,0.45) !important;
            color: #fafafa !important;
        }
        .vc-start-hint {
            font-size: 0.82rem;
            color: #71717a !important;
            text-align: center;
            margin: 0.75rem 0 0.35rem;
        }
        .vc-analyzing-header {
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .vc-analyzing-mode {
            font-size: 0.82rem;
            color: #a78bfa !important;
            margin: 0.25rem 0 0;
        }
        .vc-chat-eta {
            font-size: 0.78rem;
            color: #a78bfa !important;
            margin: 0.15rem 0 0.35rem;
            font-weight: 600;
        }
        .vc-chat-mode-pill {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 600;
            padding: 0.12rem 0.45rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.2);
            color: #c4b5fd !important;
            vertical-align: middle;
            margin-left: 0.35rem;
        }
        /* 베타 배너 */
        .vc-beta-banner {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            flex-wrap: wrap;
            padding: 0.45rem 0.85rem;
            margin-bottom: 0.75rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(99,102,241,0.14) 0%, rgba(237,233,254,0.9) 100%);
            border: 1px solid rgba(99,102,241,0.24);
        }
        .vc-beta-tag {
            font-size: 0.65rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            background: var(--vc-gradient);
            color: #fff !important;
        }
        .vc-beta-text {
            font-size: 0.78rem;
            color: #52525b !important;
        }
        /* 홈 — 체험 CTA 배너 (소셜 로그인은 상단 팝오버) */
        .vc-landing-trial-banner {
            padding: 1rem 1.15rem;
            margin-bottom: 0.55rem;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(99,102,241,0.2) 0%, #ddd6fe 45%, rgba(168,85,247,0.14) 100%);
            border: 1px solid rgba(99,102,241,0.32);
            box-shadow: 0 4px 20px rgba(99,102,241,0.14);
        }
        .vc-landing-trial-tag {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.2);
            color: #4338ca !important;
            margin-bottom: 0.4rem;
        }
        .vc-landing-trial-title {
            margin: 0;
            font-size: 1rem;
            font-weight: 700;
            color: #1c1528 !important;
            line-height: 1.35;
        }
        .vc-landing-trial-sub {
            margin: 0.35rem 0 0;
            font-size: 0.78rem;
            color: #52525b !important;
            line-height: 1.45;
        }
        .vc-landing-trial-sub b {
            color: #6366f1 !important;
            font-weight: 600;
        }
        .st-key-landing_auth_demo button {
            background: var(--vc-gradient) !important;
            border: none !important;
            color: #fff !important;
            font-weight: 700 !important;
            min-height: 48px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px var(--vc-glow) !important;
            margin-top: 0.15rem !important;
        }
        /* 분석 완료 히어로 배너 */
        .vc-result-hero {
            position: relative;
            overflow: hidden;
            border-radius: 16px;
            margin-bottom: 0.75rem;
            border: 1px solid rgba(129,140,248,0.35);
            background: linear-gradient(135deg, rgba(99,102,241,0.22) 0%, rgba(15,15,20,0.95) 55%, rgba(168,85,247,0.12) 100%);
        }
        .vc-result-hero-glow {
            position: absolute;
            top: -40%;
            right: -10%;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(168,85,247,0.25), transparent 70%);
            pointer-events: none;
        }
        .vc-result-hero-inner {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.1rem 1.25rem;
            flex-wrap: wrap;
        }
        .vc-result-hero-left { flex: 1; min-width: 200px; }
        .vc-result-badge {
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: rgba(34,197,94,0.15);
            color: #4ade80 !important;
            margin-bottom: 0.35rem;
        }
        .vc-result-hero-title {
            margin: 0;
            font-size: 1.15rem;
            font-weight: 800;
            color: #fafafa !important;
        }
        .vc-result-hero-strength {
            margin: 0.35rem 0 0;
            font-size: 0.82rem;
            color: #d4d4d8 !important;
        }
        .vc-result-hero-focus {
            margin: 0.25rem 0 0;
            font-size: 0.75rem;
            color: #a78bfa !important;
            font-weight: 600;
        }
        .vc-result-hero-score {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 88px;
            padding: 0.65rem 1rem;
            border-radius: 14px;
            background: rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .vc-result-grade {
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
        }
        .vc-result-overall {
            font-size: 2rem;
            font-weight: 900;
            line-height: 1.1;
            color: #fafafa !important;
        }
        .vc-result-overall-label {
            font-size: 0.62rem;
            color: #71717a !important;
        }
        @media (max-width: 768px) {
            .vc-chat-card { max-width: 100%; border-radius: 16px; }
            .vc-chip { font-size: 0.62rem; }
            .vc-settings-pill-row { justify-content: center; }
            .vc-sidebar-hint-text { text-align: center; }
        }

        /* 분석 설정 다이얼로그 (모바일) */
        [data-testid="stDialog"] > div {
            background: var(--vc-surface) !important;
            border: 1px solid var(--vc-border) !important;
            border-radius: 16px !important;
        }
        [data-testid="stDialog"] h2 {
            color: #fafafa !important;
            font-size: 1.05rem !important;
        }
        @media (max-width: 768px) {
            [data-testid="stDialog"] > div {
                width: min(96vw, 480px) !important;
                max-height: 88vh !important;
                overflow-y: auto !important;
            }
        }
        .st-key-btn_open_analysis_settings button,
        .st-key-btn_open_analysis_settings_results button {
            background: var(--vc-card) !important;
            color: #c4b5fd !important;
            border: 1px solid rgba(129,140,248,0.45) !important;
            font-weight: 700 !important;
            min-height: 2.75rem !important;
        }

        /* Instagram DM 코치 채팅 */
        .vc-dm-header {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 16px 16px 0 0;
            padding: 0.85rem 1rem;
            margin-bottom: 0;
        }
        .vc-dm-header-inner {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .vc-dm-avatar {
            width: 44px; height: 44px;
            border-radius: 50%;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3rem;
        }
        .vc-dm-title {
            margin: 0;
            font-weight: 700;
            font-size: 0.95rem;
            color: #fafafa !important;
        }
        .vc-dm-status {
            margin: 0.1rem 0 0;
            font-size: 0.72rem;
            color: #22c55e !important;
        }
        .vc-score-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.75rem 0;
            margin-bottom: 0.5rem;
        }
        .vc-score-chip {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            min-width: 64px;
            padding: 0.45rem 0.75rem;
            border-radius: 12px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            font-weight: 800;
            font-size: 1.1rem;
            color: #fafafa !important;
        }
        .vc-score-chip small {
            font-size: 0.62rem;
            font-weight: 600;
            color: #71717a !important;
            margin-top: 0.1rem;
        }
        .vc-score-overall {
            background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(168,85,247,0.15));
            border-color: rgba(129,140,248,0.4);
        }
        .vc-dm-shell {
            border: none;
            border-radius: 0;
            overflow: hidden;
            background: transparent;
            margin-bottom: 0;
        }
        .st-key-vc_dm_panel {
            border: 1px solid var(--vc-border);
            border-radius: 16px;
            overflow: hidden;
            background: #0f0f12;
            margin-bottom: 1.25rem;
        }
        .st-key-vc_dm_panel [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        .st-key-vc_dm_panel [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
            border: none !important;
        }
        .vc-dm-header-attached {
            border-radius: 0;
            margin-bottom: 0;
            border-bottom: 1px solid var(--vc-border);
        }
        .vc-dm-thread-attached {
            border: none;
            border-radius: 0;
        }
        .vc-dm-composer {
            border: none;
            border-top: 1px solid var(--vc-border);
            border-radius: 0;
            background: #141417;
            padding: 0.5rem 0.75rem 0.75rem;
            margin-bottom: 0;
        }
        .st-key-vc_dm_panel .st-key-coach_pill_0,
        .st-key-vc_dm_panel .st-key-coach_pill_1,
        .st-key-vc_dm_panel .st-key-coach_pill_2 {
            flex: 0 1 auto;
        }
        .st-key-vc_dm_panel .st-key-coach_pill_0 [data-testid="column"],
        .st-key-vc_dm_panel .st-key-coach_pill_1 [data-testid="column"],
        .st-key-vc_dm_panel .st-key-coach_pill_2 [data-testid="column"] {
            width: auto !important;
            flex: 0 1 auto !important;
        }
        .vc-dm-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-bottom: 0.45rem;
        }
        .st-key-coach_pill_0 button,
        .st-key-coach_pill_1 button,
        .st-key-coach_pill_2 button {
            background: rgba(99,102,241,0.14) !important;
            color: #b8b0e8 !important;
            border: 1px solid rgba(129,140,248,0.28) !important;
            border-radius: 999px !important;
            font-size: 0.58rem !important;
            font-weight: 600 !important;
            padding: 0.22rem 0.45rem !important;
            min-height: 1.55rem !important;
            height: auto !important;
            line-height: 1.25 !important;
            white-space: nowrap !important;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .vc-dm-composer [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
        }
        .vc-dm-composer [data-testid="stTextInput"] input {
            background: #27272a !important;
            border: 1px solid #3f3f46 !important;
            color: #fafafa !important;
            border-radius: 22px !important;
            padding: 0.62rem 1rem !important;
            font-size: 0.88rem !important;
            min-height: 2.5rem !important;
        }
        .vc-dm-composer [data-testid="stFormSubmitButton"] button {
            border-radius: 50% !important;
            width: 2.55rem !important;
            height: 2.55rem !important;
            min-height: 2.55rem !important;
            padding: 0 !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            margin-top: 0 !important;
        }
        .vc-dm-thread {
            background: #0f0f12;
            padding: 0.85rem 0.65rem 0.75rem;
            min-height: 200px;
            max-height: 380px;
            overflow-y: auto;
            margin-bottom: 0;
        }
        .vc-bubble-row {
            display: flex;
            align-items: flex-end;
            gap: 0.45rem;
            margin-bottom: 0.65rem;
        }
        .vc-bubble-right {
            justify-content: flex-end;
            padding-left: 2.5rem;
        }
        .vc-bubble-left {
            justify-content: flex-start;
            padding-right: 2.5rem;
        }
        .vc-bubble-user {
            background: linear-gradient(135deg, #565bcf 0%, #8134af 50%, #c13584 100%);
            color: #ffffff !important;
            border-bottom-right-radius: 4px;
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(129, 52, 175, 0.35);
        }
        .vc-bubble-avatar {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.95rem;
            flex-shrink: 0;
        }
        .vc-bubble {
            max-width: 82%;
            padding: 0.65rem 0.85rem;
            border-radius: 18px;
            font-size: 0.88rem;
            line-height: 1.55;
            word-break: break-word;
        }
        .vc-bubble-coach {
            background: #27272a;
            color: #f4f4f5 !important;
            border-bottom-left-radius: 4px;
            border: 1px solid #3f3f46;
        }
        .vc-bubble-typing {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            min-width: 72px;
            padding: 0.75rem 1rem;
        }
        .vc-typing-dot {
            width: 7px; height: 7px;
            border-radius: 50%;
            background: #a1a1aa;
            animation: vc-typing-bounce 1.2s infinite ease-in-out;
        }
        .vc-typing-dot:nth-child(2) { animation-delay: 0.15s; }
        .vc-typing-dot:nth-child(3) { animation-delay: 0.3s; }
        .vc-typing-label {
            font-size: 0.72rem;
            color: #71717a !important;
            margin-left: 0.35rem;
        }
        @keyframes vc-typing-bounce {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.45; }
            30% { transform: translateY(-4px); opacity: 1; }
        }
        .vc-insight-stack {
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
            margin-bottom: 1rem;
        }
        .vc-insight-card {
            padding: 0.85rem 1rem;
            border-radius: 14px;
            border: 1px solid var(--vc-border);
            background: var(--vc-card);
        }
        .vc-insight-good-card {
            border-left: 3px solid #22c55e;
            background: linear-gradient(90deg, rgba(34,197,94,0.08), var(--vc-card) 40%);
        }
        .vc-insight-focus-card {
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            border-left: 3px solid #6366f1;
            background: linear-gradient(90deg, rgba(99,102,241,0.1), var(--vc-card) 40%);
        }
        .vc-focus-num {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px; height: 28px;
            border-radius: 50%;
            background: rgba(99,102,241,0.35);
            color: #c4b5fd !important;
            font-weight: 800;
            font-size: 0.82rem;
            flex-shrink: 0;
        }
        .vc-insight-headline {
            margin: 0 0 0.35rem;
            font-weight: 700;
            font-size: 0.92rem;
            color: #fafafa !important;
            line-height: 1.4;
        }
        .vc-insight-detail {
            margin: 0;
            font-size: 0.82rem;
            color: #a1a1aa !important;
            line-height: 1.55;
        }
        .vc-stage-native {
            margin-bottom: 0.25rem;
        }
        .vc-stage-native-label {
            margin: 0;
            font-size: 0.82rem;
            font-weight: 700;
            color: #e4e4e7 !important;
        }
        .vc-stage-native-score {
            margin: 0.15rem 0 0;
            font-size: 1.65rem;
            font-weight: 900;
            color: #fafafa !important;
            line-height: 1;
        }
        .vc-stage-native-score span {
            font-size: 0.85rem;
            font-weight: 700;
            color: #818cf8 !important;
            margin-left: 0.35rem;
        }
        /* ── 정밀 음정 패널 ── */
        .vc-precision-panel {
            margin: 0.85rem 0 1rem;
            padding: 1rem 1rem 0.9rem;
            border-radius: 16px;
            background: linear-gradient(155deg, #ede9fe 0%, #faf8ff 55%, #ffffff 100%);
            border: 1px solid rgba(99,102,241,0.18);
        }
        .vc-precision-head {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 0.35rem;
            margin-bottom: 0.75rem;
        }
        .vc-precision-title {
            margin: 0;
            font-size: 0.92rem;
            font-weight: 800;
            color: #1c1528 !important;
        }
        .vc-precision-engine {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.12);
            color: #4338ca !important;
        }
        .vc-precision-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.45rem;
        }
        .vc-precision-stat {
            text-align: center;
            padding: 0.55rem 0.25rem;
            border-radius: 12px;
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(99,102,241,0.1);
        }
        .vc-precision-val {
            display: block;
            font-size: 1.05rem;
            font-weight: 800;
            color: #4338ca !important;
            line-height: 1.2;
        }
        .vc-precision-label {
            display: block;
            margin-top: 0.2rem;
            font-size: 0.62rem;
            font-weight: 700;
            color: #6e667d !important;
            line-height: 1.35;
        }
        .vc-precision-label small { font-weight: 500; color: #a1a1aa !important; }
        .vc-precision-chip {
            display: inline-block;
            margin-top: 0.65rem;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
        }
        .vc-precision-chip-key {
            background: rgba(99,102,241,0.14);
            color: #4338ca !important;
        }
        .vc-pitch-quality { margin-top: 0.75rem; }
        .vc-pitch-quality-title {
            margin: 0 0 0.35rem;
            font-size: 0.72rem;
            font-weight: 700;
            color: #6e667d !important;
        }
        .vc-pitch-bucket-row {
            display: flex;
            height: 8px;
            border-radius: 999px;
            overflow: hidden;
            background: #ebe6f5;
        }
        .vc-pitch-bucket {
            display: block;
            width: var(--w);
            background: var(--c);
            min-width: 2px;
        }
        .vc-pitch-quality-legend {
            display: flex;
            gap: 0.65rem;
            margin-top: 0.35rem;
            font-size: 0.62rem;
            color: #6e667d !important;
        }
        .vc-precision-recommend {
            margin: 0.65rem 0 0.75rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
            border: 1px solid rgba(245,158,11,0.35);
        }
        .vc-precision-recommend-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 800;
            color: #92400e !important;
        }
        .vc-precision-recommend-body {
            margin: 0.35rem 0 0;
            font-size: 0.78rem;
            color: #78350f !important;
            line-height: 1.5;
        }
        .vc-precision-recommend-body b { color: #b45309 !important; }
        .vc-song-hint-banner {
            margin: 0.65rem 0 0.85rem;
            padding: 0.75rem 0.95rem;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.08));
            border: 1px solid rgba(129,140,248,0.35);
        }
        .vc-song-hint-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: #4338ca !important;
        }
        .vc-song-hint-body {
            margin: 0.3rem 0 0;
            font-size: 0.76rem;
            color: #6366f1 !important;
            line-height: 1.45;
        }
        .vc-note-drill-row {
            display: flex;
            align-items: flex-start;
            gap: 0.65rem;
            margin: 0.75rem 0 0.25rem;
            padding: 0.55rem 0.7rem;
            border-radius: 10px;
            background: rgba(39,39,42,0.04);
            border: 1px solid rgba(161,161,170,0.25);
        }
        .vc-note-drill-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1.75rem;
            height: 1.75rem;
            border-radius: 999px;
            background: rgba(99,102,241,0.15);
            color: #6366f1 !important;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .vc-note-drill-title {
            margin: 0;
            font-size: 0.84rem;
            font-weight: 600;
            color: #27272a !important;
        }
        .vc-note-drill-meta {
            margin: 0.15rem 0 0;
            font-size: 0.74rem;
            color: #71717a !important;
        }
        .vc-note-drill-active {
            border-color: rgba(99,102,241,0.45) !important;
            background: rgba(99,102,241,0.08) !important;
        }
        .vc-note-timeline {
            position: relative;
            height: 0.55rem;
            margin: 0.5rem 0 0.85rem;
            border-radius: 999px;
            background: rgba(161,161,170,0.2);
            overflow: hidden;
        }
        .vc-note-tick {
            position: absolute;
            top: 0;
            left: var(--left);
            width: var(--width);
            min-width: 3px;
            height: 100%;
            border-radius: 2px;
        }
        .vc-note-tick-hit { background: #22c55e; opacity: 0.75; }
        .vc-note-tick-miss { background: #ef4444; opacity: 0.8; }
        .vc-note-tick-active {
            outline: 2px solid #6366f1;
            outline-offset: 1px;
            z-index: 2;
        }
        .vc-report-section {
            margin-top: 1.25rem;
        }
        .st-key-btn_analyzing_status button {
            background: rgba(99,102,241,0.25) !important;
            color: #c4b5fd !important;
            border: 1px solid rgba(129,140,248,0.45) !important;
            opacity: 0.85 !important;
        }
        .vc-dm-suggest-label {
            font-size: 0.78rem;
            color: #71717a !important;
            margin: 0.5rem 0 0.35rem;
        }
        [data-testid="stChatMessage"] {
            background: transparent !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0.4rem 0.45rem !important;
            margin-bottom: 0.5rem !important;
            gap: 0.55rem !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            flex-direction: row !important;
            justify-content: flex-start !important;
        }
        @keyframes vc-msg-in {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            flex-direction: row-reverse !important;
            justify-content: flex-start !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
            align-items: flex-end !important;
            flex: 0 1 auto !important;
            max-width: calc(100% - 3rem);
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
            background: #ffffff !important;
            color: #1c1528 !important;
            border: 1px solid #e0dce8 !important;
            border-radius: 18px !important;
            border-bottom-left-radius: 4px !important;
            padding: 0.75rem 0.95rem !important;
            max-width: 100% !important;
            width: auto !important;
            font-size: 0.9rem !important;
            line-height: 1.78 !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            white-space: normal !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
            background: linear-gradient(135deg, #565bcf 0%, #8134af 50%, #c13584 100%) !important;
            color: #ffffff !important;
            border-radius: 18px !important;
            border-bottom-right-radius: 4px !important;
            padding: 0.7rem 0.95rem !important;
            max-width: 78% !important;
            width: fit-content !important;
            font-size: 0.9rem !important;
            line-height: 1.72 !important;
            box-shadow: 0 2px 8px rgba(129, 52, 175, 0.35);
        }
        .st-key-vc_dm_panel [data-testid="stMarkdownContainer"] p,
        .st-key-vc_dm_panel [data-testid="stMarkdownContainer"] li {
            margin-bottom: 0.55rem !important;
            line-height: 1.78 !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
            white-space: normal !important;
        }
        .st-key-vc_dm_panel [data-testid="stMarkdownContainer"] p:last-child,
        .st-key-vc_dm_panel [data-testid="stMarkdownContainer"] li:last-child {
            margin-bottom: 0 !important;
        }
        .st-key-vc_dm_panel hr,
        .st-key-vc_dm_panel [data-testid="stMarkdownContainer"] hr {
            display: none !important;
            border: none !important;
            margin: 0 !important;
            height: 0 !important;
        }
        .st-key-vc_dm_panel [data-testid="stCaptionContainer"] {
            display: none !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p,
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] li {
            color: #ffffff !important;
        }
        .vc-bubble-typing {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.5rem 0.75rem;
            background: #27272a;
            border-radius: 18px;
            border: 1px solid #3f3f46;
        }
        .st-key-vc_dm_thread {
            background: #0f0f12;
            padding: 0.75rem 0.4rem 0.65rem;
            min-height: 200px;
            max-height: 420px;
            overflow-y: auto;
            overflow-x: hidden;
            border-bottom: 1px solid var(--vc-border);
            scroll-behavior: smooth;
        }
        .st-key-vc_dm_thread [data-testid="stVerticalBlock"] {
            max-height: 380px;
            overflow-y: auto !important;
            scroll-behavior: smooth;
        }
        .vc-detail-panel [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
        .vc-detail-panel [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
            line-height: 1.78 !important;
            margin-bottom: 0.6rem !important;
            word-break: keep-all !important;
            overflow-wrap: anywhere !important;
        }
        .vc-detail-panel [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p:last-child {
            margin-bottom: 0 !important;
        }
        .st-key-vc_dm_panel [data-testid="chatAvatarIcon-assistant"] {
            background: var(--vc-gradient) !important;
        }
        .st-key-coach_suggest_0 button,
        .st-key-coach_suggest_1 button,
        .st-key-coach_suggest_2 button {
            background: var(--vc-card) !important;
            color: #c4b5fd !important;
            border: 1px solid rgba(129,140,248,0.35) !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            text-align: left !important;
            white-space: normal !important;
            height: auto !important;
            min-height: 2.5rem !important;
            padding: 0.5rem 0.65rem !important;
        }
        .vc-login-gate {
            text-align: center;
            padding: 0.5rem 0.25rem 1rem;
            margin-bottom: 0.5rem;
        }
        .vc-login-gate .vc-login-card-panel {
            margin-top: 0;
        }
        .vc-results-head {
            margin-bottom: 1.25rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--vc-border);
        }

        /* 상세 분석 리포트 */
        .vc-detail-hero {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            padding: 0.85rem 1rem;
            margin-bottom: 0.75rem;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(24,24,27,0.9));
            border: 1px solid rgba(129,140,248,0.25);
        }
        .vc-detail-hero-icon {
            width: 44px; height: 44px;
            border-radius: 12px;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.25rem;
        }
        .vc-detail-hero-title {
            margin: 0;
            font-size: 0.95rem;
            font-weight: 800;
            color: #fafafa !important;
        }
        .vc-detail-hero-sub {
            margin: 0.15rem 0 0;
            font-size: 0.75rem;
            color: #71717a !important;
        }
        .vc-detail-panel {
            background: rgba(24,24,27,0.5);
            border: 1px solid var(--vc-border);
            border-radius: 16px;
            padding: 1rem 1.1rem 0.5rem;
            margin-bottom: 0.5rem;
        }
        .vc-section-label {
            margin: 1rem 0 0.55rem;
            font-size: 0.78rem;
            font-weight: 700;
            color: #a1a1aa !important;
            letter-spacing: 0.02em;
        }
        .vc-score-ring-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0.5rem 0 0.75rem;
        }
        .vc-score-ring {
            width: 128px;
            height: 128px;
            border-radius: 50%;
            background: conic-gradient(
                var(--ring-color) calc(var(--pct) * 1%),
                #27272a 0
            );
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 24px rgba(99,102,241,0.15);
        }
        .vc-score-ring-inner {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .vc-score-ring-grade {
            font-size: 0.65rem;
            font-weight: 800;
            color: var(--ring-color) !important;
            letter-spacing: 0.08em;
        }
        .vc-score-ring-val {
            font-size: 2rem;
            font-weight: 900;
            line-height: 1;
            color: #fafafa !important;
        }
        .vc-score-ring-label {
            margin: 0.55rem 0 0;
            font-size: 0.82rem;
            font-weight: 700;
            color: #e4e4e7 !important;
        }
        .vc-score-ring-sub {
            margin: 0.1rem 0 0;
            font-size: 0.68rem;
            color: #71717a !important;
        }
        .vc-stage-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.65rem;
        }
        @media (max-width: 768px) {
            .vc-stage-grid { grid-template-columns: 1fr; }
        }
        .vc-stage-card {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 14px;
            padding: 0.85rem 0.9rem;
            border-top: 3px solid var(--accent);
        }
        .vc-stage-card-top {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.35rem;
        }
        .vc-stage-icon { font-size: 1rem; }
        .vc-stage-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #a1a1aa !important;
        }
        .vc-stage-score-row {
            display: flex;
            align-items: baseline;
            gap: 0.35rem;
            margin-bottom: 0.45rem;
        }
        .vc-stage-score {
            font-size: 1.65rem;
            font-weight: 900;
            color: #fafafa !important;
            line-height: 1;
        }
        .vc-stage-grade {
            font-size: 0.72rem;
            font-weight: 800;
            color: var(--accent) !important;
        }
        .vc-stage-bar {
            height: 6px;
            border-radius: 999px;
            background: #27272a;
            overflow: hidden;
            margin-bottom: 0.4rem;
        }
        .vc-stage-bar > div {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--accent), rgba(255,255,255,0.35));
        }
        .vc-stage-caption {
            margin: 0;
            font-size: 0.68rem;
            color: #71717a !important;
            line-height: 1.35;
        }
        .vc-radar-frame, .vc-graph-frame {
            background: #18181b;
            border: 1px solid var(--vc-border);
            border-radius: 14px;
            padding: 0.35rem;
            overflow: hidden;
        }
        .vc-graph-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.65rem;
        }
        .vc-legend-pill {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 999px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
        }
        .vc-legend-ok { color: #60a5fa !important; }
        .vc-legend-bad { color: #f87171 !important; }
        .vc-legend-guide { color: #4ade80 !important; }
        .vc-dev-list {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
            margin-top: 0.35rem;
        }
        .vc-dev-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.65rem;
            padding: 0.65rem 0.85rem;
            border-radius: 12px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
        }
        .vc-dev-high { border-left: 3px solid #f87171; }
        .vc-dev-mid { border-left: 3px solid #f59e0b; }
        .vc-dev-low { border-left: 3px solid #818cf8; }
        .vc-dev-main { display: flex; flex-direction: column; gap: 0.1rem; }
        .vc-dev-time {
            font-size: 0.82rem;
            font-weight: 700;
            color: #e4e4e7 !important;
        }
        .vc-dev-note {
            font-size: 0.72rem;
            color: #71717a !important;
        }
        .vc-dev-badge {
            font-size: 0.68rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            color: #d4d4d8 !important;
            white-space: nowrap;
        }
        .vc-insight-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.85rem 0 0.5rem;
        }
        .vc-insight-pill {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            color: #d4d4d8 !important;
        }
        .vc-insight-accent { border-color: rgba(168,85,247,0.4); color: #d8b4fe !important; }
        .vc-insight-good { border-color: rgba(34,197,94,0.35); color: #86efac !important; }
        .vc-mr-note {
            font-size: 0.78rem;
            padding: 0.55rem 0.75rem;
            border-radius: 10px;
            margin: 0.5rem 0 0;
        }
        .vc-mr-warn {
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.3);
            color: #fcd34d !important;
        }
        .vc-mr-info {
            background: rgba(99,102,241,0.1);
            border: 1px solid rgba(129,140,248,0.25);
            color: #c4b5fd !important;
        }
        .vc-feedback-panel {
            margin-top: 0.75rem;
            padding-top: 0.5rem;
            border-top: 1px solid var(--vc-border);
        }
        .vc-coach-summary {
            margin: 0 0 0.75rem;
            padding: 0.55rem 0.75rem;
            font-size: 0.85rem;
            color: #d4d4d8 !important;
            background: rgba(99,102,241,0.06);
            border-radius: 0 10px 10px 0;
        }
        .vc-coach-block {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 12px;
            padding: 0.75rem 0.85rem;
            margin-bottom: 0.55rem;
        }
        .vc-coach-block-num {
            margin: 0 0 0.35rem;
            font-size: 0.72rem;
            font-weight: 800;
            color: #a78bfa !important;
        }
        .vc-coach-line {
            margin: 0.2rem 0;
            font-size: 0.82rem;
            color: #d4d4d8 !important;
            line-height: 1.45;
        }
        .vc-action-card {
            display: flex;
            gap: 0.75rem;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.55rem;
        }
        .vc-action-priority {
            width: 28px; height: 28px;
            border-radius: 8px;
            background: var(--vc-gradient);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.82rem;
            font-weight: 800;
            color: #fff !important;
            flex-shrink: 0;
        }
        .vc-action-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: #fafafa !important;
        }
        .vc-action-rx, .vc-action-practice {
            margin: 0.25rem 0 0;
            font-size: 0.78rem;
            color: #d4d4d8 !important;
        }
        .vc-action-reason {
            margin: 0.35rem 0 0;
            font-size: 0.72rem;
            color: #71717a !important;
            font-style: italic;
        }
        .vc-gpt-box {
            background: var(--vc-card);
            border: 1px solid rgba(129,140,248,0.25);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            font-size: 0.88rem;
            line-height: 1.55;
            color: #e4e4e7 !important;
        }
        .vc-compare-box {
            background: #18181b;
            border: 1px solid var(--vc-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            font-size: 0.78rem;
            color: #d4d4d8 !important;
            white-space: pre-wrap;
        }
        .vc-download-card {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            margin-bottom: 0.65rem;
        }
        .vc-download-icon { font-size: 1.35rem; }
        .vc-download-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: #fafafa !important;
        }
        .vc-download-path {
            margin: 0.15rem 0 0;
            font-size: 0.72rem;
            color: #71717a !important;
            word-break: break-all;
        }
        .vc-clip-name {
            margin: 0.35rem 0 0.15rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: #c4b5fd !important;
        }
        .vc-empty-note {
            font-size: 0.82rem;
            color: #71717a !important;
            padding: 0.65rem 0;
        }

        /* 마이 페이지 */
        .vc-mypage-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.55rem;
            margin-bottom: 1rem;
        }
        .vc-mypage-stat {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 12px;
            padding: 0.75rem 0.5rem;
            text-align: center;
        }
        .vc-mypage-stat-val {
            display: block;
            font-size: 1.35rem;
            font-weight: 900;
            color: #fafafa !important;
        }
        .vc-mypage-stat-lbl {
            display: block;
            font-size: 0.65rem;
            color: #71717a !important;
            margin-top: 0.15rem;
        }
        .vc-empty-card {
            text-align: center;
            padding: 2rem 1.25rem;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 16px;
            margin-bottom: 1rem;
        }
        .vc-empty-title {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: #fafafa !important;
        }
        .vc-empty-desc {
            margin: 0.65rem 0 0;
            font-size: 0.85rem;
            color: #71717a !important;
            line-height: 1.5;
        }
        .vc-record-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.45rem;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 12px;
        }
        .vc-record-date {
            margin: 0;
            font-size: 0.72rem;
            color: #71717a !important;
        }
        .vc-record-song {
            margin: 0.15rem 0 0;
            font-size: 0.88rem;
            font-weight: 600;
            color: #e4e4e7 !important;
        }
        .vc-record-sub {
            margin: 0;
            font-size: 0.68rem;
            color: #52525b !important;
        }
        .vc-history-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.85rem;
            padding: 0.9rem 1rem;
            margin-bottom: 0.35rem;
            background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, var(--vc-card) 45%);
            border: 1px solid rgba(129,140,248,0.28);
            border-left: 3px solid var(--banner-accent, #6366f1);
            border-radius: 14px;
        }
        .vc-history-banner-left { flex: 1; min-width: 0; }
        .vc-history-date {
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 700;
            color: #a5b4fc !important;
            background: rgba(99,102,241,0.18);
            padding: 0.15rem 0.45rem;
            border-radius: 6px;
            margin-bottom: 0.35rem;
        }
        .vc-history-song {
            margin: 0;
            font-size: 0.92rem;
            font-weight: 700;
            color: #fafafa !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .vc-history-sub {
            margin: 0.25rem 0 0;
            font-size: 0.72rem;
            color: #71717a !important;
        }
        .vc-history-score { text-align: center; flex-shrink: 0; }
        .vc-history-overall {
            display: block;
            font-size: 1.55rem;
            font-weight: 900;
            color: var(--banner-accent, #c4b5fd) !important;
            line-height: 1;
        }
        .vc-history-score-label {
            display: block;
            font-size: 0.65rem;
            color: #71717a !important;
        }
        .vc-record-scores { text-align: right; }
        .vc-record-overall {
            display: block;
            font-size: 1.25rem;
            font-weight: 900;
            color: #c4b5fd !important;
        }
        .vc-record-sub {
            font-size: 0.65rem;
            color: #71717a !important;
        }

        /* 피드백 */
        .vc-feedback-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .vc-feedback-stat {
            font-size: 0.75rem;
            color: #a1a1aa !important;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
        }
        .vc-feedback-card {
            background: var(--vc-card);
            border: 1px solid var(--vc-border);
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.45rem;
        }
        .vc-feedback-card-meta {
            margin: 0;
            font-size: 0.68rem;
            color: #a78bfa !important;
            font-weight: 700;
        }
        .vc-feedback-card-msg {
            margin: 0.35rem 0 0;
            font-size: 0.82rem;
            color: #d4d4d8 !important;
            line-height: 1.45;
        }
        .st-key-beta_feedback_shortcut button {
            background: rgba(99,102,241,0.15) !important;
            color: #c4b5fd !important;
            border: 1px solid rgba(129,140,248,0.35) !important;
            font-weight: 700 !important;
            min-height: 2.4rem !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            background: var(--vc-card) !important;
            border-radius: 10px 10px 0 0 !important;
            border: 1px solid var(--vc-border) !important;
            padding: 0.45rem 0.85rem !important;
            font-size: 0.78rem !important;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            background: rgba(99,102,241,0.15) !important;
            border-color: rgba(129,140,248,0.4) !important;
            color: #c4b5fd !important;
        }
        .st-key-btn_new_analysis .stButton > button {
            background: var(--vc-card) !important;
            color: var(--vc-muted) !important;
            border: 1px solid var(--vc-border) !important;
        }
        .score-card h2 { color: var(--vc-text) !important; }
        .vc-section { color: var(--vc-text); font-weight: 800; font-size: 1.25rem; }
        .vc-caption { color: var(--vc-muted); font-size: 0.88rem; }

        /* Force markdown HTML text visible */
        [data-testid="stMarkdownContainer"] .vc-section-h2,
        [data-testid="stMarkdownContainer"] .vc-trust-item strong,
        [data-testid="stMarkdownContainer"] .vc-pain-card,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: inherit;
        }

        @media (max-width: 768px) {
            .block-container { padding-left: 0.65rem !important; padding-right: 0.65rem !important; }
            .vc-header-shell { padding: 0.65rem 0.75rem 0.2rem; margin: -0.5rem -0.5rem 0; }
            .vc-header-name { font-size: 0.78rem; }
            .vc-header-tag { display: none; }
            .vc-header-logo { width: 34px; height: 34px; font-size: 1rem; }
            .vc-navbar-marker + [data-testid="stHorizontalBlock"] {
                padding: 0.45rem 0.55rem !important;
                border-radius: 16px !important;
            }
            .st-key-nav_brand_home button { font-size: 0.82rem !important; min-height: 2.5rem !important; }
            .st-key-nav_menu > div > button { min-width: 2.5rem !important; }
            .vc-mypage-stats { grid-template-columns: repeat(2, 1fr) !important; }
            .st-key-top_auth_popover,
            .st-key-top_auth_user { max-width: 100%; }
            .st-key-top_auth_popover > div > button,
            .st-key-top_auth_user > div > button {
                font-size: 0.72rem !important;
                padding: 0.45rem 0.55rem !important;
                min-height: 2.5rem !important;
            }
            [data-testid="column"] { min-width: 0 !important; }
            .vc-score-strip { justify-content: center; }
            .vc-score-chip { min-width: 56px; font-size: 0.95rem; }
            .vc-result-hero-inner { flex-direction: column; text-align: center; }
            .vc-result-hero-score { width: 100%; }
            [data-testid="stFileUploader"] section { padding: 0.5rem !important; }
            [data-testid="stChatInput"] {
                padding-bottom: max(0.5rem, env(safe-area-inset-bottom, 0)) !important;
            }
            .vc-hero-h1 { font-size: clamp(1.75rem, 8vw, 2.4rem); }
            .vc-record-hero { padding: 1rem 0.9rem; margin-bottom: 0.65rem; }
            .vc-record-hero-title { font-size: 1.2rem; }
            .vc-record-hero-lead { font-size: 0.82rem; }
            [data-testid="stAudioInput"] button { min-width: 100% !important; }
            .vc-precision-grid { grid-template-columns: repeat(2, 1fr) !important; }
            .st-key-landing_cta, .st-key-landing_cta_bottom,
            .st-key-landing_my, .st-key-btn_open_analysis_settings,
            .st-key-btn_open_analysis_settings_results,
            .st-key-btn_start_analysis, .st-key-btn_new_analysis {
                width: 100% !important;
            }
            .st-key-landing_cta button, .st-key-landing_cta_bottom button,
            .st-key-btn_start_analysis button {
                min-height: 48px !important;
            }
            .vc-steps-row { flex-direction: column; }
            .vc-step-arrow { display: none; }
            .vc-step-card { min-width: 100%; }
            /* 로그인 · 랜딩 */
            .vc-login-card-panel {
                padding: 1.1rem 1rem;
                border-radius: 18px;
                margin-left: 0;
                margin-right: 0;
                max-width: 100%;
            }
            .vc-login-hero { padding: 1rem 0.5rem 0.85rem; max-width: 100%; }
            .vc-auth-btn { min-height: 50px; font-size: 0.92rem; border-radius: 12px; }
            .vc-landing-trial-banner {
                padding: 0.9rem 1rem;
                margin-bottom: 0.45rem;
            }
            .vc-landing-trial-title { font-size: 0.92rem; }
            .st-key-nav_brand_home button {
                font-size: 0.72rem !important;
                padding: 0.4rem 0.45rem !important;
            }
            [class*="st-key-nav_btn_"] button {
                font-size: 0.72rem !important;
                min-height: 2.4rem !important;
            }
            .st-key-top_auth_popover > div > button {
                font-size: 0.72rem !important;
                padding: 0.42rem 0.55rem !important;
            }
            /* DM 채팅 — 인스타 풀폭 */
            .st-key-vc_dm_panel {
                margin-left: -0.65rem;
                margin-right: -0.65rem;
                border-radius: 0;
                border-left: none;
                border-right: none;
            }
            .vc-dm-header { border-radius: 0; }
            .vc-dm-composer {
                padding-bottom: max(0.65rem, env(safe-area-inset-bottom, 0));
            }
            .vc-dm-pill-row button {
                min-height: 2.5rem !important;
                font-size: 0.78rem !important;
            }
            /* 팝오버 로그인 */
            [data-testid="stPopoverBody"] {
                padding: 0.85rem !important;
                min-width: min(92vw, 320px) !important;
            }
            [data-testid="stPopoverBody"] .vc-auth-btn { min-height: 46px; }
        }
        @media (max-width: 900px) {
            .vc-header-shell + div [data-testid="column"]:nth-child(1) { flex: 1.2 !important; }
            .vc-header-shell + div [data-testid="column"]:nth-child(2) { flex: 2.5 !important; }
            .vc-header-shell + div [data-testid="column"]:nth-child(3) { flex: 1.3 !important; }
        }

        /* ── Light mode overrides (lavender cream · test) ── */
        .st-key-nav_brand_home button {
            color: #1c1528 !important;
            background: rgba(99,102,241,0.08) !important;
        }
        .st-key-nav_brand_home button:hover {
            color: #4f46e5 !important;
            background: rgba(99,102,241,0.14) !important;
        }
        .vc-header-name { color: #1c1528 !important; }
        .vc-header-tag { color: #6e667d !important; }
        .vc-section-h2, .vc-trust-item strong,
        .vc-page-title, .vc-section-title, .vc-spotlight-card h3,
        .vc-featured-card h3, .vc-tech-card h3, .vc-step-card strong,
        .vc-stage-label, .vc-login-brand-title, .vc-login-card-heading,
        .vc-landing-trial-title, .vc-result-hero-title, .vc-result-overall,
        .vc-detail-hero-title, .vc-insight-headline, .vc-chat-name,
        .vc-analyze-panel-title, .vc-page-head h2 {
            color: #1c1528 !important;
        }
        .vc-trust-item strong { color: #4338ca !important; }
        .vc-trust-item span { color: #6e667d !important; }
        .vc-pain-card { color: #3f3f46 !important; }
        .vc-testimonial p { color: #3f3f46 !important; }
        .vc-hero-lead b { color: #4338ca !important; }
        .vc-section-sub b { color: #4338ca !important; }
        .vc-page-desc, .vc-section-sub, .vc-spotlight-card p,
        .vc-featured-card p, .vc-tech-card p, .vc-step-card small,
        .vc-hero-desc, .vc-beta-text, .vc-landing-trial-sub,
        .vc-login-brand-tag, .vc-login-benefits li, .vc-login-footnote,
        .vc-insight-body, .vc-chat-msg, .vc-analyze-panel-desc,
        .vc-result-hero-strength, .vc-detail-hero-sub, .vc-footer p {
            color: #6e667d !important;
        }
        .vc-stat-chip, .vc-bento-card, .vc-spotlight-card, .vc-tech-card,
        .vc-step-card, .vc-stage-card, .vc-pain-card, .vc-quote-card,
        .vc-featured-card, .vc-detail-panel, .vc-login-card-panel,
        .vc-score-ring-inner {
            background: var(--vc-gradient-card) !important;
            border-color: rgba(99,102,241,0.16) !important;
        }
        .vc-featured-card {
            background: linear-gradient(135deg, #ede9fe 0%, #f8f6ff 100%) !important;
        }
        .vc-stat-chip {
            background: linear-gradient(145deg, #ffffff, #f3f0ff) !important;
        }
        .vc-stat-chip b { color: #1c1528 !important; }
        .vc-hero-main {
            background:
                radial-gradient(ellipse 80% 60% at 20% 0%, rgba(99,102,241,0.28), transparent),
                radial-gradient(ellipse 60% 50% at 90% 20%, rgba(168,85,247,0.18), transparent),
                linear-gradient(160deg, #ddd6fe 0%, #ede9fe 42%, #f5f3ff 100%) !important;
            border-color: rgba(99,102,241,0.28) !important;
            box-shadow: 0 8px 32px rgba(99,102,241,0.12) !important;
        }
        .vc-landing-trial-banner {
            background: linear-gradient(135deg, rgba(99,102,241,0.2) 0%, #ddd6fe 45%, rgba(168,85,247,0.14) 100%) !important;
            border-color: rgba(99,102,241,0.32) !important;
            box-shadow: 0 4px 20px rgba(99,102,241,0.14) !important;
        }
        .vc-landing-trial-tag { color: #4f46e5 !important; background: rgba(99,102,241,0.12) !important; }
        .vc-landing-trial-sub b { color: #6366f1 !important; }
        .vc-result-hero {
            background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, #ede9fe 50%, rgba(168,85,247,0.1) 100%) !important;
        }
        .vc-beta-banner {
            background: linear-gradient(90deg, rgba(99,102,241,0.14) 0%, rgba(237,233,254,0.9) 100%) !important;
            border-color: rgba(99,102,241,0.24) !important;
        }
        .vc-beta-text { color: #52525b !important; }

        /* ── Light mode — analysis · results · my page ── */
        .stApp:has(#vc-analyzing-anchor)::before {
            background: rgba(244,242,248,0.82) !important;
        }
        .vc-page-badge { color: #4338ca !important; }
        .vc-analyze-panel-title,
        .vc-analyzing-title,
        .vc-upload-title,
        .vc-score-ring-val,
        .vc-stage-score,
        .vc-mypage-stat-val,
        .vc-empty-title,
        .vc-history-song,
        .vc-record-song,
        .vc-dm-title,
        .vc-dev-time {
            color: #1c1528 !important;
        }
        .vc-analyze-panel-desc,
        .vc-analyzing-sub,
        .vc-upload-desc,
        .vc-start-hint,
        .vc-tip-soft-body,
        .vc-empty-note,
        .vc-empty-desc,
        .vc-mypage-stat-lbl,
        .vc-history-sub,
        .vc-history-score-label,
        .vc-record-date,
        .vc-record-sub,
        .vc-stage-caption,
        .vc-score-ring-sub,
        .vc-dev-note,
        .vc-insight-detail {
            color: #52525b !important;
        }
        .vc-result-hero-strength,
        .vc-score-ring-label {
            color: #3f3f46 !important;
        }
        .vc-result-hero-focus,
        .vc-analyzing-mode,
        .vc-chat-eta,
        .vc-section-label,
        .vc-chat-name,
        .vc-chat-pct,
        .vc-tip-soft-title,
        .vc-stage-label {
            color: #6366f1 !important;
        }
        .vc-trust-item strong,
        .vc-score-chip,
        .vc-history-overall {
            color: #4338ca !important;
        }
        .vc-result-badge { color: #16a34a !important; background: rgba(34,197,94,0.12) !important; }
        .vc-result-hero {
            background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, #ede9fe 50%, rgba(168,85,247,0.1) 100%) !important;
            border-color: rgba(99,102,241,0.28) !important;
        }
        .vc-result-hero-score {
            background: rgba(255,255,255,0.9) !important;
            border: 1px solid rgba(99,102,241,0.2) !important;
        }
        .vc-result-overall-label,
        .vc-score-chip small {
            color: #6e667d !important;
        }
        .st-key-vc_analyze_panel .vc-analyze-progress-card,
        .st-key-vc_analyze_panel .vc-chat-card,
        .vc-analyzing-panel {
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%) !important;
            border: 1px solid rgba(99,102,241,0.22) !important;
            box-shadow: 0 12px 40px rgba(99,102,241,0.1) !important;
        }
        .vc-chat-card { background: #ffffff !important; }
        .vc-chat-msg { color: #3f3f46 !important; }
        .vc-chat-progress,
        .vc-stage-bar {
            background: #e0dce8 !important;
        }
        .vc-chip-done { color: #4338ca !important; }
        .vc-chip-tip::after {
            background: #ffffff !important;
            color: #1c1528 !important;
            border: 1px solid #e0dce8 !important;
        }
        .st-key-btn_cancel_analysis_main button {
            background: #ffffff !important;
            color: #52525b !important;
            border-color: rgba(99,102,241,0.22) !important;
        }
        .st-key-btn_cancel_analysis_main button:hover {
            color: #1c1528 !important;
            border-color: rgba(99,102,241,0.4) !important;
        }
        .st-key-btn_open_analysis_settings button,
        .st-key-btn_open_analysis_settings_results button {
            background: #ffffff !important;
            color: #4338ca !important;
            border-color: rgba(99,102,241,0.28) !important;
        }
        .vc-upload-zone,
        .vc-upload-card,
        .vc-mypage-stat,
        .vc-empty-card,
        .vc-insight-card {
            background: linear-gradient(145deg, #ffffff 0%, #f3f0ff 100%) !important;
            border-color: rgba(99,102,241,0.18) !important;
        }
        .vc-upload-hint-text,
        .vc-upload-hint-text span { color: #52525b !important; }
        .vc-history-banner {
            background: linear-gradient(135deg, rgba(99,102,241,0.14) 0%, #f5f3ff 55%) !important;
            border-color: rgba(99,102,241,0.22) !important;
        }
        .vc-history-date { color: #4338ca !important; }
        .vc-detail-hero {
            background: linear-gradient(135deg, rgba(99,102,241,0.14), #f5f3ff) !important;
            border-color: rgba(99,102,241,0.22) !important;
        }
        .vc-detail-panel {
            background: rgba(255,255,255,0.95) !important;
            border-color: rgba(99,102,241,0.16) !important;
        }
        .vc-score-ring {
            background: conic-gradient(var(--ring-color) calc(var(--pct) * 1%), #e0dce8 0) !important;
        }
        .vc-radar-frame,
        .vc-graph-frame {
            background: #f8f6ff !important;
            border-color: rgba(99,102,241,0.16) !important;
        }
        .vc-insight-good-card {
            background: linear-gradient(90deg, rgba(34,197,94,0.08), #ffffff 42%) !important;
        }
        .vc-insight-focus-card {
            background: linear-gradient(90deg, rgba(99,102,241,0.1), #ffffff 42%) !important;
        }
        .vc-focus-num {
            color: #4338ca !important;
            background: rgba(99,102,241,0.14) !important;
        }
        .vc-insight-pill {
            color: #3f3f46 !important;
            background: #ffffff !important;
            border-color: #e0dce8 !important;
        }
        .vc-insight-accent { color: #6366f1 !important; }
        .vc-insight-good { color: #16a34a !important; }
        .vc-dev-badge {
            background: rgba(99,102,241,0.08) !important;
            color: #52525b !important;
        }
        .vc-score-overall {
            background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(168,85,247,0.08)) !important;
            border-color: rgba(99,102,241,0.28) !important;
        }
        .vc-score-chip {
            background: #ffffff !important;
            color: #4338ca !important;
        }
        .vc-feedback-panel,
        .vc-feedback-card {
            background: #ffffff !important;
            border-color: rgba(99,102,241,0.16) !important;
        }
        .vc-feedback-card-msg,
        .vc-feedback-card-meta { color: #52525b !important; }
        .vc-chat-mode-pill { color: #4338ca !important; }
        .st-key-coach_pill_0 button,
        .st-key-coach_pill_1 button,
        .st-key-coach_pill_2 button {
            color: #4338ca !important;
            background: rgba(99,102,241,0.1) !important;
            border-color: rgba(99,102,241,0.22) !important;
        }
        .vc-dm-composer [data-testid="stTextInput"] input {
            background: #ffffff !important;
            color: #1c1528 !important;
            border-color: rgba(99,102,241,0.2) !important;
        }
        [data-testid="stDialog"] h2 { color: #1c1528 !important; }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span {
            color: #1c1528 !important;
        }
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
            color: #52525b !important;
        }
        .vc-stage-native-label { color: #6e667d !important; }
        .vc-stage-native-score { color: #1c1528 !important; }
        .vc-stage-native-score span { color: #6366f1 !important; }
        .vc-coach-summary,
        .vc-coach-line,
        .vc-action-rx,
        .vc-action-practice,
        .vc-gpt-box,
        .vc-compare-box {
            color: #52525b !important;
        }
        .vc-coach-block-num,
        .vc-clip-name { color: #6366f1 !important; }
        .vc-coach-block,
        .vc-action-card,
        .vc-gpt-box,
        .vc-download-card {
            background: #ffffff !important;
            border-color: rgba(99,102,241,0.16) !important;
        }
        .vc-compare-box {
            background: #f8f6ff !important;
        }
        .vc-action-title,
        .vc-download-title {
            color: #1c1528 !important;
        }
        .vc-action-reason,
        .vc-download-path {
            color: #6e667d !important;
        }
        .vc-mr-warn { color: #b45309 !important; }
        .vc-mr-info { color: #4338ca !important; }

        .st-key-vc_dm_panel {
            background: #ffffff !important;
            border: 1px solid rgba(99,102,241,0.18) !important;
            box-shadow: 0 4px 24px rgba(99,102,241,0.06) !important;
        }
        .st-key-vc_dm_thread, .vc-dm-thread, .vc-dm-composer {
            background: #f8f6ff !important;
        }
        .vc-dm-header {
            background: linear-gradient(135deg, #f3f0ff 0%, #ffffff 100%) !important;
            border-bottom: 1px solid rgba(99,102,241,0.12) !important;
        }
        .st-key-vc_dm_panel [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
            background: #ffffff !important;
            color: #1c1528 !important;
            border: 1px solid #e0dce8 !important;
        }
        .vc-bubble-typing {
            background: #ffffff !important;
            border-color: #e0dce8 !important;
        }
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            color: #1c1528 !important;
            border-color: rgba(99,102,241,0.2) !important;
        }
        [data-testid="stPopoverBody"] {
            background: #ffffff !important;
            border: 1px solid rgba(99,102,241,0.15) !important;
            box-shadow: 0 8px 32px rgba(99,102,241,0.1) !important;
        }
        [data-testid="stDialog"] > div {
            background: #faf9fd !important;
            color: #1c1528 !important;
        }
        [data-testid="stAlert"], .stAlert {
            background: #f3f0ff !important;
            border: 1px solid rgba(99,102,241,0.2) !important;
            color: #4338ca !important;
        }
        .st-key-top_auth_popover .stButton > button,
        .st-key-top_auth_user .stButton > button {
            background: rgba(99,102,241,0.06) !important;
            color: #1c1528 !important;
            border: 1px solid rgba(99,102,241,0.14) !important;
        }
        .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            border: 1px solid rgba(99,102,241,0.22) !important;
            color: #4f46e5 !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: #f3f0ff !important;
        }
        [data-testid="stFileUploader"] section {
            background: #ffffff !important;
            border-color: rgba(99,102,241,0.22) !important;
        }
        label, .stCaption, [data-testid="stWidgetLabel"] p {
            color: #6e667d !important;
        }
        .vc-progress-track, .vc-chip-pending {
            background: #ebe6f5 !important;
        }
        .vc-page-head {
            border-bottom-color: rgba(99,102,241,0.15) !important;
        }
        @media (max-width: 768px) {
            .vc-navbar-marker + [data-testid="stHorizontalBlock"] {
                background: rgba(255,255,255,0.96) !important;
                border-top: 1px solid rgba(99,102,241,0.12) !important;
                box-shadow: 0 -4px 24px rgba(99,102,241,0.06) !important;
            }
            .vc-beta-banner {
                flex-wrap: nowrap !important;
                gap: 0.35rem !important;
            }
            .vc-beta-tag { font-size: 0.58rem !important; padding: 0.18rem 0.4rem !important; }
            .vc-beta-text { font-size: 0.68rem !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .st-key-beta_feedback_shortcut button {
                font-size: 0.68rem !important;
                min-height: 2.2rem !important;
                padding: 0.3rem 0.45rem !important;
            }
        }
        """
        + sidebar_css
        + """
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_shell() -> None:
    st.markdown(
        """
        <div class="vc-header-brand" style="justify-content:center;padding:1.5rem 0;">
            <span class="vc-header-logo">🎤</span>
            <div class="vc-header-titles">
                <span class="vc-header-name">VOCAL COACH AI</span>
                <span class="vc-header-tag">로그인 · 회원가입</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def topbar() -> None:
    pass


def hero(title: str, subtitle: str, badge: str = "ANALYSIS") -> None:
    st.markdown(
        f"""
        <div class="vc-page-head">
            <span class="vc-page-badge">{badge}</span>
            <h2 class="vc-page-title">{title}</h2>
            <p class="vc-page-desc">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str = "") -> None:
    st.markdown(f'<p class="vc-section">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<p class="vc-caption">{caption}</p>', unsafe_allow_html=True)


def sidebar_label(text: str) -> None:
    st.markdown(f'<p class="vc-sidebar-label">{text}</p>', unsafe_allow_html=True)
