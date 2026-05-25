"""
DTW 기반 음악적 피치 비교 — 인터벌·루바토 인식.

[핵심]
- 절대 센트 오차 + 음정 '간격(Interval)' 일치율 복합
- 시간 왜곡(Rubato)은 감점보다 '표현력'으로 해석
- 키(조) 이동은 median offset 보정
"""

from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np
from scipy.ndimage import median_filter

FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")
MATCH_CENTS = 35          # 표현적 여유 (기존 25 → 35)
INTERVAL_TOL_SEMITONES = 1.0
DEVIATION_CENTS = 55
MIN_SEGMENT_SEC = 0.35
RUBATO_TIME_COST = 0.12   # 유연성 가중치 — 시간 왜곡 패널티 완화
RUBATO_STRETCH_MIN_CV = 0.12


@dataclass
class DTWDeviationSegment:
    user_start_sec: float
    user_end_sec: float
    ref_start_sec: float
    ref_end_sec: float
    avg_cent_error: float
    max_cent_error: float
    note_hint: str


@dataclass
class DTWComparisonResult:
    """DTW 정렬 + 음악적 지표."""

    accuracy_percent: float
    mean_cent_error: float
    max_cent_error: float
    matched_frames: int
    total_aligned_frames: int
    deviation_segments: list[DTWDeviationSegment] = field(default_factory=list)
    warp_path_length: int = 0
    method: str = "rubato_aware_dtw"
    # 음악적 해석
    interval_match_percent: float = 0.0
    absolute_match_percent: float = 0.0
    musical_accuracy_percent: float = 0.0
    rubato_score: float = 0.0
    expressiveness_bonus: float = 0.0
    transposition_cents: float = 0.0
    rubato_detected: bool = False


def _hop_length(duration_sec: float) -> int:
    if duration_sec < 60:
        return 512
    if duration_sec < 180:
        return 1024
    return 2048


def extract_f0_track(
    y: np.ndarray, sr: int, hop_length: int
) -> tuple[np.ndarray, np.ndarray]:
    f0, _, _ = librosa.pyin(
        y, fmin=FMIN, fmax=FMAX, sr=sr, hop_length=hop_length
    )
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    return times, f0


def _interpolate_f0(f0: np.ndarray) -> np.ndarray:
    out = f0.copy().astype(float)
    valid = np.isfinite(out) & (out > 0)
    if not np.any(valid):
        return out
    idx = np.arange(len(out))
    out[~valid] = np.interp(idx[~valid], idx[valid], out[valid])
    return median_filter(out, size=5)


def _subsample(arr: np.ndarray, max_frames: int) -> tuple[np.ndarray, int]:
    step = max(1, len(arr) // max_frames)
    return arr[::step], step


def _dtw_path_rubato_aware(
    user_midi: np.ndarray,
    guide_midi: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Rubato-aware DTW: 대각 이동은 저비용, 시간 스텝(skip)은 RUBATO_TIME_COST.
    Returns cost_matrix, wp (N×2), cumulative cost at end.
    """
    n, m = len(user_midi), len(guide_midi)
    if n == 0 or m == 0:
        return np.array([]), np.empty((0, 2), dtype=int), np.array([])

    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    # backtrack pointers
    ptr_i = np.zeros((n + 1, m + 1), dtype=np.int32)
    ptr_j = np.zeros((n + 1, m + 1), dtype=np.int32)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            pitch_cost = abs(float(user_midi[i - 1] - guide_midi[j - 1]))
            candidates = [
                (D[i - 1, j - 1], i - 1, j - 1, 0.0),           # match
                (D[i - 1, j], i - 1, j, RUBATO_TIME_COST),       # user ahead
                (D[i, j - 1], i, j - 1, RUBATO_TIME_COST),       # guide ahead
            ]
            best = min(candidates, key=lambda x: x[0] + pitch_cost + x[3])
            D[i, j] = best[0] + pitch_cost + best[3]
            ptr_i[i, j] = best[1]
            ptr_j[i, j] = best[2]

    # backtrack
    i, j = n, m
    path: list[tuple[int, int]] = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        pi, pj = int(ptr_i[i, j]), int(ptr_j[i, j])
        if pi == i and pj == j:
            break
        i, j = pi, pj
    path.reverse()
    wp = np.array(path, dtype=int) if path else np.empty((0, 2), dtype=int)
    return D, wp, wp


def _interval_match_percent(
    user_midi: np.ndarray,
    guide_midi: np.ndarray,
    ui: np.ndarray,
    gi: np.ndarray,
    both: np.ndarray,
) -> float:
    """정렬 경로상 연속 음정 '간격' 일치율."""
    idx = np.where(both)[0]
    if idx.size < 4:
        return 0.0
    u_seq = user_midi[ui[idx]]
    g_seq = guide_midi[gi[idx]]
    du = np.diff(u_seq)
    dg = np.diff(g_seq)
    if du.size == 0:
        return 0.0
    err = np.abs(du - dg)
    return float(np.mean(err <= INTERVAL_TOL_SEMITONES) * 100.0)


def _rubato_metrics(
    ui: np.ndarray,
    gi: np.ndarray,
    interval_match: float,
) -> tuple[float, float, bool]:
    """시간 stretch 변동 + 인터벌 일치 → 루바토·표현력 점수."""
    if len(ui) < 6:
        return 0.0, 0.0, False

    stretch = np.diff(gi.astype(float)) / (np.diff(ui.astype(float)) + 1e-6)
    stretch = stretch[np.isfinite(stretch) & (stretch > 0) & (stretch < 5)]
    if stretch.size < 4:
        return 0.0, 0.0, False

    stretch_cv = float(np.std(stretch) / (np.mean(stretch) + 1e-6))
    rubato_detected = stretch_cv >= RUBATO_STRETCH_MIN_CV and interval_match >= 55.0

    if not rubato_detected:
        return 0.0, 0.0, False

    rubato_score = min(100.0, 50.0 + interval_match * 0.45 + stretch_cv * 25.0)
    bonus = min(15.0, stretch_cv * 20.0 + (interval_match - 50) * 0.1)
    return round(rubato_score, 1), round(bonus, 1), True


def _group_segments(
    mask: np.ndarray,
    user_times: np.ndarray,
    ref_times: np.ndarray,
    errors_cents: np.ndarray,
    user_f0: np.ndarray,
) -> list[DTWDeviationSegment]:
    idx = np.where(mask)[0]
    if idx.size == 0:
        return []
    breaks = np.where(np.diff(idx) > 1)[0] + 1
    groups = np.split(idx, breaks)
    segments: list[DTWDeviationSegment] = []

    for group in groups:
        if group.size == 0:
            continue
        u0, u1 = float(user_times[group[0]]), float(user_times[group[-1]])
        r0, r1 = float(ref_times[group[0]]), float(ref_times[group[-1]])
        if u1 - u0 < MIN_SEGMENT_SEC:
            continue
        err = errors_cents[group]
        hz = float(np.median(user_f0[group]))
        note = librosa.hz_to_note(hz, unicode=False) if hz > 0 else "N/A"
        segments.append(
            DTWDeviationSegment(
                user_start_sec=round(u0, 2),
                user_end_sec=round(u1, 2),
                ref_start_sec=round(r0, 2),
                ref_end_sec=round(r1, 2),
                avg_cent_error=round(float(np.mean(np.abs(err))), 1),
                max_cent_error=round(float(np.max(np.abs(err))), 1),
                note_hint=note,
            )
        )
    return segments


def compare_pitch_dtw(
    user_audio: np.ndarray,
    user_sr: int,
    guide_audio: np.ndarray,
    guide_sr: int,
) -> DTWComparisonResult:
    duration = max(len(user_audio), len(guide_audio)) / user_sr
    hop = _hop_length(duration)

    user_times, user_f0 = extract_f0_track(user_audio, user_sr, hop)
    guide_times, guide_f0 = extract_f0_track(guide_audio, guide_sr, hop)

    user_i = _interpolate_f0(user_f0)
    guide_i = _interpolate_f0(guide_f0)

    user_midi_full = librosa.hz_to_midi(np.maximum(user_i, 1e-6))
    guide_midi_full = librosa.hz_to_midi(np.maximum(guide_i, 1e-6))

    max_frames = 2500
    user_midi, step_u = _subsample(user_midi_full, max_frames)
    guide_midi, step_g = _subsample(guide_midi_full, max_frames)

    _, wp, _ = _dtw_path_rubato_aware(user_midi, guide_midi)

    if wp.size == 0:
        return DTWComparisonResult(
            accuracy_percent=0.0,
            mean_cent_error=0.0,
            max_cent_error=0.0,
            matched_frames=0,
            total_aligned_frames=0,
            method="rubato_aware_dtw",
        )

    gi = np.clip(wp[:, 1] * step_g, 0, len(guide_f0) - 1).astype(int)
    ui = np.clip(wp[:, 0] * step_u, 0, len(user_f0) - 1).astype(int)

    f0_u = user_f0[ui]
    f0_g = guide_f0[gi]
    both = np.isfinite(f0_u) & np.isfinite(f0_g) & (f0_u > 0) & (f0_g > 0)

    if not np.any(both):
        return DTWComparisonResult(
            accuracy_percent=0.0,
            mean_cent_error=0.0,
            max_cent_error=0.0,
            matched_frames=0,
            total_aligned_frames=len(wp),
            warp_path_length=len(wp),
            method="rubato_aware_dtw",
        )

    cents_err = 1200.0 * np.log2(f0_u[both] / f0_g[both])
    transposition = float(np.median(cents_err))
    cents_adj = cents_err - transposition
    abs_err = np.abs(cents_adj)

    both_idx = np.where(both)[0]
    abs_match = float(np.mean(abs_err <= MATCH_CENTS) * 100.0)
    interval_match = _interval_match_percent(
        user_midi_full, guide_midi_full, ui, gi, both
    )

    rubato_score, express_bonus, rubato_ok = _rubato_metrics(ui, gi, interval_match)

    # 음악적 정확도: 인터벌 60% + 절대(조 보정) 40%
    musical_acc = 0.6 * interval_match + 0.4 * abs_match
    if rubato_ok:
        musical_acc = min(100.0, musical_acc + express_bonus * 0.5)

    accuracy = musical_acc  # legacy field = musical composite

    mean_err = float(np.mean(abs_err))
    max_err = float(np.max(abs_err))

    # 이탈 구간: 조 보정 후 큰 오차 + 인터벌도 어긋난 프레임
    full_err = np.full(len(wp), np.nan)
    abs_err_full = np.full(len(wp), np.nan)
    abs_err_full[both] = abs_err
    full_err[both] = abs_err

    seg_mask = np.zeros(len(wp), dtype=bool)
    if both_idx.size >= 2:
        u_m = librosa.hz_to_midi(np.maximum(f0_u[both], 1e-6))
        g_m = librosa.hz_to_midi(np.maximum(f0_g[both], 1e-6))
        du = np.diff(u_m)
        dg = np.diff(g_m)
        step_bad = np.abs(du - dg) > INTERVAL_TOL_SEMITONES * 1.5
        for k, bi in enumerate(both_idx):
            if abs_err[k] < DEVIATION_CENTS:
                continue
            # 표현적 편차만(인터벌 OK)이면 구간 제외
            if k > 0 and k - 1 < len(step_bad) and not step_bad[k - 1]:
                if abs_err[k] < DEVIATION_CENTS + 25:
                    continue
            if k < len(step_bad) and not step_bad[k]:
                if abs_err[k] < DEVIATION_CENTS + 25:
                    continue
            seg_mask[bi] = True

    u_times_aligned = user_times[ui]
    g_times_aligned = guide_times[gi]

    segments = _group_segments(
        seg_mask,
        u_times_aligned,
        g_times_aligned,
        np.nan_to_num(full_err, nan=0.0),
        f0_u.copy(),
    )

    return DTWComparisonResult(
        accuracy_percent=round(accuracy, 1),
        mean_cent_error=round(mean_err, 1),
        max_cent_error=round(max_err, 1),
        matched_frames=int(np.sum(both)),
        total_aligned_frames=len(wp),
        deviation_segments=segments,
        warp_path_length=len(wp),
        method="rubato_aware_dtw",
        interval_match_percent=round(interval_match, 1),
        absolute_match_percent=round(abs_match, 1),
        musical_accuracy_percent=round(musical_acc, 1),
        rubato_score=rubato_score,
        expressiveness_bonus=express_bonus,
        transposition_cents=round(transposition, 1),
        rubato_detected=rubato_ok,
    )


def load_and_compare_files(
    user_path,
    guide_path,
    sr: int = 22050,
) -> DTWComparisonResult:
    y_u, _ = librosa.load(user_path, sr=sr, mono=True)
    y_g, _ = librosa.load(guide_path, sr=sr, mono=True)
    return compare_pitch_dtw(y_u, sr, y_g, sr)
