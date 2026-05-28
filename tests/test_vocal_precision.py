"""vocal_precision 모듈 단위 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vocal_precision import (
    analyze_note_precision,
    cents_vs_reference_transposed,
    estimate_transposition_cents,
    precision_pitch_score,
    smooth_f0_track,
)


def test_smooth_f0_reduces_jitter() -> None:
    t = np.linspace(0, 1, 200)
    f0 = 440.0 + 8.0 * np.sin(2 * np.pi * 7 * t)
    f0[::17] = np.nan
    probs = np.where(np.isfinite(f0), 0.9, 0.0)
    smoothed = smooth_f0_track(f0, probs)
    v = np.isfinite(smoothed)
    assert np.std(np.diff(smoothed[v])) < np.std(np.diff(f0[v]))


def test_transposition_detection() -> None:
    f0_user = np.full(20, 440.0)
    f0_ref = np.full(20, 493.88)  # B4 vs A4 ~ −200 cents
    shift = estimate_transposition_cents(f0_user, f0_ref)
    assert abs(shift + 196) < 25


def test_cents_after_transposition_near_zero() -> None:
    f0_user = np.full(20, 440.0)
    f0_ref = np.full(20, 493.88)
    shift = estimate_transposition_cents(f0_user, f0_ref)
    cents = cents_vs_reference_transposed(f0_user, f0_ref, shift)
    assert float(np.nanmean(np.abs(cents))) < 25.0


def test_note_precision_buckets() -> None:
    times = np.linspace(0, 2, 40)
    f0 = np.full(40, 440.0)
    f0_ref = np.full(40, 440.0)
    cents_ref = np.zeros(40)
    cents_ref[5:10] = -15
    cents_ref[15:20] = 3
    cents_ref[25:30] = 18
    eval_mask = np.ones(40, dtype=bool)
    m = analyze_note_precision(times, f0, f0_ref, cents_ref, eval_mask, match_cents=25.0)
    assert m.precise >= 1
    assert m.note_count >= 1
    assert 0.0 <= m.precision_ratio <= 1.0


def test_precision_pitch_score_range() -> None:
    from vocal_precision import NotePrecisionMetrics

    m = NotePrecisionMetrics(
        sustain_ratio=0.6,
        precision_ratio=0.7,
        note_hit_ratio=0.8,
    )
    s = precision_pitch_score(m, base_match_pct=70, sustained_ratio=0.5, seg_penalty=2)
    assert 0 <= s <= 100


if __name__ == "__main__":
    test_smooth_f0_reduces_jitter()
    test_transposition_detection()
    test_cents_after_transposition_near_zero()
    test_note_precision_buckets()
    test_precision_pitch_score_range()
    print("vocal_precision tests passed.")
