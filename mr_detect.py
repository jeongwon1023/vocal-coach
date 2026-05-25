"""
MR(반주) 포함 녹음 감지 — 목소리-only 녹음 안내.
"""

from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np


@dataclass
class MRDetectionResult:
    likely_mr: bool
    confidence: float
    percussive_ratio: float
    harmonic_ratio: float
    message: str


def detect_mr_content(y: np.ndarray, sr: int) -> MRDetectionResult:
    """
    HPSS + percussive energy 비율로 MR/반주 포함 가능성 추정.

    [메모] 드럼·반주가 크면 percussive 성분 비율이 높아집니다.
    """
    y_harm, y_perc = librosa.effects.hpss(y)
    harm_e = float(np.mean(y_harm**2) + 1e-12)
    perc_e = float(np.mean(y_perc**2) + 1e-12)
    total = harm_e + perc_e
    perc_ratio = perc_e / total
    harm_ratio = harm_e / total

    # percussive 35% 이상이면 MR 가능성
    likely = perc_ratio > 0.32 and harm_ratio > 0.3
    confidence = min(1.0, perc_ratio * 1.5) if likely else 0.0

    if likely:
        msg = (
            "MR/반주가 포함된 녹음으로 보입니다. "
            "박자·음색 점수가 실제보다 낮게 나올 수 있어요. "
            "이어폰으로 MR을 듣고 마이크에는 목소리만 녹음하면 분석이 정확해집니다."
        )
    else:
        msg = "목소리 중심 녹음으로 보입니다. 현재 점수를 그대로 참고하세요."

    return MRDetectionResult(
        likely_mr=likely,
        confidence=round(confidence, 2),
        percussive_ratio=round(perc_ratio, 3),
        harmonic_ratio=round(harm_ratio, 3),
        message=msg,
    )
