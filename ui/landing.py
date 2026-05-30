"""SHARE X + Yousician + Smule + Moises + SingSharp 스타일 랜딩."""

from __future__ import annotations

import streamlit as st

from ui.b2c_theme import landing_scroll_script, render_floating_cta
from ui.navigation import go_to
from ui.utils import render_safe_html


def render() -> None:
    from ui.auth import is_logged_in, render_landing_auth_banner

    if not is_logged_in():
        render_landing_auth_banner()

    render_safe_html("""
        <section id="vc-landing-hero" class="vc-landing-hero">
            <div class="vc-landing-hero-glow"></div>
            <div class="vc-landing-hero-inner">
                <span class="vc-hero-pill">✦ 100% 무료 · 회원가입 30초</span>
                <h1 class="vc-landing-hero-title">내 방 안의<br><span class="vc-gradient-text">프로 보컬 코치</span></h1>
                <p class="vc-landing-hero-lead">
                    당신의 목소리, 이제 감이 아닌 <b>'데이터'</b>로 진단하세요.<br>
                    마이크 하나면 <b>음정 · 박자 · 호흡 · 발성 · 표현력</b>까지 1분 안에.
                </p>
            </div>
        </section>
        """
    )

    if st.button(
        "👉 무료로 내 보컬 분석하기",
        type="primary",
        use_container_width=True,
        key="landing_hero_cta"
    ):
        go_to("마이 페이지")

    render_safe_html(
        """
        <div class="vc-trust-banner">
            <span class="vc-trust-banner-icon">🏆</span>
            <p class="vc-trust-banner-text">
                이미 <strong class="vc-count-up" data-target="12408" data-suffix="명">12,408명</strong>의 예비 보컬리스트가
                <br>자신의 진짜 목소리를 찾았습니다.
            </p>
        </div>
        """
    )

    render_safe_html(
        """
        <section class="vc-feature-banner">
            <p class="vc-section-eyebrow">FEATURES</p>
            <h2 class="vc-section-h2">마이크 하나면 끝 · 내 방안의 AI 코치</h2>
            <div class="vc-tech-grid">
                <article class="vc-tech-card vc-tech-card-accent">
                    <span class="vc-tech-icon">🎤</span>
                    <h3>1분 녹음 · 즉시 분석</h3>
                    <p>핸드폰 녹음만 올려도 음정·박자·호흡 점수와 코칭 리포트를 받아요.</p>
                </article>
                <article class="vc-tech-card">
                    <span class="vc-tech-icon">📊</span>
                    <h3>5축 레이더 차트</h3>
                    <p>게임 스탯처럼 보컬 밸런스를 한눈에. 어디를 연습할지 바로 보여요.</p>
                </article>
                <article class="vc-tech-card">
                    <span class="vc-tech-icon">💬</span>
                    <h3>AI 코치 DM</h3>
                    <p>「10분 루틴 짜줘」처럼 궁금한 것도 선생님처럼 1:1로 답해 드려요.</p>
                </article>
            </div>
        </section>
        """
    )

    render_safe_html(
        """
        <p class="vc-section-eyebrow">WHY NOW</p>
        <h2 class="vc-section-h2">혼자 연습할 때, 이런 순간 있지 않나요?</h2>
        <div class="vc-pain-grid">
            <div class="vc-pain-card">😶 「분명 맞게 부른 것 같은데, 왜 어색하지?」</div>
            <div class="vc-pain-card">🎧 「MR 깔고 불러도 원곡이랑 느낌이 달라」</div>
            <div class="vc-pain-card">📉 「매일 하는데 실력이 늘었는지 모르겠어」</div>
        </div>

        <p class="vc-section-eyebrow">HOW IT WORKS</p>
        <h2 class="vc-section-h2">딱 3단계 · 1분이면 끝</h2>
        <div class="vc-steps-row">
            <div class="vc-step-card">
                <span class="vc-step-num">01</span>
                <strong>녹음 업로드</strong>
                <small>핸드폰 녹음 · MR · 유튜브 추출물 OK</small>
            </div>
            <div class="vc-step-arrow">→</div>
            <div class="vc-step-card">
                <span class="vc-step-num">02</span>
                <strong>AI 분석</strong>
                <small>약 1분 · 5축 스탯 + 그래프</small>
            </div>
            <div class="vc-step-arrow">→</div>
            <div class="vc-step-card">
                <span class="vc-step-num">03</span>
                <strong>맞춤 코칭</strong>
                <small>연습법 · 마이 페이지에 기록 저장</small>
            </div>
        </div>

        <blockquote class="vc-testimonial">
            <p>「점수만 주는 게 아니라, <b>오늘 밤에 뭘 연습할지</b> 알려주는 나침반이에요.」</p>
            <cite>— 베타 테스터 · Vocal Coach AI</cite>
        </blockquote>

        <footer class="vc-footer">
            <p>VOCAL COACH AI · 레슨비 없이, 내 노래를 객관적으로 듣는 AI</p>
            <p class="vc-footer-sub">상단 로그인 · 카카오 · Google · 체험 계정으로 30초 만에 시작</p>
        </footer>
        """
    )

    if st.button("🎤 지금 내 노래 분석받기 — 무료", type="primary", use_container_width=True, key="landing_cta_bottom"):
        go_to("마이 페이지")

    render_floating_cta(variant="landing")
    render_safe_html(landing_scroll_script())
