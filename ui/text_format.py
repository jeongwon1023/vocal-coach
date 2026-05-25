"""코칭·채팅 텍스트 줄바꿈·가독성."""

from __future__ import annotations

import re

_CIRCLED = re.compile(r"([①②③④⑤⑥⑦⑧⑨⑩])")
_NUMBERED = re.compile(r"(?<=\S)\s+(\d+[.)]\s)")


def format_step_lines(text: str) -> str:
    """①②③·1. 2. 목록을 줄바꿈으로 분리."""
    if not text:
        return ""
    t = text.strip()
    t = _CIRCLED.sub(r"\n\n\1", t)
    t = _NUMBERED.sub(r"\n\n\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def format_readable_paragraphs(text: str) -> str:
    """긴 문장·섹션 이모지 앞 줄바꿈."""
    t = format_step_lines(text)
    for token in ("🌟", "🎯", "📊", "📋", "🎤", "📅", "💡"):
        t = t.replace(f"\n{token}", f"\n\n{token}")
    t = re.sub(r"\n(\d+\.\s+\*\*)", r"\n\n\1", t)
    t = re.sub(r"\n(·\s+\*\*)", r"\n\n\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
