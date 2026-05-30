"""로그인 버튼·카드 UI (홈 · 마이 · 팝오버 공통)."""

from __future__ import annotations

import streamlit as st

from auth_service import auth_base_url, google_configured, kakao_configured
from ui.runtime_env import is_streamlit_cloud
from ui.utils import render_safe_html


def _oauth_hint(provider: str) -> str:
    if is_streamlit_cloud():
        return f"{provider}: 베타 — **체험 계정**으로 이용해 주세요"
    return f"{provider}: OAuth 미설정 (로컬 .env 참고)"


def render_trial_button(*, key_prefix: str = "trial") -> None:
    """체험 계정만 — 랜딩 등 소셜 로그인은 상단 팝오버."""
    if st.button(
        "✦ 체험 계정으로 바로 시작",
        key=f"{key_prefix}_demo",
        use_container_width=True,
        type="primary"
    ):
        from ui.auth import start_demo

        start_demo()


def render_auth_buttons(*, key_prefix: str = "auth", compact: bool = False) -> None:
    """카카오 → Google → 체험 (한국 앱 UX 순서)."""
    base = auth_base_url()
    g_ok = google_configured()
    k_ok = kakao_configured()
    sm = " vc-auth-sm" if compact else ""

    if k_ok:
        render_safe_html(f'<a href="{base}/auth/kakao" class="vc-auth-btn vc-auth-kakao{sm}">'
            f'<span class="vc-auth-btn-icon">💬</span> 카카오로 시작하기</a>'
        )
    else:
        render_safe_html(
            f'<span class="vc-auth-btn vc-auth-kakao vc-auth-disabled{sm}">'
            f'<span class="vc-auth-btn-icon">💬</span> 카카오로 시작하기</span>'
        )

    if g_ok:
        render_safe_html(
            f'<a href="{base}/auth/google" class="vc-auth-btn vc-auth-google{sm}">'
            f'<span class="vc-auth-btn-icon vc-auth-g-icon">G</span> Google로 시작하기</a>'
        )
    else:
        render_safe_html(
            f'<span class="vc-auth-btn vc-auth-google vc-auth-disabled{sm}">'
            f'<span class="vc-auth-btn-icon vc-auth-g-icon">G</span> Google로 시작하기</span>'
        )

    if not k_ok and not g_ok and not compact:
        st.caption("소셜 로그인은 준비 중이에요 · **체험 계정**으로 바로 이용해 보세요")

    render_safe_html(
        """
        <div class="vc-auth-divider" aria-hidden="true">
            <span>또는</span>
        </div>
        """
    )

    demo_label = "✦ 체험 계정으로 시작" if not compact else "✦ 체험 계정"
    if st.button(demo_label, key=f"{key_prefix}_demo", use_container_width=True, type="primary"):
        from ui.auth import start_demo

        start_demo()


def render_login_hero(*, compact: bool = False) -> None:
    if compact:
        render_safe_html(
            """
            <div class="vc-login-hero vc-login-hero-compact">
                <div class="vc-login-logo-ring">🎤</div>
                <h2 class="vc-login-brand-title">로그인이 필요해요</h2>
                <p class="vc-login-brand-tag">분석·기록은 로그인 후 이용할 수 있어요</p>
            </div>
            """
        )
        return

    render_safe_html(
        """
        <div class="vc-login-hero">
            <div class="vc-login-logo-ring">🎤</div>
            <h1 class="vc-login-brand-title">Vocal Coach AI</h1>
            <p class="vc-login-brand-tag">AI 보컬 코치 · 무료 베타</p>
            <ul class="vc-login-benefits">
                <li><span>📊</span> 음정 · 박자 · 호흡 분석</li>
                <li><span>💬</span> AI 선생님 DM 코칭</li>
                <li><span>📈</span> 마이 페이지 기록 저장</li>
            </ul>
        </div>
        """
    )


def render_login_card(*, key_prefix: str = "login", compact: bool = False) -> None:
    render_login_hero(compact=compact)
    render_safe_html('<div class="vc-login-card-marker"></div>')
    with st.container(border=True):
        if not compact:
            render_safe_html('<p class="vc-login-card-heading">3초 만에 시작하기</p>'
            )
        render_auth_buttons(key_prefix=key_prefix, compact=compact)
        foot = (
            "가입 없이 체험 계정으로도 모든 기능을 써볼 수 있어요"
            if not compact
            else "체험 계정으로 바로 시작할 수 있어요"
        )
        render_safe_html(f'<p class="vc-login-footnote">{foot}</p>')
