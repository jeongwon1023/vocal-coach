"""인기곡 힌트 — JSON DB · 유튜브 검색어 · 장르 프리셋."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_DIR / "data" / "song_hints.json"


@dataclass(frozen=True)
class SongHint:
    title: str
    artist: str
    youtube_query: str
    style_preset: str = "auto"
    genre_label: str = ""
    aliases: tuple[str, ...] = ()


def _parse_hint(raw: dict) -> SongHint | None:
    title = (raw.get("title") or "").strip()
    artist = (raw.get("artist") or "").strip()
    query = (raw.get("youtube_query") or "").strip()
    if not title or not artist or not query:
        return None
    aliases = tuple(a.strip() for a in (raw.get("aliases") or []) if str(a).strip())
    return SongHint(
        title=title,
        artist=artist,
        youtube_query=query,
        style_preset=(raw.get("style_preset") or "auto").strip() or "auto",
        genre_label=(raw.get("genre_label") or "").strip(),
        aliases=aliases,
    )


@lru_cache(maxsize=8)
def _load_hints_from_path(path_str: str, mtime_ns: int) -> tuple[SongHint, ...]:
    path = Path(path_str)
    if not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    songs = data.get("songs") if isinstance(data, dict) else data
    if not isinstance(songs, list):
        return ()
    hints: list[SongHint] = []
    for item in songs:
        if not isinstance(item, dict):
            continue
        hint = _parse_hint(item)
        if hint:
            hints.append(hint)
    return tuple(hints)


def load_song_hints(db_path: Path | None = None) -> tuple[SongHint, ...]:
    """JSON 곡 DB 로드 — mtime 변경 시 자동 갱신."""
    path = db_path or DEFAULT_DB_PATH
    mtime_ns = int(path.stat().st_mtime_ns) if path.exists() else 0
    return _load_hints_from_path(str(path.resolve()), mtime_ns)


def reload_song_hints() -> tuple[SongHint, ...]:
    """DB 파일 변경 후 캐시 갱신."""
    _load_hints_from_path.cache_clear()
    return load_song_hints()


def _hints() -> tuple[SongHint, ...]:
    return load_song_hints()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def all_song_hints() -> tuple[SongHint, ...]:
    return _hints()


def format_song_label(hint: SongHint) -> str:
    return f"{hint.artist} — {hint.title}"


def _matches(hint: SongHint, q: str) -> bool:
    if _norm(hint.title) in q or _norm(f"{hint.artist} {hint.title}") in q:
        return True
    if _norm(hint.artist) in q and _norm(hint.title) in q:
        return True
    for alias in hint.aliases:
        if _norm(alias) in q:
            return True
    return False


def lookup_song_hint(song_title: str | None) -> SongHint | None:
    if not song_title or not song_title.strip():
        return None
    hints = _hints()
    if not hints:
        return None
    q = _norm(song_title)
    for hint in hints:
        if _matches(hint, q):
            return hint
    title_only = [h for h in hints if _norm(h.title) == q or q == _norm(h.title)]
    if len(title_only) == 1:
        return title_only[0]
    return None


def search_song_hints(query: str, *, limit: int = 8) -> list[SongHint]:
    """부분 일치 검색 — 자동완성용."""
    hints = _hints()
    q = _norm(query)
    if not q:
        return list(hints[:limit])
    scored: list[tuple[int, SongHint]] = []
    for hint in hints:
        hay = _norm(f"{hint.artist} {hint.title} {' '.join(hint.aliases)}")
        if q in hay:
            score = hay.index(q) if q in hay else 99
            scored.append((score, hint))
    scored.sort(key=lambda x: (x[0], x[1].title))
    return [h for _, h in scored[:limit]]


def unique_genres() -> tuple[str, ...]:
    genres = sorted({h.genre_label for h in _hints() if h.genre_label})
    return tuple(genres)


def filter_song_hints(
    query: str = "",
    *,
    genre: str | None = None,
    limit: int = 48,
) -> list[SongHint]:
    """검색 + 장르 필터."""
    hints = list(_hints())
    if genre and genre != "전체":
        hints = [h for h in hints if h.genre_label == genre]
    q = _norm(query)
    if q:
        filtered: list[SongHint] = []
        for hint in hints:
            hay = _norm(f"{hint.artist} {hint.title} {' '.join(hint.aliases)}")
            if q in hay:
                filtered.append(hint)
        hints = filtered
    return hints[:limit]


def apply_song_hints(song_title: str | None, session: dict) -> SongHint | None:
    """session dict-like (session_state)에 힌트 반영."""
    hint = lookup_song_hint(song_title)
    if not hint:
        session.pop("_song_hint", None)
        return None
    if session.get("style_preset", "auto") == "auto":
        session["style_preset"] = hint.style_preset
    session["_song_hint"] = {
        "title": hint.title,
        "artist": hint.artist,
        "youtube_query": hint.youtube_query,
        "genre_label": hint.genre_label,
    }
    if session.get("auto_youtube_on_hint", True):
        session["use_youtube"] = True
    return hint
