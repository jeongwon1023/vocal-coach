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


_HINTS: tuple[SongHint, ...] = (
    SongHint("밤편지", "아이유", "아이유 밤편지 MR instrumental vocal", "ballad", "발라드"),
    SongHint("사랑을 했다", "iKON", "iKON 사랑을 했다 MR", "hiphop", "힙합"),
    SongHint("Ditto", "NewJeans", "NewJeans Ditto instrumental", "hiphop", "K-Pop"),
    SongHint("Super Shy", "NewJeans", "NewJeans Super Shy instrumental", "hiphop", "K-Pop"),
    SongHint("Spring Day", "BTS", "BTS Spring Day MR", "ballad", "발라드"),
    SongHint("봄날", "BTS", "BTS 봄날 MR", "ballad", "발라드"),
    SongHint("Dynamite", "BTS", "BTS Dynamite instrumental", "hiphop", "K-Pop"),
    SongHint("Good Day", "아이유", "아이유 Good Day MR", "ballad", "발라드"),
    SongHint("너의 의미", "아이유", "아이유 너의 의미 MR", "ballad", "발라드"),
    SongHint("Blinding Lights", "The Weeknd", "Blinding Lights instrumental", "rock", "Pop"),
    SongHint("Someone Like You", "Adele", "Someone Like You piano instrumental", "ballad", "발라드"),
    SongHint("Shallow", "Lady Gaga", "Shallow instrumental karaoke", "ballad", "발라드"),
    SongHint("Bohemian Rhapsody", "Queen", "Bohemian Rhapsody instrumental", "rock", "락"),
    SongHint("Hotel California", "Eagles", "Hotel California instrumental", "rock", "락"),
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def lookup_song_hint(song_title: str | None) -> SongHint | None:
    if not song_title or not song_title.strip():
        return None
    q = _norm(song_title)
    for hint in _HINTS:
        if _norm(hint.title) in q or _norm(f"{hint.artist} {hint.title}") in q:
            return hint
        if _norm(hint.artist) in q and _norm(hint.title) in q:
            return hint
    return None


def apply_song_hints(song_title: str | None, session: dict) -> SongHint | None:
    """session dict-like (session_state)에 힌트 반영."""
    hint = lookup_song_hint(song_title)
    if not hint:
        return None
    if session.get("style_preset", "auto") == "auto":
        session["style_preset"] = hint.style_preset
    session["_song_hint"] = {
        "title": hint.title,
        "artist": hint.artist,
        "youtube_query": hint.youtube_query,
        "genre_label": hint.genre_label,
    }
    return hint
