#!/usr/bin/env python3
"""Supabase Kakao Provider 연동 상태 검증."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)


def _load_secrets() -> tuple[str | None, str | None]:
    url = os.environ.get("SUPABASE_URL", "").strip() or None
    key = os.environ.get("SUPABASE_KEY", "").strip() or None
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        for line in secrets_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "SUPABASE_URL" and not url:
                url = v
            if k == "SUPABASE_KEY" and not key:
                key = v
    return url, key


def main() -> int:
    url, key = _load_secrets()
    print("=== Vocal Coach · Kakao OAuth 검증 ===\n")
    if not url or not key:
        print("FAIL: SUPABASE_URL / SUPABASE_KEY 없음 (.streamlit/secrets.toml 확인)")
        return 1
    print(f"Supabase URL: {url}")

    try:
        from ui.supabase_client import is_supabase_key_format

        if not is_supabase_key_format(key):
            print("FAIL: SUPABASE_KEY 형식이 올바르지 않음 (placeholder 또는 짧은 키)")
            return 1
    except Exception as exc:
        print(f"WARN: 키 형식 검사 생략 ({exc})")

    settings_url = f"{url.rstrip('/')}/auth/v1/settings"
    try:
        resp = httpx.get(
            settings_url,
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"FAIL: Supabase 연결 실패 — {exc}")
        print("  → SUPABASE_KEY가 anon/publishable 실제 키인지 확인")
        return 1

    data = resp.json()
    external = data.get("external") or {}
    enabled = [name for name, on in external.items() if on]
    print(f"활성 Provider: {', '.join(enabled) or '(없음)'}")

    if "kakao" in enabled:
        print("\nOK: Kakao Provider가 Supabase에서 활성화되어 있습니다.")
        print("\n다음: 앱에서 로그인 → 카카오로 계속하기")
        return 0

    print("\nFAIL: Kakao Provider가 비활성화되어 있습니다.")
    print("  → Supabase Dashboard → Authentication → Providers → Kakao ON")
    print("  → Client ID = Kakao REST API Key")
    print("  → Client Secret = Kakao Client Secret")
    print(f"  → Kakao Redirect URI = {url.rstrip('/')}/auth/v1/callback")
    return 1


if __name__ == "__main__":
    sys.exit(main())
