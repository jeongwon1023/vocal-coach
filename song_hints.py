"""인기곡 힌트 — 유튜브 검색어 · 장르 프리셋 (경량 곡 DB)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SongHint:
    title: str
    artist: str
    youtube_query: str
    style_preset: str = "auto"
    genre_label: str = ""
    aliases: tuple[str, ...] = ()


def _h(
    title: str,
    artist: str,
    query: str,
    preset: str = "auto",
    genre: str = "",
    *aliases: str,
) -> SongHint:
    return SongHint(title, artist, query, preset, genre, aliases)


_HINTS: tuple[SongHint, ...] = (
    # 발라드 · K-Pop
    _h("밤편지", "아이유", "아이유 밤편지 MR instrumental vocal", "ballad", "발라드"),
    _h("Good Day", "아이유", "아이유 Good Day MR", "ballad", "발라드", "굿데이"),
    _h("너의 의미", "아이유", "아이유 너의 의미 MR", "ballad", "발라드"),
    _h("Celebrity", "아이유", "아이유 Celebrity instrumental", "ballad", "K-Pop", "셀러브리티"),
    _h("Love poem", "아이유", "아이유 Love poem MR", "ballad", "발라드", "러브 poem", "러브포엠"),
    _h("사랑을 했다", "iKON", "iKON 사랑을 했다 MR", "hiphop", "힙합"),
    _h("Ditto", "NewJeans", "NewJeans Ditto instrumental", "hiphop", "K-Pop"),
    _h("Super Shy", "NewJeans", "NewJeans Super Shy instrumental", "hiphop", "K-Pop"),
    _h("Hype Boy", "NewJeans", "NewJeans Hype Boy instrumental", "hiphop", "K-Pop"),
    _h("Attention", "NewJeans", "NewJeans Attention instrumental", "hiphop", "K-Pop"),
    _h("Spring Day", "BTS", "BTS Spring Day MR", "ballad", "발라드"),
    _h("봄날", "BTS", "BTS 봄날 MR", "ballad", "발라드"),
    _h("Dynamite", "BTS", "BTS Dynamite instrumental", "hiphop", "K-Pop"),
    _h("Butter", "BTS", "BTS Butter instrumental", "hiphop", "K-Pop"),
    _h("Permission to Dance", "BTS", "BTS Permission to Dance instrumental", "hiphop", "K-Pop"),
    _h("How You Like That", "BLACKPINK", "BLACKPINK How You Like That instrumental", "hiphop", "K-Pop"),
    _h("Kill This Love", "BLACKPINK", "BLACKPINK Kill This Love MR", "hiphop", "K-Pop"),
    _h("Cheer Up", "TWICE", "TWICE Cheer Up instrumental", "hiphop", "K-Pop", "치어업"),
    _h("Feel Special", "TWICE", "TWICE Feel Special instrumental", "ballad", "K-Pop"),
    _h("ANTIFRAGILE", "LE SSERAFIM", "LE SSERAFIM ANTIFRAGILE instrumental", "hiphop", "K-Pop"),
    _h("UNFORGIVEN", "LE SSERAFIM", "LE SSERAFIM UNFORGIVEN instrumental", "hiphop", "K-Pop"),
    _h("Supernova", "aespa", "aespa Supernova instrumental", "hiphop", "K-Pop", "슈퍼노바"),
    _h("Drama", "aespa", "aespa Drama instrumental", "hiphop", "K-Pop", "드라마"),
    _h("Tomboy", "(G)I-DLE", "(G)I-DLE Tomboy instrumental", "hiphop", "K-Pop", "톰보이"),
    _h("Queencard", "(G)I-DLE", "(G)I-DLE Queencard instrumental", "hiphop", "K-Pop", "퀸카"),
    _h("God's Menu", "Stray Kids", "Stray Kids God's Menu instrumental", "hiphop", "K-Pop", "神메뉴"),
    _h("Love Shot", "EXO", "EXO Love Shot MR", "hiphop", "K-Pop", "러브샷"),
    _h("Eyes, Nose, Lips", "태양", "Taeyang Eyes Nose Lips MR", "ballad", "R&B", "눈코입"),
    _h("양화대교", "Zion.T", "Zion.T Yanghwa Bridge MR", "hiphop", "힙합", "Yanghwa Bridge"),
    _h("어떻게 이별을 준비하겠어", "AKMU", "AKMU How can I love the heart MR", "ballad", "발라드"),
    _h("Gangnam Style", "PSY", "PSY Gangnam Style instrumental", "hiphop", "K-Pop", "강남스타일"),
    _h("첫눈처럼 너에게 가겠다", "에일리", "Ailee I Will Go To You Like the First Snow MR", "ballad", "발라드", "첫눈"),
    _h("All I Want for Christmas Is You", "Mariah Carey", "All I Want for Christmas Is You karaoke", "ballad", "Pop"),
    # Pop · Rock · Western
    _h("Blinding Lights", "The Weeknd", "Blinding Lights instrumental", "rock", "Pop"),
    _h("Someone Like You", "Adele", "Someone Like You piano instrumental", "ballad", "발라드"),
    _h("Shallow", "Lady Gaga", "Shallow instrumental karaoke", "ballad", "발라드"),
    _h("Bohemian Rhapsody", "Queen", "Bohemian Rhapsody instrumental", "rock", "락"),
    _h("Hotel California", "Eagles", "Hotel California instrumental", "rock", "락"),
    _h("Perfect", "Ed Sheeran", "Ed Sheeran Perfect piano instrumental", "ballad", "Pop"),
    _h("Shape of You", "Ed Sheeran", "Ed Sheeran Shape of You instrumental", "hiphop", "Pop"),
    _h("Rolling in the Deep", "Adele", "Adele Rolling in the Deep instrumental", "rock", "Pop"),
    _h("My Heart Will Go On", "Celine Dion", "My Heart Will Go On instrumental karaoke", "ballad", "발라드"),
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def all_song_hints() -> tuple[SongHint, ...]:
    return _HINTS


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
    q = _norm(song_title)
    for hint in _HINTS:
        if _matches(hint, q):
            return hint
    # 제목만 입력한 경우 (예: "Ditto")
    title_only = [h for h in _HINTS if _norm(h.title) == q or q == _norm(h.title)]
    if len(title_only) == 1:
        return title_only[0]
    return None


def search_song_hints(query: str, *, limit: int = 8) -> list[SongHint]:
    """부분 일치 검색 — 자동완성용."""
    q = _norm(query)
    if not q:
        return list(_HINTS[:limit])
    scored: list[tuple[int, SongHint]] = []
    for hint in _HINTS:
        hay = _norm(f"{hint.artist} {hint.title} {' '.join(hint.aliases)}")
        if q in hay:
            score = hay.index(q) if q in hay else 99
            scored.append((score, hint))
    scored.sort(key=lambda x: (x[0], x[1].title))
    return [h for _, h in scored[:limit]]


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
