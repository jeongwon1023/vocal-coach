"""
점수 피드백 → 임계값·가중치 자동 보정 (Phase 1, DL 없음).

「점수가 맞나요?」 agree/disagree JSON을 읽어 scoring_calibration.json 을 갱신하고
analysis.py 결과 점수에 소폭 반영합니다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
CALIBRATION_PATH = PROJECT_DIR / "records" / "feedback" / "scoring_calibration.json"
MIN_FEEDBACK_SAMPLES = 5
MAX_OVERALL_BIAS = 6.0
MAX_STAGE_BIAS = 4.0
MAX_GENEROSITY = 1.08
MIN_GENEROSITY = 0.94

_HIGH_KEYWORDS = ("너무 높", "과대", "깎", "낮춰", "과하게 높", "too high")
_LOW_KEYWORDS = ("낮", "짠", "안 맞", "안맞", "어렵", "불공", "까다", "too low", "strict")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


@dataclass
class ScoringCalibration:
    version: int = 1
    updated_at: str = ""
    samples_agree: int = 0
    samples_disagree: int = 0
    overall_bias: float = 0.0
    stage_bias: dict[str, float] = field(default_factory=lambda: {"1": 0.0, "2": 0.0, "3": 0.0})
    generosity: float = 1.0
    enabled: bool = True
    min_samples_met: bool = False
    notes: str = ""

    def summary_ko(self) -> str:
        if not self.min_samples_met:
            need = max(0, MIN_FEEDBACK_SAMPLES - self.samples_agree - self.samples_disagree)
            return f"피드백 {self.samples_agree + self.samples_disagree}건 — 보정 활성화까지 {need}건 더 필요"
        parts = [f"동의 {self.samples_agree} · 불일치 {self.samples_disagree}"]
        if abs(self.overall_bias) >= 0.05:
            parts.append(f"종합 보정 {self.overall_bias:+.1f}점")
        if abs(self.generosity - 1.0) >= 0.005:
            parts.append(f"관대도 ×{self.generosity:.3f}")
        return " · ".join(parts)


def default_calibration() -> ScoringCalibration:
    return ScoringCalibration(updated_at=_now_iso(), notes="초기값 (피드백 없음)")


def load_calibration() -> ScoringCalibration:
    if not CALIBRATION_PATH.exists():
        return default_calibration()
    try:
        raw = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        return ScoringCalibration(
            version=int(raw.get("version", 1)),
            updated_at=str(raw.get("updated_at") or ""),
            samples_agree=int(raw.get("samples_agree") or 0),
            samples_disagree=int(raw.get("samples_disagree") or 0),
            overall_bias=float(raw.get("overall_bias") or 0),
            stage_bias={str(k): float(v) for k, v in (raw.get("stage_bias") or {}).items()},
            generosity=float(raw.get("generosity") or 1.0),
            enabled=bool(raw.get("enabled", True)),
            min_samples_met=bool(raw.get("min_samples_met", False)),
            notes=str(raw.get("notes") or ""),
        )
    except Exception:
        return default_calibration()


def save_calibration(cal: ScoringCalibration) -> Path:
    CALIBRATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(cal)
    CALIBRATION_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return CALIBRATION_PATH


def _list_score_feedback() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from feedback_store import FEEDBACK_DIR

    agree_dir = FEEDBACK_DIR / "agree"
    disagree_dir = FEEDBACK_DIR / "disagree"
    agrees: list[dict[str, Any]] = []
    disagrees: list[dict[str, Any]] = []

    if agree_dir.exists():
        for p in agree_dir.glob("feedback_*.json"):
            try:
                agrees.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
    if disagree_dir.exists():
        for p in disagree_dir.glob("feedback_*.json"):
            try:
                disagrees.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
    return agrees, disagrees


def _comment_direction(comment: str) -> str:
    """disagree 코멘트 방향: low=점수 너무 낮다, high=너무 높다, unknown."""
    c = (comment or "").lower()
    if any(k in c for k in _HIGH_KEYWORDS):
        return "high"
    if any(k in c for k in _LOW_KEYWORDS):
        return "low"
    return "unknown"


def _stage_key(stage_scores: dict[str, Any] | None, stage: int) -> float | None:
    if not stage_scores:
        return None
    raw = stage_scores.get(str(stage), stage_scores.get(stage))
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def train_from_feedback() -> ScoringCalibration:
    """agree/disagree 피드백으로 calibration JSON 생성·저장."""
    agrees, disagrees = _list_score_feedback()
    n_a, n_d = len(agrees), len(disagrees)
    total = n_a + n_d

    cal = default_calibration()
    cal.samples_agree = n_a
    cal.samples_disagree = n_d
    cal.updated_at = _now_iso()

    if total < MIN_FEEDBACK_SAMPLES:
        cal.min_samples_met = False
        cal.notes = f"피드백 {total}건 — 최소 {MIN_FEEDBACK_SAMPLES}건 필요"
        save_calibration(cal)
        return cal

    cal.min_samples_met = True

    low_votes = 0
    high_votes = 0
    for item in disagrees:
        direction = _comment_direction(item.get("comment", ""))
        if direction == "high":
            high_votes += 1
        elif direction == "low":
            low_votes += 1
        else:
            low_votes += 1

    net_low = low_votes - high_votes
    overall_bias = net_low * 0.35 + (n_d - n_a * 0.25) * 0.12
    overall_bias = max(-3.0, min(MAX_OVERALL_BIAS, overall_bias))

    disagree_rate = n_d / total if total else 0.0
    generosity = 1.0 + max(0.0, disagree_rate - 0.25) * 0.12 - max(0.0, 0.25 - disagree_rate) * 0.04
    generosity = max(MIN_GENEROSITY, min(MAX_GENEROSITY, generosity))

    stage_acc = {"1": 0.0, "2": 0.0, "3": 0.0}
    stage_counts = {"1": 0, "2": 0, "3": 0}
    for item in disagrees:
        overall = float(item.get("overall_score") or 0)
        ss = item.get("stage_scores") or {}
        for stage in (1, 2, 3):
            s = _stage_key(ss, stage)
            if s is None or overall <= 0:
                continue
            gap = overall - s
            if gap > 12:
                stage_acc[str(stage)] += min(0.35, gap * 0.015)
                stage_counts[str(stage)] += 1

    stage_bias: dict[str, float] = {}
    for key in ("1", "2", "3"):
        cnt = stage_counts[key]
        bias = stage_acc[key] / cnt if cnt else 0.0
        stage_bias[key] = round(min(MAX_STAGE_BIAS, bias), 2)

    cal.overall_bias = round(overall_bias, 2)
    cal.stage_bias = stage_bias
    cal.generosity = round(generosity, 4)
    cal.notes = (
        f"자동 보정 — disagree {n_d}건 (낮음 {low_votes}/높음 {high_votes}), "
        f"generosity {cal.generosity:.3f}"
    )
    save_calibration(cal)
    return cal


def maybe_retrain_after_feedback() -> ScoringCalibration:
    """피드백 저장 직후 호출."""
    return train_from_feedback()


def apply_calibration_to_report(report: Any) -> ScoringCalibration:
    """CurriculumReport 점수에 calibration 반영 (in-place)."""
    cal = load_calibration()
    if not cal.enabled or not cal.min_samples_met:
        return cal

    for stage in getattr(report, "stages", []) or []:
        sid = getattr(stage, "stage", None)
        if sid not in (1, 2, 3, 4):
            continue
        bias = float(cal.stage_bias.get(str(sid), 0.0))
        if sid == 4:
            bias += cal.overall_bias * 0.35
        else:
            bias += cal.overall_bias * 0.12
        stage.score = _clamp_score(stage.score * cal.generosity + bias)

    report.overall_score = _clamp_score(report.overall_score * cal.generosity + cal.overall_bias)
    return cal
