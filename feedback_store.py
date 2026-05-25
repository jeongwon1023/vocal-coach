"""
사용자 피드백 저장 — 점수 알고리즘 지속 개선용.

「점수가 실력과 맞나요?」 응답을 수집해
사람이 듣기에 좋은데 낮게 나온 케이스를 추후 보정합니다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

PROJECT_DIR = Path(__file__).resolve().parent
FEEDBACK_DIR = PROJECT_DIR / "records" / "feedback"
DISAGREE_DIR = FEEDBACK_DIR / "disagree"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def save_feedback(
    *,
    agrees: bool,
    record_id: str | None = None,
    overall_score: float | None = None,
    stage_scores: dict[str, Any] | None = None,
    song_title: str | None = None,
    style_preset: str | None = None,
    comment: str = "",
    record_snapshot: dict[str, Any] | None = None,
) -> Path:
    """
    피드백 JSON 저장.
    agrees=False → disagree/ 하위에 별도 보관 (학습·보정용).
    """
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    if not agrees:
        DISAGREE_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "feedback_id": uuid4().hex[:12],
        "recorded_at": _now_iso(),
        "agrees": agrees,
        "record_id": record_id,
        "overall_score": overall_score,
        "stage_scores": stage_scores,
        "song_title": song_title,
        "style_preset": style_preset,
        "comment": (comment or "").strip(),
    }
    if not agrees and record_snapshot:
        entry["record_snapshot"] = record_snapshot

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sub = "agree" if agrees else "disagree"
    base = DISAGREE_DIR if not agrees else FEEDBACK_DIR / "agree"
    base.mkdir(parents=True, exist_ok=True)
    fname = f"feedback_{sub}_{stamp}_{entry['feedback_id']}.json"
    path = base / fname
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_disagree_feedback(limit: int = 50) -> list[dict[str, Any]]:
    """보정·GPT 학습용 — 점수 불일치 케이스."""
    if not DISAGREE_DIR.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(DISAGREE_DIR.glob("feedback_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def feedback_stats() -> dict[str, int]:
    agree = len(list((FEEDBACK_DIR / "agree").glob("feedback_*.json"))) if (FEEDBACK_DIR / "agree").exists() else 0
    disagree = len(list(DISAGREE_DIR.glob("feedback_*.json"))) if DISAGREE_DIR.exists() else 0
    beta = len(list((FEEDBACK_DIR / "beta").glob("beta_*.json"))) if (FEEDBACK_DIR / "beta").exists() else 0
    return {"agree": agree, "disagree": disagree, "beta": beta, "total": agree + disagree + beta}


def save_beta_feedback(
    *,
    message: str,
    category: str,
    rating: int | None = None,
    user_id: str | None = None,
    user_name: str | None = None,
    page: str | None = None,
    contact: str | None = None,
) -> Path:
    """베타 사용자 피드백 — 버그 · 기능 · UX · 분석 품질."""
    beta_dir = FEEDBACK_DIR / "beta"
    beta_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "feedback_id": uuid4().hex[:12],
        "recorded_at": _now_iso(),
        "type": "beta",
        "category": category,
        "rating": rating,
        "message": (message or "").strip(),
        "user_id": user_id,
        "user_name": user_name,
        "page": page,
        "contact": (contact or "").strip() or None,
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = beta_dir / f"beta_{stamp}_{entry['feedback_id']}.json"
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_beta_feedback(limit: int = 30) -> list[dict[str, Any]]:
    beta_dir = FEEDBACK_DIR / "beta"
    if not beta_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(beta_dir.glob("beta_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out
