"""코칭·채팅 텍스트 줄바꿈·가독성."""

from __future__ import annotations

import html
import re

_CIRCLED = re.compile(r"([①②③④⑤⑥⑦⑧⑨⑩])")
_NUMBERED = re.compile(r"(?<=\S)\s+(\d+[.)]\s)")
_SECTION_EMOJI: tuple[tuple[str, str], ...] = (
    ("🌟", "good"),
    ("🎯", "focus"),
    ("📊", "stats"),
    ("📋", "routine"),
    ("📅", "check"),
    ("💡", "tip"),
    ("🎤", "coach")
)


def format_step_lines(text: str) -> str:
    """①②③·1. 2. 목록을 줄바꿈으로 분리."""
    if not text:
        return ""
    t = text.strip()
    t = _CIRCLED.sub(r"\n\n\1", t)
    t = _NUMBERED.sub(r"\n\n\1", t)
    # "1. " "2. " at line start after long paragraph
    t = re.sub(r"(?<=\S)\s+(?=\d+[.)]\s)", "\n\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def normalize_markdown_noise(text: str) -> str:
    """취소선·구분선·시간대 tilde 깨짐 제거."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"~~([^~]*?)~~", r"\1", t)
    t = t.replace("~~", "")
    t = re.sub(r"^\s*[-*_]{3,}\s*.*$", "", t, flags=re.M)
    t = re.sub(r"\n[-*_]{3,}\s*", "\n", t)
    t = re.sub(r"(\d+)~(\d+)", r"\1–\2", t)
    return t.strip()


def _md_inline(text: str) -> str:
    esc = html.escape(text or "")
    esc = re.sub(r"\*\*(.+?)\*\*", r'<strong class="vc-coach-strong">\1</strong>', esc)
    return esc


def format_coach_rich_html(text: str) -> str:
    """코칭 탭용 — 줄바꿈·단계 화살표·섹션 색상."""
    t = sanitize_coach_text(normalize_markdown_noise(text))
    if not t:
        return ""
    t = format_readable_paragraphs(t)

    blocks: list[str] = []
    step_num = 0

    for para in re.split(r"\n\n+", t):
        para = para.strip()
        if not para:
            continue

        sec_class = ""
        for emoji, cls in _SECTION_EMOJI:
            if para.startswith(emoji):
                sec_class = f" vc-coach-sec-{cls}"
                break

        lines_html: list[str] = []
        for line in para.split("\n"):
            line = line.strip()
            if not line:
                continue

            if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", line) or re.match(r"^\d+[.)]\s", line):
                step_num += 1
                body = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", line)
                body = re.sub(r"^\d+[.)]\s*", "", body)
                lines_html.append(
                    f'<p class="vc-coach-step">'
                    f'<span class="vc-coach-step-n">→ {step_num}</span>'
                    f"<span>{_md_inline(body)}</span></p>"
                )
            elif line.startswith("· ") or line.startswith("• "):
                lines_html.append(f'<p class="vc-coach-bullet">{_md_inline(line[2:].strip())}</p>')
            elif line.startswith("**") and "**" in line[2:]:
                lines_html.append(f'<p class="vc-coach-headline">{_md_inline(line)}</p>')
            elif any(line.startswith(e) for e, _ in _SECTION_EMOJI):
                lines_html.append(f'<p class="vc-coach-sec-title">{_md_inline(line)}</p>')
            else:
                lines_html.append(f'<p class="vc-coach-line">{_md_inline(line)}</p>')

        if lines_html:
            blocks.append(f'<div class="vc-coach-sec{sec_class}">{"".join(lines_html)}</div>')

    if not blocks:
        return f'<div class="vc-coach-rich"><p class="vc-coach-line">{_md_inline(t)}</p></div>'
    return f'<div class="vc-coach-rich">{"".join(blocks)}</div>'


def solution_to_checklist(text: str) -> str:
    """①②③·번호 목록 → 마크다운 체크리스트."""
    if not text:
        return ""
    t = format_step_lines(text.strip())
    items: list[str] = []
    for line in re.split(r"\n+", t):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        line = line.strip(" ·-")
        if line:
            items.append(f"- [ ] {line}")
    return "\n".join(items) if items else t


def normalize_checklist_markdown(text: str) -> str:
    """`- [ ]` 항목마다 줄바꿈 보장 — 한 줄로 붙는 마크다운 깨짐 방지."""
    if not text:
        return ""
    t = text.replace("\\n", "\n").strip()
    t = re.sub(r"(?<=\S)\s*-\s*\[\s*\]\s*", "\n- [ ] ", t)
    t = re.sub(r"^\s*-\s*\[\s*\]\s*", "- [ ] ", t, flags=re.M)
    lines: list[str] = []
    for raw in t.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith("- [ ]"):
            line = f"- [ ] {line.lstrip('- ').strip()}"
        lines.append(line)
    return "\n".join(lines)


_ENGINEER_PATTERNS = (
    (re.compile(r"Superflux[^.]*\.?", re.I), ""),
    (re.compile(r"Böck\s*2013[^.]*\.?", re.I), ""),
    (re.compile(r"Bock\s*2013[^.]*\.?", re.I), ""),
    (re.compile(r"\(논문[^)]*\)", re.I), ""),
    (re.compile(r"박\s*간격\s*들쭉날쭉\s*지수\s*[\d.]+", re.I), "리듬의 그루브가 흔들림"),
    (re.compile(r"박\s*간격\s*지수\s*[\d.]+[^.]*", re.I), "박자가 비교적 안정적"),
    (re.compile(r"\(지수\s*[\d.]+[^)]*\)", re.I), ""),
    (re.compile(r"지수\s*[\d.]+\s*,?\s*목표\s*[\d.]+\s*이하", re.I), ""),
    (re.compile(r"소리\s*뱉는\s*타이밍", re.I), "음을 시작하는 첫 타점")
)


def sanitize_coach_text(text: str) -> str:
    """유저 화면 — 논문명·내부 지수 등 엔지니어 언어 제거."""
    if not text:
        return ""
    t = text.strip()
    for pat, repl in _ENGINEER_PATTERNS:
        t = pat.sub(repl, t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\(\s*\)", "", t)
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
