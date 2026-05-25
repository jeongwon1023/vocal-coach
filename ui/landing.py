"""SHARE X + Yousician + Smule + Moises + SingSharp 스타일 랜딩."""

from __future__ import annotations

import streamlit as st

from ui.navigation import go_to


def render() -> None:
    st.markdown(
        """
        <section class="vc-hero-main">
            <div class="vc-hero-badge-row">
                <span class="vc-hero-pill">✦ 무료 AI 보컬 분석</span>
                <span class="vc-hero-pill vc-hero-pill-live">
                    <span class="vc-live-dot"></span>지금 바로 1분 안에 결과
                </span>
            </div>
            <h1 class="vc-hero-h1">
                내 노래,<br>
                <span class="vc-gradient-text">어디가 아쉬운지</span> 알려드릴게요
            </h1>
            <p class="vc-hero-lead">
                학원 1회 레슨비 없이, 녹음 한 번이면 끝.<br>
                <b>음정 · 박자 · 호흡 · 음색</b>을 AI가 듣고, 선생님처럼
                「잘한 점 → 고칠 점 → 연습법」 순서로 코칭해 드려요.
            </p>
            <div class="vc-trust-row">
                <div class="vc-trust-item"><strong>4</strong><span>분석 영역</span></div>
                <div class="vc-trust-item"><strong>~1분</strong><span>결과 확인</span></div>
                <div class="vc-trust-item"><strong>0원</strong><span>무료 체험</span></div>
                <div class="vc-trust-item"><strong>24/7</strong><span>언제든</span></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    cta1, cta2 = st.columns([3, 1])
    with cta1:
        if st.button(
            "🎤 무료로 분석 시작하기",
            type="primary",
            use_container_width=True,
            key="landing_cta",
        ):
            go_to("분석")
    with cta2:
        if st.button("성장 기록 보기", use_container_width=True, key="landing_my"):
            go_to("마이 페이지")

    st.markdown(
        """
        <p class="vc-section-eyebrow">WHY VOCAL COACH AI</p>
        <h2 class="vc-section-h2">혼자 연습할 때, 이런 고민 있지 않나요?</h2>
        <div class="vc-pain-grid">
            <div class="vc-pain-card">😶 「음정은 맞는 것 같은데… 뭔가 어색해」</div>
            <div class="vc-pain-card">🎧 「MR 깔고 불러도 원곡이랑 다른 느낌」</div>
            <div class="vc-pain-card">📉 「매일 하는데 실력이 늘었는지 모르겠어」</div>
        </div>
        <p class="vc-section-sub">
            Vocal Coach AI는 녹음을 <b>객관적으로</b> 들어 드리고,
            틀린 구간·연습 루틴까지 짚어 줍니다.
        </p>

        <p class="vc-section-eyebrow">FEATURES</p>
        <h2 class="vc-section-h2">이런 걸 한 번에 받아보세요</h2>
        <div class="vc-tech-grid">
            <article class="vc-tech-card vc-tech-card-accent">
                <span class="vc-tech-icon">🎯</span>
                <h3>음정 · 멜로디</h3>
                <p>틀린 구간을 초 단위로 표시. 원곡 가이드와 비교해 어디를 연습할지 바로 알 수 있어요.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">🫁</span>
                <h3>호흡 · 다이내믹</h3>
                <p>프레이즈마다 호흡이 흔들리는지, 크레센도는 자연스러운지 분석해요.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">🎨</span>
                <h3>음색 · 배음</h3>
                <p>목소리만의 톤과 프로급 발성의 차이를 수치로 보여 드려요.</p>
            </article>
            <article class="vc-tech-card">
                <span class="vc-tech-icon">📈</span>
                <h3>성장 기록</h3>
                <p>로그인하면 점수가 쌓여요. 같은 곡을 다시 불러도 얼마나 나아졌는지 비교.</p>
            </article>
        </div>

        <p class="vc-section-eyebrow">HOW IT WORKS</p>
        <h2 class="vc-section-h2">3단계면 끝나요</h2>
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
                <small>약 1분 · 음정·박자·호흡·음색</small>
            </div>
            <div class="vc-step-arrow">→</div>
            <div class="vc-step-card">
                <span class="vc-step-num">03</span>
                <strong>맞춤 코칭</strong>
                <small>연습법 · 마이 페이지 저장</small>
            </div>
        </div>

        <div class="vc-featured-card">
            <span class="vc-featured-tag">🔥 가장 많이 쓰는 기능</span>
            <h3>유튜브 가이드 레슨</h3>
            <p>
                곡 제목만 입력하면 원곡 MR·가이드 보컬과 내 목소리를 비교해요.
                「원곡이랑 뭐가 다른지」 구간별로 알려 드립니다.
            </p>
        </div>

        <blockquote class="vc-testimonial">
            <p>「점수 0점이 아니라, <b>다음에 연습할 것</b>을 알려주는 나침반이에요.」</p>
            <cite>— Vocal Coach AI · 보컬 선생님 철학</cite>
        </blockquote>

        <footer class="vc-footer">
            <p>VOCAL COACH AI · 보컬 학원을 대체하는 AI 레슨실</p>
            <p class="vc-footer-sub">Google · 카카오 로그인 · 체험 계정 지원</p>
        </footer>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🎤 지금 바로 무료 분석하기", type="primary", use_container_width=True, key="landing_cta_bottom"):
        go_to("분석")
