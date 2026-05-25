"""
OAuth 인증 — Google · Kakao · 로컬 세션.

FastAPI auth_server.py 와 Streamlit app.py 가 공유합니다.
환경 변수 (.env):
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
  KAKAO_REST_API_KEY
  AUTH_SECRET (세션 서명, 임의 문자열)
  AUTH_BASE_URL=http://localhost:8001
  STREAMLIT_URL=http://localhost:8501
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
USERS_DIR = PROJECT_DIR / ".cache" / "users"
SESSIONS_DIR = PROJECT_DIR / ".cache" / "sessions"


@dataclass
class User:
    id: str
    name: str
    email: str | None
    provider: str  # google | kakao | demo
    avatar_url: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def auth_base_url() -> str:
    return os.environ.get("AUTH_BASE_URL", "http://localhost:8001").rstrip("/")


def streamlit_url() -> str:
    return os.environ.get("STREAMLIT_URL", "http://localhost:8501").rstrip("/")


def google_configured() -> bool:
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))


def kakao_configured() -> bool:
    return bool(os.environ.get("KAKAO_REST_API_KEY"))


def _user_path(user_id: str) -> Path:
    return USERS_DIR / f"{user_id}.json"


def save_user(user: User) -> None:
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    if not user.created_at:
        user.created_at = _now_iso()
    _user_path(user.id).write_text(
        json.dumps(user.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_user(user_id: str) -> User | None:
    path = _user_path(user_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return User(**data)
    except Exception:
        return None


def find_or_create_oauth_user(
    *,
    provider: str,
    provider_uid: str,
    name: str,
    email: str | None,
    avatar_url: str | None,
) -> User:
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(f"{provider}:{provider_uid}".encode()).hexdigest()[:16]
    user_id = f"{provider}_{digest}"

    existing = load_user(user_id)
    if existing:
        existing.name = name or existing.name
        existing.email = email or existing.email
        existing.avatar_url = avatar_url or existing.avatar_url
        save_user(existing)
        return existing

    user = User(
        id=user_id,
        name=name or "보컬 학습자",
        email=email,
        provider=provider,
        avatar_url=avatar_url,
        created_at=_now_iso(),
    )
    save_user(user)
    return user


def create_demo_user(name: str = "체험 학습자") -> User:
    user_id = f"demo_{uuid.uuid4().hex[:10]}"
    user = User(
        id=user_id,
        name=name,
        email=None,
        provider="demo",
        created_at=_now_iso(),
    )
    save_user(user)
    return user


def create_session(user_id: str) -> str:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    path = SESSIONS_DIR / f"{token}.json"
    path.write_text(
        json.dumps({"user_id": user_id, "created_at": _now_iso()}, ensure_ascii=False),
        encoding="utf-8",
    )
    return token


def resolve_session(token: str | None) -> User | None:
    if not token:
        return None
    path = SESSIONS_DIR / f"{token}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return load_user(data["user_id"])
    except Exception:
        return None


def delete_session(token: str) -> None:
    path = SESSIONS_DIR / f"{token}.json"
    path.unlink(missing_ok=True)


def user_records_dir(user_id: str) -> Path:
    d = PROJECT_DIR / "records" / "users" / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d
