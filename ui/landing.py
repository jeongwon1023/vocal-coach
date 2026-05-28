"""SHARE X + Yousician + Smule + Moises + SingSharp 스타일 랜딩."""

from __future__ import annotations

import streamlit as st

from ui.navigation import go_to


def render() -> None:
    from ui.auth import is_logged_in, render_landing_auth_banner

    if not is_logged_in():
        render_landing_auth_banner()

    st.markdown(
        """
        <section class="vc-hero-main">
            <div class="vc-hero-badge-row">
                <span class="vc-hero-pill">✦ 100% 무료 · 회원가입 30초</span>
                <span class="vc-hero-pill vc-hero-pill-live">
                    <span class="vc-live-dot"></span>지금 바로 1분 안에 결과
                </span>
            </div>
            <h1 class="vc-hero-h1">
                노래 실력,<br>
                <span class="vc-gradient-text">감 말고 점수</span>로 확인하세요
            </h1>
            <p class="vc-hero-lead">
                「나 잘 부르는 것 같은데…」 혼자 연습할 때 가장 답답하죠.<br>
                녹음 <b>한 번</b>만 올리거나 <b>마이크로 바로 녹음</b>하면 <b>음정 · 박자 · 호흡 · 음색</b> 점수와<br>
                선생님처럼 <b>「잘한 점 → 고칠 점 → 오늘 연습법」</b>을 DM으로 받아요.
            </p>
            <div class="vc-trust-row">
                <div class="vc-trust-item"><strong>~1분</strong><span>분석 완료</span></div>
                <div class="vc-trust-item"><strong>0원</strong><span>레슨비</span></div>
                <div class="vc-trust-item"><strong>4영역</strong><span>정밀 점수</span></div>
                <div class="vc-trust-item"><strong>24/7</strong><span>언제든</span></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    cta1, cta2 = st.columns([3, 1])
    with cta1:
        if st.button(
            "🎤 내 노래 무료 분석받기",
            type="primary",
            use_container_width=True,
            key="landing_cta",
        ):
            go_to("마이 페이지")
    with cta2:
        if st.button("성장 기록", use_container_width=True, key="landing_my"):
            go_to("마이 페이지")

    st.markdown(
        """
        <p class="vc-section-eyebrow">WHY NOW</p>
        <h2 class="vc-section-h2">혼자 연습할 때, 이런 순간 있지 않나요?</h2>
        <div class="vc-pain-grid">
            <div class="vc-pain-card">😶 「분명 맞게 부른 것 같은데, 왜 어색하지?」</div>
            <div class="vc-pain-card">🎧 「MR 깔고 불러도 원곡이랑 느낌이 달라」</div>
            <div class="vc-pain-card">📉 「매일 하는데 실력이 늘었는지 모르겠어」</div>
        </div>
        <p class="vc-section-sub">
            Vocal Coach AI는 <b>객관적인 점수</b>로 어디가 아쉬운지 보여 주고,
            <b>다음에 뭘 연습할지</b>까지 짚어 드려요. 레슨비 걱정 없이, 지금 바로.
        </p>

        <p class="vc-section-eyebrow">WHAT YOU GET</p>
        <h2 class="vc-section-h2">1분 뒤, 이런 결과를 받아요</h2>
        <div class="vc-tech-grid">
            <article class="vc-tech-card vc-tech-card-accent">
                <span class="vc-tech-icon">🎯</span>
                <h3>음정 · 멜로디</h3>
                <p>틀린 구간을 초 단위로 표시. 원곡 가이드와 비교해 「여기만 연습하면 돼」가 바로 보여요.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">⏱️</span>
                <h3>박자 · 리듬</h3>
                <p>박이 밀리는 구간, 프레이즈 타이밍까지 짚어 줘요. 메트로놈 없이도 약점이 보여요.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">🫁</span>
                <h3>호흡 · 음색</h3>
                <p>호흡이 흔들리는 구간, 목소리 톤의 차이를 수치로. 「예쁘게 부르는 법」의 힌트까지.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">💬</span>
                <h3>AI 코치 DM</h3>
                <p>분석 후 선생님이 DM처럼 코칭. 「10분 루틴 짜줘」처럼 궁금한 것도 바로 물어보세요.</p>
            </article>
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
                <small>약 1분 · 4영역 점수 + 그래프</small>
            </div>
            <div class="vc-step-arrow">→</div>
            <div class="vc-step-card">
                <span class="vc-step-num">03</span>
                <strong>맞춤 코칭</strong>
                <small>연습법 · 마이 페이지에 기록 저장</small>
            </div>
        </div>

        <div class="vc-featured-card">
            <span class="vc-featured-tag">🔥 가장 인기 있는 기능</span>
            <h3>유튜브 가이드 레슨</h3>
            <p>
                곡 제목만 입력하면 원곡 MR·가이드 보컬과 내 목소리를 비교해요.
                「원곡이랑 뭐가 다른지」 구간별로 알려 드립니다.
            </p>
        </div>

        <blockquote class="vc-testimonial">
            <p>「점수만 주는 게 아니라, <b>오늘 밤에 뭘 연습할지</b> 알려주는 나침반이에요.」</p>
            <cite>— 베타 테스터 · Vocal Coach AI</cite>
        </blockquote>

        <footer class="vc-footer">
            <p>VOCAL COACH AI · 레슨비 없이, 내 노래를 객관적으로 듣는 AI</p>
            <p class="vc-footer-sub">상단 로그인 · 카카오 · Google · 체험 계정으로 30초 만에 시작</p>
        </footer>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🎤 지금 내 노래 분석받기 — 무료", type="primary", use_container_width=True, key="landing_cta_bottom"):
        go_to("마이 페이지")
