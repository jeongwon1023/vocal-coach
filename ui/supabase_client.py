"""Supabase 클라이언트 — sb_publishable_* 키 지원 (supabase-py JWT 검증 우회)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase._sync.client import SyncClient

_JWT_KEY = re.compile(r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$")


def is_supabase_key_format(key: str) -> bool:
    key = (key or "").strip()
    if not key or len(key) < 30:
        return False
    lowered = key.lower()
    if "..." in key or "your-" in lowered or "xxxx" in lowered or "또는" in key:
        return False
    if key.startswith("eyJ"):
        return len(key) >= 100 and bool(_JWT_KEY.match(key))
    if key.startswith(("sb_publishable_", "sb_secret_")):
        return len(key) >= 30
    return bool(_JWT_KEY.match(key))


def create_supabase_client(url: str, key: str, *, storage) -> SyncClient:
    """
    supabase.create_client 래퍼.

    Supabase 대시보드의 publishable key(sb_publishable_...)는 supabase-py가
    JWT 형식만 허용해 거부하므로, SyncClient를 직접 조립합니다.
    """
    from supabase._sync.client import SupabaseException, SyncClient
    from supabase.lib.client_options import SyncClientOptions as ClientOptions

    url = url.strip().rstrip("/")
    key = key.strip()
    if not url:
        raise SupabaseException("supabase_url is required")
    if not key:
        raise SupabaseException("supabase_key is required")
    if not re.match(r"^(https?)://.+", url):
        raise SupabaseException("Invalid URL")
    if not is_supabase_key_format(key):
        raise SupabaseException(
            "Invalid API key — Supabase Dashboard → API → anon public key(eyJ...) 또는 publishable key를 확인하세요."
        )

    options = ClientOptions(storage=storage)
    client = SyncClient.__new__(SyncClient)
    client.supabase_url = url
    client.supabase_key = key
    client.options = options
    options.headers.update(client._get_auth_headers())
    client.rest_url = f"{url}/rest/v1"
    client.realtime_url = f"{url}/realtime/v1".replace("http", "ws")
    client.auth_url = f"{url}/auth/v1"
    client.storage_url = f"{url}/storage/v1"
    client.functions_url = f"{url}/functions/v1"
    client.auth = client._init_supabase_auth_client(
        auth_url=client.auth_url,
        client_options=options,
    )
    client.realtime = client._init_realtime_client(
        realtime_url=client.realtime_url,
        supabase_key=client.supabase_key,
        options=options.realtime if options else None,
    )
    client._postgrest = None
    client._storage = None
    client._functions = None
    client.auth.on_auth_state_change(client._listen_to_auth_events)
    return client
