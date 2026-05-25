"""
OAuth 로그인 서버 — Google · Kakao

실행: uvicorn auth_server:app --port 8001
또는 run_web.bat (자동 기동)
"""

from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from auth_service import (  # noqa: E402
    auth_base_url,
    create_session,
    find_or_create_oauth_user,
    google_configured,
    kakao_configured,
    streamlit_url,
)
from gpt_coach import load_dotenv_if_present  # noqa: E402

load_dotenv_if_present(PROJECT_DIR)

app = FastAPI(title="Vocal Coach Auth", version="1.0.0")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"


def _redirect_back(token: str) -> RedirectResponse:
    base = streamlit_url()
    q = urllib.parse.urlencode({"token": token})
    return RedirectResponse(url=f"{base}?{q}")


@app.get("/health")
def health():
    return {
        "ok": True,
        "google": google_configured(),
        "kakao": kakao_configured(),
    }


@app.get("/auth/google")
def auth_google():
    if not google_configured():
        raise HTTPException(
            503,
            "Google OAuth 미설정. .env에 GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET 추가",
        )
    redirect_uri = f"{auth_base_url()}/auth/google/callback"
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@app.get("/auth/google/callback")
async def auth_google_callback(code: str | None = None, error: str | None = None):
    if error or not code:
        raise HTTPException(400, error or "인증 취소")
    redirect_uri = f"{auth_base_url()}/auth/google/callback"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(400, "Google 토큰 교환 실패")
        access = token_resp.json().get("access_token")
        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access}"},
        )
    if user_resp.status_code != 200:
        raise HTTPException(400, "Google 사용자 정보 실패")
    info = user_resp.json()
    user = find_or_create_oauth_user(
        provider="google",
        provider_uid=str(info.get("id", "")),
        name=info.get("name") or "Google 사용자",
        email=info.get("email"),
        avatar_url=info.get("picture"),
    )
    return _redirect_back(create_session(user.id))


@app.get("/auth/kakao")
def auth_kakao():
    if not kakao_configured():
        raise HTTPException(
            503,
            "Kakao OAuth 미설정. .env에 KAKAO_REST_API_KEY 추가",
        )
    redirect_uri = f"{auth_base_url()}/auth/kakao/callback"
    params = {
        "client_id": os.environ["KAKAO_REST_API_KEY"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
    }
    url = KAKAO_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@app.get("/auth/kakao/callback")
async def auth_kakao_callback(code: str | None = None, error: str | None = None):
    if error or not code:
        raise HTTPException(400, error or "인증 취소")
    redirect_uri = f"{auth_base_url()}/auth/kakao/callback"
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": os.environ["KAKAO_REST_API_KEY"],
                "redirect_uri": redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(400, "Kakao 토큰 교환 실패")
        access = token_resp.json().get("access_token")
        user_resp = await client.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access}"},
        )
    if user_resp.status_code != 200:
        raise HTTPException(400, "Kakao 사용자 정보 실패")
    info = user_resp.json()
    kakao_account = info.get("kakao_account") or {}
    profile = kakao_account.get("profile") or {}
    user = find_or_create_oauth_user(
        provider="kakao",
        provider_uid=str(info.get("id", "")),
        name=profile.get("nickname") or "카카오 사용자",
        email=kakao_account.get("email"),
        avatar_url=profile.get("profile_image_url"),
    )
    return _redirect_back(create_session(user.id))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("auth_server:app", host="0.0.0.0", port=8001, reload=True)
