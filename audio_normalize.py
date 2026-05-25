"""
오디오 표준화 — 44.1 kHz · Mono · -14 LUFS.

유튜브·녹음 파일마다 다른 볼륨·샘플레이트·압축률을 맞춰
분석 엔진이 동등한 기준에서 평가하도록 합니다.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

TARGET_SR = 44100
TARGET_LUFS = -14.0
PEAK_LIMIT = 0.99

PROJECT_DIR = Path(__file__).resolve().parent
NORMALIZED_CACHE = PROJECT_DIR / ".cache" / "normalized"


def _loudness_normalize(y: np.ndarray, sr: int, target_lufs: float = TARGET_LUFS) -> np.ndarray:
    """Integrated LUFS 정규화. pyloudnorm 없으면 RMS 근사."""
    y = y.astype(np.float64)
    if y.size == 0:
        return y

    try:
        import pyloudnorm as pyln

        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(y)
        if np.isfinite(loudness):
            y = pyln.normalize.loudness(y, loudness, target_lufs)
    except Exception:
        # -14 LUFS ≈ RMS -18 dBFS 근사 (모노 음성·노래)
        rms = float(np.sqrt(np.mean(y**2)))
        if rms > 1e-8:
            target_rms = 10 ** (-18.0 / 20.0)
            y = y * (target_rms / rms)

    peak = float(np.max(np.abs(y)))
    if peak > PEAK_LIMIT:
        y = y * (PEAK_LIMIT / peak)
    return y.astype(np.float32)


def normalize_audio_array(
    y: np.ndarray,
    sr: int,
    *,
    target_sr: int = TARGET_SR,
    target_lufs: float = TARGET_LUFS,
) -> tuple[np.ndarray, int]:
    """배열을 표준 SR·LUFS로 변환."""
    if y.ndim > 1:
        y = librosa.to_mono(y)
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    y = _loudness_normalize(y, sr, target_lufs)
    return y, sr


def normalize_audio_file(
    input_path: Path,
    output_path: Path | None = None,
    *,
    inplace: bool = False,
    target_sr: int = TARGET_SR,
    target_lufs: float = TARGET_LUFS,
) -> Path:
    """
    파일 → 44.1 kHz mono WAV, -14 LUFS.
    inplace=True면 같은 경로에 덮어씁니다.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    if output_path is None:
        output_path = input_path if inplace else input_path.with_stem(input_path.stem + "_norm")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    y, sr = librosa.load(input_path, sr=None, mono=True)
    y, sr = normalize_audio_array(y, sr, target_sr=target_sr, target_lufs=target_lufs)
    sf.write(output_path, y, sr, subtype="PCM_16")
    return output_path


def _cache_key(path: Path) -> str:
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def ensure_normalized(
    audio_path: Path,
    *,
    force: bool = False,
    target_sr: int = TARGET_SR,
    target_lufs: float = TARGET_LUFS,
) -> Path:
    """
    분석 전 필수 전처리. 캐시된 정규화 WAV를 반환합니다.
    원본과 동일 경로면 .cache/normalized/ 에 저장합니다.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    NORMALIZED_CACHE.mkdir(parents=True, exist_ok=True)
    key = _cache_key(audio_path)
    cached = NORMALIZED_CACHE / f"{audio_path.stem}_{key}.wav"

    if cached.exists() and not force:
        return cached

    return normalize_audio_file(
        audio_path,
        cached,
        target_sr=target_sr,
        target_lufs=target_lufs,
    )


def normalize_reference_paths(mr_path: Path | None, guide_path: Path | None) -> tuple[Path | None, Path | None]:
    """reference_fetcher 이후 MR·가이드 WAV 표준화."""
    out_mr, out_guide = mr_path, guide_path
    if mr_path and mr_path.exists():
        out_mr = normalize_audio_file(mr_path, inplace=True)
    if guide_path and guide_path.exists():
        out_guide = normalize_audio_file(guide_path, inplace=True)
    return out_mr, out_guide
