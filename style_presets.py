"""
가창 스타일별 평가 프로필 — 발라드 / 락 / 힙합.

장르마다 중요한 요소가 다르므로 Stage 가중치·허용치를 분리합니다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StylePreset:
    id: str
    label: str
    stage_weights: tuple[float, float, float]  # pitch, rhythm, breath/timbre
    melody_match_cents: float = 35.0
    rhythm_cv_target: float = 0.28
    timing_tolerance_ms: float = 80.0
    pro_score_floor: float = 72.0
    description: str = ""


PRESETS: dict[str, StylePreset] = {
    "auto": StylePreset(
        id="auto",
        label="자동 (곡 제목 추론)",
        stage_weights=(0.40, 0.30, 0.30),
        description="곡 제목·키워드로 발라드/락/힙합을 추론합니다.",
    ),
    "ballad": StylePreset(
        id="ballad",
        label="발라드",
        stage_weights=(0.60, 0.20, 0.20),
        melody_match_cents=30.0,
        rhythm_cv_target=0.32,
        timing_tolerance_ms=100.0,
        pro_score_floor=75.0,
        description="음정·멜로디 라인 정확도 중심 (60%).",
    ),
    "rock": StylePreset(
        id="rock",
        label="락 / 밴드",
        stage_weights=(0.20, 0.35, 0.45),
        melody_match_cents=45.0,
        rhythm_cv_target=0.38,
        timing_tolerance_ms=120.0,
        pro_score_floor=78.0,
        description="리듬·배음(에너지·음색) 중심 (80%).",
    ),
    "hiphop": StylePreset(
        id="hiphop",
        label="힙합 / R&B",
        stage_weights=(0.20, 0.30, 0.50),
        melody_match_cents=40.0,
        rhythm_cv_target=0.35,
        timing_tolerance_ms=90.0,
        pro_score_floor=78.0,
        description="그루브·음색·리듬 중심 (80%).",
    ),
    "standard": StylePreset(
        id="standard",
        label="균형 (기본)",
        stage_weights=(0.40, 0.30, 0.30),
        description="3영역 균형 평가.",
    ),
}

_BALLAD_KW = re.compile(
    r"발라드|ballad|ost|사랑|이별|그리|눈물|안녕|goodbye|love|slow",
    re.I,
)
_ROCK_KW = re.compile(
    r"락|rock|metal|punk|band|밴드|기타|guitar|hard|헤비|alternative",
    re.I,
)
_HIPHOP_KW = re.compile(
    r"힙합|hip.?hop|rap|r&b|rnb|trap|drill|비트|freestyle|피처링",
    re.I,
)


def resolve_preset(preset_id: str | None, song_title: str | None = None) -> StylePreset:
    """UI/API에서 선택한 프리셋 또는 곡 제목 기반 추론."""
    pid = (preset_id or "auto").lower().strip()
    if pid != "auto" and pid in PRESETS:
        return PRESETS[pid]

    title = (song_title or "").strip()
    if title:
        if _HIPHOP_KW.search(title):
            return PRESETS["hiphop"]
        if _ROCK_KW.search(title):
            return PRESETS["rock"]
        if _BALLAD_KW.search(title):
            return PRESETS["ballad"]

    return PRESETS["standard"]


def weighted_overall(
    pitch_score: float,
    rhythm_score: float,
    timbre_score: float,
    preset: StylePreset,
) -> float:
    w1, w2, w3 = preset.stage_weights
    total_w = w1 + w2 + w3
    if total_w <= 0:
        return round((pitch_score + rhythm_score + timbre_score) / 3, 1)
    return round(
        (pitch_score * w1 + rhythm_score * w2 + timbre_score * w3) / total_w,
        1,
    )


def apply_score_floor(
    overall: float,
    stages: list,
    preset: StylePreset,
    *,
    is_pro_like: bool = False,
    musical_accuracy: float | None = None,
) -> float:
    """실력자·고품질 신호 시 0점 방지 바닥."""
    floor = preset.pro_score_floor
    if is_pro_like:
        floor = max(floor, 80.0)
    if musical_accuracy is not None and musical_accuracy >= 70:
        floor = max(floor, 75.0)

    stage_scores = [s.score for s in stages[:3]]
    if stage_scores:
        best = max(stage_scores)
        if best >= 70:
            floor = max(floor, min(best - 5, 78.0))
        if all(s >= 45 for s in stage_scores):
            floor = max(floor, 50.0)

    return max(overall, floor)
