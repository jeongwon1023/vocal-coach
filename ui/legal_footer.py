"""법무 · 프라이버시 · 베타 안내."""

from __future__ import annotations

import os

import streamlit as st

from ui.utils import render_safe_html

DEFAULT_TERMS_URL = os.environ.get(
    "VC_TERMS_URL",
    "https://www.notion.so/",
)
DEFAULT_PRIVACY_URL = os.environ.get(
    "VC_PRIVACY_URL",
    "https://www.notion.so/",
)
DEFAULT_FEEDBACK_URL = os.environ.get(
    "VC_FEEDBACK_FORM_URL",
    "https://forms.gle/",
)


def _secret_url(name: str, default: str) -> str:
    try:
        if name in st.secrets:
            v = str(st.secrets[name]).strip()
            if v:
                return v
    except Exception:
        pass
    return default


def terms_url() -> str:
    return _secret_url("TERMS_URL", DEFAULT_TERMS_URL)


def privacy_url() -> str:
    return _secret_url("PRIVACY_URL", DEFAULT_PRIVACY_URL)


def feedback_form_url() -> str:
    return _secret_url("FEEDBACK_FORM_URL", DEFAULT_FEEDBACK_URL)


def render_beta_data_warning() -> None:
    """Streamlit Cloud 재부팅 시 로컬 기록 소실 안내."""
    render_safe_html(
        """
        <div class="vc-beta-data-warn">
            <span>⚠️</span>
            <p><b>베타 안내</b> · 재배포·서버 재시작 시 기기에 저장된 분석 기록이 초기화될 수 있습니다.
            중요한 결과는 <b>PDF 저장</b> 또는 <b>로그인 후 클라우드 동기화</b>를 권장합니다.</p>
        </div>
        """
    )


def render_upload_privacy_notice() -> None:
    render_safe_html(
        """
        <p class="vc-upload-privacy">
            🔒 업로드한 음성은 <b>보컬 분석 목적</b>으로만 처리되며 AI 학습에 사용되지 않습니다.
            MR·반주 포함 시 <b>저작권 책임은 업로더</b>에게 있습니다.
        </p>
        """
    )


def render_legal_footer(*, compact: bool = False) -> None:
    t = terms_url()
    p = privacy_url()
    f = feedback_form_url()
    if compact:
        render_safe_html(
            f"""
            <p class="vc-legal-footer vc-legal-compact">
                <a href="{t}" target="_blank" rel="noopener">이용약관</a>
                · <a href="{p}" target="_blank" rel="noopener">개인정보처리방침</a>
                · <a href="{f}" target="_blank" rel="noopener">피드백</a>
            </p>
            """
        )
        return
    render_safe_html(
        f"""
        <div class="vc-legal-footer-block">
            <p class="vc-legal-footer">
                <a href="{t}" target="_blank" rel="noopener">이용약관</a>
                · <a href="{p}" target="_blank" rel="noopener">개인정보처리방침</a>
            </p>
            <p class="vc-legal-caption">
                녹음 파일은 분석 후 서버에 영구 보관하지 않으며, 베타 기간 중 기록이 초기화될 수 있습니다.
            </p>
        </div>
        """
    )


def render_result_feedback_banner() -> None:
    """결과 페이지 — 마찰 없는 피드백."""
    url = feedback_form_url()
    render_safe_html(
        f"""
        <div class="vc-feedback-banner">
            <p>점수가 이상한가요? 30초만 투자해 주세요 🙏</p>
            <a class="vc-feedback-link" href="{url}" target="_blank" rel="noopener">
                피드백 남기기 →
            </a>
        </div>
        """
    )
