"""
음악적 맥락 분석 — 배음 밀도, 프로급 음색 판별.

절대 주파수가 아닌 '소리의 조화로움'을 평가합니다.
"""

from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np

PRO_TIMBRE_MIN_SCORE = 80.0
PRO_HARMONIC_DENSITY = 0.22


@dataclass
class HarmonicTimbreMetrics:
    harmonic_density: float
    peak_regularity: float
    spectral_tonality: float
    timbre_score: float
    is_pro_like: bool
    note: str = ""


def _harmonic_energy_ratio(
    spectrum: np.ndarray,
    freqs: np.ndarray,
    f0_hz: float,
    n_harmonics: int = 8,
) -> float:
    """f0 배음 계열 에너지 / 전체 스펙트럼 에너지."""
    if f0_hz <= 0 or not np.isfinite(f0_hz):
        return 0.0
    total = float(spectrum.sum()) + 1e-10
    harm = 0.0
    for h in range(1, n_harmonics + 1):
        target = f0_hz * h
        if target >= freqs[-1]:
            break
        idx = int(np.argmin(np.abs(freqs - target)))
        lo = max(0, idx - 1)
        hi = min(len(spectrum), idx + 2)
        harm += float(spectrum[lo:hi].max())
    return min(1.0, harm / total)


def analyze_harmonic_timbre(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    times: np.ndarray,
    *,
    y_harm: np.ndarray | None = None,
) -> HarmonicTimbreMetrics:
    """
    배음 구조·스펙트럼 톤ality → 음색(Timbre) 점수.
    가수 목소리: 배음이 고르게 분포 → harmonic_density ↑
    """
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)

    n_fft = 2048
    S = np.abs(librosa.stft(y_harm, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    flatness = librosa.feature.spectral_flatness(y=y_harm, hop_length=hop_length)[0]
    tonality = 1.0 - np.clip(flatness, 0.0, 1.0)

    n = min(S.shape[1], len(f0), len(times), len(tonality))
    voiced = np.isfinite(f0[:n]) & (f0[:n] > 0)
    voiced_idx = np.where(voiced)[0]

    ratios: list[float] = []
    for fi in voiced_idx:
        ratios.append(_harmonic_energy_ratio(S[:, fi], freqs, float(f0[fi])))

    if not ratios:
        return HarmonicTimbreMetrics(
            harmonic_density=0.0,
            peak_regularity=0.0,
            spectral_tonality=0.0,
            timbre_score=0.0,
            is_pro_like=False,
            note="유성 구간 없음",
        )

    harmonic_density = float(np.mean(ratios))
    peak_regularity = float(1.0 - np.std(ratios) / (np.mean(ratios) + 1e-6))
    peak_regularity = float(np.clip(peak_regularity, 0.0, 1.0))
    spec_tonal = float(np.mean(tonality[:n][voiced]))

    # 프로급: 배음 풍부 + 규칙적 + tonal (기계음 flatness 높음)
    raw = (
        harmonic_density * 45.0
        + peak_regularity * 25.0
        + spec_tonal * 30.0
    )
    timbre_score = float(np.clip(raw, 0.0, 100.0))
    is_pro = timbre_score >= PRO_TIMBRE_MIN_SCORE or (
        harmonic_density >= PRO_HARMONIC_DENSITY and spec_tonal >= 0.35
    )
    if is_pro and timbre_score < PRO_TIMBRE_MIN_SCORE:
        timbre_score = PRO_TIMBRE_MIN_SCORE

    note = (
        "프로급 배음 조화 — 성대·공명 풍부"
        if is_pro
        else "배음 구조 분석 완료"
    )
    return HarmonicTimbreMetrics(
        harmonic_density=round(harmonic_density, 4),
        peak_regularity=round(peak_regularity, 4),
        spectral_tonality=round(spec_tonal, 4),
        timbre_score=round(timbre_score, 1),
        is_pro_like=is_pro,
        note=note,
    )
