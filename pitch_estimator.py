"""F0 추출 — pYIN + optional CREPE 앙상블 (정밀 모드)."""

from __future__ import annotations

import os

import librosa
import numpy as np

from vocal_research import extract_pitch_pyin

FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")
CREPE_SR = 16000


def crepe_available() -> bool:
    if os.environ.get("USE_CREPE", "1").strip() in ("0", "false", "no"):
        return False
    try:
        import crepe  # noqa: F401

        return True
    except ImportError:
        return False


def extract_crepe_f0(
    y: np.ndarray,
    sr: int,
    hop_length: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """CREPE F0 — 16 kHz, librosa 프레임에 맞춰 보간."""
    import crepe

    y_in = y
    if sr != CREPE_SR:
        y_in = librosa.resample(y.astype(float), orig_sr=sr, target_sr=CREPE_SR)
    step_ms = max(10, int(1000 * hop_length / sr))
    _time, frequency, confidence, _ = crepe.predict(
        y_in,
        CREPE_SR,
        viterbi=True,
        step_size=step_ms,
        verbose=0,
    )
    n_frames = 1 + max(0, (len(y) - 1) // hop_length)
    frame_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)
    f0 = np.full(n_frames, np.nan, dtype=float)
    voiced_probs = np.zeros(n_frames, dtype=float)
    for i, t in enumerate(frame_times):
        j = int(np.argmin(np.abs(_time - t)))
        if j < len(frequency) and frequency[j] > 0 and confidence[j] >= 0.35:
            f0[i] = float(frequency[j])
            voiced_probs[i] = float(confidence[j])
    times = frame_times
    return times, f0, voiced_probs


def _track_quality(f0: np.ndarray, voiced_probs: np.ndarray) -> float:
    voiced = np.isfinite(f0) & (f0 > 0)
    n_voiced = int(np.sum(voiced))
    if n_voiced == 0:
        return 0.0
    vp_mean = float(np.mean(voiced_probs[voiced]))
    return n_voiced * 0.01 + vp_mean * 50.0


def blend_f0_tracks(
    tracks: list[tuple[np.ndarray, np.ndarray, np.ndarray, str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """프레임별 신뢰도 가중 F0 블렌드."""
    if not tracks:
        raise ValueError("no f0 tracks")
    if len(tracks) == 1:
        t, f0, vp, label = tracks[0]
        return t, f0, vp, label

    n = min(len(tracks[0][1]), *(len(t[1]) for t in tracks))
    f0_out = np.full(n, np.nan, dtype=float)
    vp_out = np.zeros(n, dtype=float)
    labels = "+".join(t[3] for t in tracks)

    for i in range(n):
        weights: list[float] = []
        freqs: list[float] = []
        for _, f0, vp, _ in tracks:
            if i >= len(f0):
                continue
            if np.isfinite(f0[i]) and f0[i] > 0:
                w = float(vp[i]) if i < len(vp) else 0.5
                weights.append(max(w, 0.05))
                freqs.append(float(f0[i]))
        if freqs:
            w_arr = np.array(weights)
            f0_out[i] = float(np.average(freqs, weights=w_arr / w_arr.sum()))
            vp_out[i] = float(np.mean(weights))

    return tracks[0][0][:n], f0_out, vp_out, labels


def extract_pitch_ensemble(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    *,
    y_harm: np.ndarray | None = None,
    audio_path=None,
    fast: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """pYIN robust + (정밀) CREPE 앙상블."""
    from analysis import extract_pitch_robust

    times, f0, vp, source = extract_pitch_robust(
        y, sr, hop_length, y_harm=y_harm, audio_path=audio_path
    )
    if fast or not crepe_available():
        return times, f0, vp, source

    try:
        t2, f0_c, vp_c = extract_crepe_f0(y, sr, hop_length)
        n = min(len(f0), len(f0_c))
        tracks = [
            (times[:n], f0[:n], vp[:n], source),
            (t2[:n], f0_c[:n], vp_c[:n], "crepe"),
        ]
        if _track_quality(f0_c, vp_c) >= _track_quality(f0, vp) * 0.85:
            return blend_f0_tracks(tracks)
    except Exception:
        pass

    return times, f0, vp, source
