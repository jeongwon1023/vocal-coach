"""보컬 분리 — 정밀 모드용 (enhanced HPSS · optional Demucs)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

PROJECT_DIR = Path(__file__).resolve().parent
VOCAL_CACHE = PROJECT_DIR / ".cache" / "vocals"


def _cache_path(audio_path: Path | None, suffix: str) -> Path | None:
    if audio_path is None or not audio_path.exists():
        return None
    key = hashlib.sha256(
        f"{audio_path.resolve()}:{audio_path.stat().st_mtime_ns}:{suffix}".encode()
    ).hexdigest()[:20]
    return VOCAL_CACHE / f"{key}_{suffix}.wav"


def enhanced_hpss_vocal(y: np.ndarray, sr: int, *, audio_path: Path | None = None) -> np.ndarray:
    """강화 HPSS + 센터 채널 — MR 믹스 보컬 강조 (Demucs 없을 때)."""
    from analysis import emphasize_vocal_track

    vocal = emphasize_vocal_track(y, sr, audio_path)
    y_harm, _ = librosa.effects.hpss(y, margin=(1.0, 5.0))
    blend = 0.62 * vocal.astype(float) + 0.38 * y_harm.astype(float)
    peak = float(np.max(np.abs(blend)))
    if peak <= 1e-9:
        return y
    return librosa.util.normalize(blend)


def _demucs_vocals(y: np.ndarray, sr: int, cache_path: Path | None) -> np.ndarray:
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    if cache_path and cache_path.exists():
        out, file_sr = sf.read(str(cache_path), always_2d=False)
        if file_sr != sr:
            out = librosa.resample(out.astype(float), orig_sr=file_sr, target_sr=sr)
        return librosa.util.normalize(out.astype(float))

    target_sr = 44100
    wav = y.astype(np.float32)
    if sr != target_sr:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=target_sr)
    tensor = torch.from_numpy(wav).float()
    if tensor.dim() == 1:
        tensor = tensor.unsqueeze(0)

    model = get_model("htdemucs")
    model.eval()
    with torch.no_grad():
        sources = apply_model(model, tensor.unsqueeze(0), device="cpu", progress=False)[0]
    vocals = sources[-1].mean(dim=0).numpy()

    if cache_path:
        VOCAL_CACHE.mkdir(parents=True, exist_ok=True)
        sf.write(str(cache_path), vocals, target_sr)

    if sr != target_sr:
        vocals = librosa.resample(vocals, orig_sr=target_sr, target_sr=sr)
    return librosa.util.normalize(vocals)


def prepare_vocal_signal(
    y: np.ndarray,
    sr: int,
    *,
    audio_path: Path | None = None,
    fast: bool = False,
) -> tuple[np.ndarray, str]:
    """
    분석용 보컬 트랙 반환.
    fast=True → 원본 그대로.
    """
    if fast:
        return y, "original"

    mode = os.environ.get("VOCAL_SEP", "enhanced").lower().strip()
    cache = _cache_path(audio_path, "demucs") if audio_path else None

    if mode in ("demucs", "auto"):
        try:
            return _demucs_vocals(y, sr, cache), "demucs"
        except Exception:
            if mode == "demucs":
                raise

    return enhanced_hpss_vocal(y, sr, audio_path=audio_path), "enhanced_hpss"
