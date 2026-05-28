"""
정밀 보컬 분석 — 경쟁 서비스 벤치마크 반영.

참고 벤치마크:
- Simply Sing / Yousician: 실시간 F0 + 스무딩·게이팅, 노트 단위 정확도
- Smule: score-coded MIDI 타깃, 키(조) 보정 후 센트 편차
- Singing Carrots: ±5¢(precise) / ±12¢(audible) 다단계 정밀도
- Singscope / MTG: 프레임 F0 + 비브라토 구간 분리, 노트 세그먼트
- DTW(Yousician dataset): timing_offset + pitch_offset per note
"""

from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np
from scipy.ndimage import median_filter

# Singing Carrots 기준 (pitch monitor docs)
CENTS_PRECISE = 5.0   # just interval — 훈련된 귀도 거의 못 들음
CENTS_GOOD = 12.0     # 일반인도 들을 수 있는 편차
CENTS_AUDIBLE = 25.0  # 반음의 ¼ — 멜로디 매치 기본

SMOOTH_ALPHA = 0.18   # Simply Sing류 지수 스무딩
NOTE_MIN_SEC = 0.18
NOTE_HYSTERESIS_FRAMES = 3


@dataclass
class NoteSegment:
    start_sec: float
    end_sec: float
    midi_median: float
    ref_midi_median: float | None
    mean_cents_error: float
    max_cents_error: float
    hit: bool
    timing_offset_ms: float | None = None


@dataclass
class NotePrecisionMetrics:
    """노트·프레임 다단계 음정 지표."""
    sustain_ratio: float = 0.0       # ±5¢ 유지 비율 (Singing Carrots sustain)
    precision_ratio: float = 0.0     # ±match_cents 이내 (precision)
    note_hit_ratio: float = 0.0      # 노트 단위 적중 (Yousician/Smule)
    transposition_cents: float = 0.0
    too_low: int = 0
    slightly_low: int = 0
    precise: int = 0
    slightly_high: int = 0
    too_high: int = 0
    note_count: int = 0
    timing_score: float | None = None
    note_segments: list[NoteSegment] = field(default_factory=list)


def smooth_f0_track(
    f0: np.ndarray,
    voiced_probs: np.ndarray | None = None,
    *,
    alpha: float = SMOOTH_ALPHA,
    median_size: int = 5,
) -> np.ndarray:
    """지수 스무딩 + median — 실시간 튜너류 안정 F0 (Simply Sing / Singscope)."""
    out = f0.copy().astype(float)
    voiced = np.isfinite(out) & (out > 0)
    if not np.any(voiced):
        return out

    if voiced_probs is not None and len(voiced_probs) == len(out):
        strong = voiced & (voiced_probs >= 0.35)
    else:
        strong = voiced

    prev: float | None = None
    for i in range(len(out)):
        if not strong[i]:
            continue
        v = float(out[i])
        if prev is None:
            prev = v
        else:
            prev = alpha * v + (1.0 - alpha) * prev
        out[i] = prev

    filled = out.copy()
    idx = np.arange(len(filled))
    if np.any(voiced):
        filled[~voiced] = np.interp(idx[~voiced], idx[voiced], out[voiced])
        if median_size > 1:
            filled = median_filter(filled, size=median_size)
        filled[~voiced] = np.nan
    return filled


def gate_f0_by_energy(
    f0: np.ndarray,
    y: np.ndarray,
    sr: int,
    hop_length: int,
    *,
    min_ratio: float = 0.07,
) -> np.ndarray:
    """RMS 게이팅 — 배경·숨소리 F0 제거 (Simply Sing amplitude gate)."""
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    n = min(len(rms), len(f0))
    out = f0.copy()
    peak = float(np.max(rms[:n])) if n else 0.0
    if peak <= 1e-9:
        return out
    thr = peak * min_ratio
    for i in range(n):
        if rms[i] < thr:
            out[i] = np.nan
    return out


def estimate_transposition_cents(
    f0: np.ndarray,
    f0_ref: np.ndarray,
    *,
    voiced_prob: np.ndarray | None = None,
    min_frames: int = 12,
) -> float:
    """
    전곡 키(조) 오프셋 — Smule/Yousician pitch_offset 보정.
    MR·키 변경 녹음에서 절대 높이 오차를 줄임.
    """
    both = (
        np.isfinite(f0)
        & np.isfinite(f0_ref)
        & (f0 > 0)
        & (f0_ref > 0)
    )
    if voiced_prob is not None and len(voiced_prob) == len(f0):
        both &= voiced_prob >= 0.4
    if np.sum(both) < min_frames:
        return 0.0
    cents = 1200.0 * np.log2(f0[both] / f0_ref[both])
    med = float(np.median(cents))
    inliers = cents[np.abs(cents - med) <= 100.0]
    if inliers.size < 5:
        return med
    return float(np.median(inliers))


def cents_vs_reference_transposed(
    f0: np.ndarray,
    f0_ref: np.ndarray,
    transposition_cents: float,
) -> np.ndarray:
    """조 보정 후 기준 대비 센트."""
    both = (
        np.isfinite(f0)
        & np.isfinite(f0_ref)
        & (f0 > 0)
        & (f0_ref > 0)
    )
    err = np.full_like(f0, np.nan, dtype=float)
    factor = 2.0 ** (transposition_cents / 1200.0)
    err[both] = 1200.0 * np.log2(f0[both] / (f0_ref[both] * factor))
    return err


def _group_note_indices(midi_round: np.ndarray, voiced: np.ndarray) -> list[np.ndarray]:
    """연속 동일 음(반올림 MIDI) 그룹 — 노트 hysteresis."""
    idx = np.where(voiced)[0]
    if idx.size == 0:
        return []
    groups: list[list[int]] = [[int(idx[0])]]
    for i in idx[1:]:
        if int(round(midi_round[i])) == int(round(midi_round[groups[-1][-1]])):
            groups[-1].append(int(i))
        else:
            groups.append([int(i)])
    return [np.array(g, dtype=int) for g in groups if len(g) >= NOTE_HYSTERESIS_FRAMES]


def segment_notes(
    times: np.ndarray,
    f0: np.ndarray,
    f0_ref: np.ndarray,
    cents_ref: np.ndarray,
    *,
    match_cents: float = CENTS_AUDIBLE,
) -> list[NoteSegment]:
    """
    노트 단위 세그먼트 (Yousician notes_successful / Smule score-coded targets).
    """
    voiced = np.isfinite(f0) & (f0 > 0)
    if not np.any(voiced):
        return []

    midi = librosa.hz_to_midi(f0)
    midi_round = np.round(midi)
    segments: list[NoteSegment] = []

    for group in _group_note_indices(midi_round, voiced):
        t0, t1 = float(times[group[0]]), float(times[group[-1]])
        if t1 - t0 < NOTE_MIN_SEC:
            continue
        user_m = float(np.median(midi[group]))
        ref_mask = (
            np.isfinite(f0_ref[group])
            & (f0_ref[group] > 0)
            & np.isfinite(cents_ref[group])
        )
        ref_m = None
        if np.any(ref_mask):
            ref_m = float(np.median(librosa.hz_to_midi(f0_ref[group][ref_mask])))
        seg_c = cents_ref[group]
        seg_c = seg_c[np.isfinite(seg_c)]
        if seg_c.size == 0:
            continue
        mean_e = float(np.mean(np.abs(seg_c)))
        max_e = float(np.max(np.abs(seg_c)))
        hit = mean_e <= match_cents

        timing_ms = None
        if f0_ref is not None and np.any(np.isfinite(f0_ref)):
            ref_voiced = np.isfinite(f0_ref) & (f0_ref > 0)
            ref_idx = np.where(ref_voiced)[0]
            if ref_idx.size >= 2:
                ref_midi = librosa.hz_to_midi(f0_ref[ref_voiced])
                target = int(round(user_m))
                matches = np.where(np.abs(np.round(ref_midi) - target) <= 0.5)[0]
                if matches.size:
                    ref_onset_i = ref_idx[matches[0]]
                    timing_ms = (times[group[0]] - times[ref_onset_i]) * 1000.0

        segments.append(
            NoteSegment(
                start_sec=round(t0, 2),
                end_sec=round(t1, 2),
                midi_median=round(user_m, 2),
                ref_midi_median=round(ref_m, 2) if ref_m is not None else None,
                mean_cents_error=round(mean_e, 1),
                max_cents_error=round(max_e, 1),
                hit=hit,
                timing_offset_ms=round(timing_ms, 1) if timing_ms is not None else None,
            )
        )
    return segments


def _bucket_cents(abs_cents: float) -> str:
    if abs_cents <= CENTS_PRECISE:
        return "precise"
    if abs_cents <= CENTS_GOOD:
        return "slightly"
    if abs_cents <= CENTS_AUDIBLE:
        return "audible"
    return "far"


def analyze_note_precision(
    times: np.ndarray,
    f0: np.ndarray,
    f0_ref: np.ndarray,
    cents_ref: np.ndarray,
    eval_mask: np.ndarray,
    *,
    match_cents: float = CENTS_AUDIBLE,
    timing_tolerance_ms: float = 80.0,
) -> NotePrecisionMetrics:
    """Singing Carrots sustain/precision + Yousician 노트 적중 + 타이밍."""
    metrics = NotePrecisionMetrics()
    if not np.any(eval_mask):
        return metrics

    abs_c = np.abs(cents_ref[eval_mask])
    metrics.sustain_ratio = float(np.mean(abs_c <= CENTS_PRECISE))
    metrics.precision_ratio = float(np.mean(abs_c <= match_cents))

    buckets = {"too_low": 0, "slightly_low": 0, "precise": 0, "slightly_high": 0, "too_high": 0}
    signed = cents_ref[eval_mask]
    for c in signed:
        if not np.isfinite(c):
            continue
        ac = abs(float(c))
        b = _bucket_cents(ac)
        if b == "precise":
            buckets["precise"] += 1
        elif c < 0:
            buckets["too_low" if ac > CENTS_GOOD else "slightly_low"] += 1
        else:
            buckets["too_high" if ac > CENTS_GOOD else "slightly_high"] += 1

    metrics.too_low = buckets["too_low"]
    metrics.slightly_low = buckets["slightly_low"]
    metrics.precise = buckets["precise"]
    metrics.slightly_high = buckets["slightly_high"]
    metrics.too_high = buckets["too_high"]

    note_segs = segment_notes(times, f0, f0_ref, cents_ref, match_cents=match_cents)
    metrics.note_segments = note_segs
    metrics.note_count = len(note_segs)
    if note_segs:
        metrics.note_hit_ratio = float(np.mean([1.0 if n.hit else 0.0 for n in note_segs]))

    timing_offsets = [
        abs(n.timing_offset_ms)
        for n in note_segs
        if n.timing_offset_ms is not None
    ]
    if timing_offsets:
        within = float(np.mean([1.0 if t <= timing_tolerance_ms else 0.0 for t in timing_offsets]))
        avg_ms = float(np.mean(timing_offsets))
        metrics.timing_score = round(within * 70.0 + max(0.0, 30.0 - avg_ms * 0.15), 1)

    return metrics


def precision_pitch_score(
    metrics: NotePrecisionMetrics,
    *,
    base_match_pct: float,
    sustained_ratio: float,
    seg_penalty: float,
) -> float:
    """노트·다단계 정밀도 반영 음정 점수."""
    score = (
        base_match_pct * 0.38
        + metrics.precision_ratio * 100.0 * 0.22
        + metrics.sustain_ratio * 100.0 * 0.12
        + metrics.note_hit_ratio * 100.0 * 0.18
        + sustained_ratio * 10.0
        - seg_penalty
    )
    if metrics.timing_score is not None:
        score += metrics.timing_score * 0.10
    return max(0.0, min(100.0, score))
