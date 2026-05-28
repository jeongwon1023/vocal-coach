"""
논문·음성학 연구 기반 보컬 분석 보조 모듈.

주요 참고:
- Mauch & Dixon (2014) pYIN — ICASSP; voiced probability 가중 F0
- De Cheveigné & Kawahara (2002) YIN — JASA
- Böck & Widmer (2013) Superflux — DAFx; 비브라토 환경 onset
- Nix et al. (2016) / Voice Science — 비브라토 4.5–6.5 Hz, extent
- Sundberg — singer's formant 2–4 kHz
- Praat manual — jitter/shimmer (local) on sustained vowels
- PMC11026466 — 훈련된 가수 평균 pitch interval deviation ~22 cent (SD 11)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np
from scipy.ndimage import median_filter

# ── 연구 기반 임계값 ──
VOICED_PROB_MIN = 0.50  # pYIN: 유성 프레임 신뢰 하한
PITCH_EXCELLENT_CENTS = 22  # 훈련 가수 평균 수준 (PMC11026466)
PITCH_GOOD_CENTS = 35
PITCH_ACCEPTABLE_CENTS = 50  # 반음의 절반; 지각 mistuning 경계
MELODY_MATCH_STRICT_CENTS = 25

VIBRATO_RATE_MIN_HZ = 4.5
VIBRATO_RATE_MAX_HZ = 6.5
VIBRATO_WOBBLE_MAX_HZ = 4.0
VIBRATO_BLEAT_MIN_HZ = 7.0
VIBRATO_EXTENT_MIN_CENTS = 25
VIBRATO_EXTENT_MAX_CENTS = 120

JITTER_NORMAL_MAX_PCT = 1.04  # Praat: local jitter 정상 상한 근사
SHIMMER_NORMAL_MAX_PCT = 3.81
HNR_GOOD_MIN_DB = 15.0
HNR_WEAK_MAX_DB = 10.0

SINGER_FORMANT_LOW_HZ = 2000.0
SINGER_FORMANT_HIGH_HZ = 4000.0
SINGER_FORMANT_RATIO_GOOD = 0.12

RHYTHM_IOI_CV_TARGET = 0.28


@dataclass
class VibratoMetrics:
    rate_hz: float
    extent_cents: float
    quality: str  # normal | wobble | bleat | weak | none


@dataclass
class VoiceResearchMetrics:
    """한 곡 전체 요약 (논문 지표)."""
    voiced_prob_mean: float = 0.0
    melody_match_weighted: float = 0.0
    mean_abs_cents_ref: float = 0.0
    pitch_tier: str = "unknown"
    vibrato: VibratoMetrics | None = None
    jitter_local_pct: float | None = None
    shimmer_local_pct: float | None = None
    hnr_db: float | None = None
    singer_formant_ratio: float | None = None
    rhythm_cv_superflux: float | None = None
    rhythm_onset_count: int = 0
    research_notes: list[str] = field(default_factory=list)


def extract_pitch_pyin(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    *,
    fmin: float,
    fmax: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """pYIN F0 + voiced flag + probability (Mauch & Dixon 2014)."""
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        hop_length=hop_length,
    )
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    return times, f0, voiced_flag, voiced_probs


def _detrend_f0_cents(f0_hz: np.ndarray) -> np.ndarray:
    midi = librosa.hz_to_midi(f0_hz)
    t = np.linspace(0, 1, len(midi))
    trend = np.polyval(np.polyfit(t, midi, 1), t)
    return (midi - trend) * 100.0


def analyze_vibrato_chunk(f0_hz: np.ndarray, frame_dt: float) -> VibratoMetrics | None:
    """
    F0 contour FFT로 비브라토 rate/extent (Nix et al. 2016; Voice Science).
    """
    if len(f0_hz) < 8 or frame_dt <= 0:
        return None
    cents = _detrend_f0_cents(f0_hz)
    extent = float(np.max(cents) - np.min(cents))
    if extent < VIBRATO_EXTENT_MIN_CENTS:
        return VibratoMetrics(0.0, extent, "none")

    # Zero-pad FFT for rate in 2–10 Hz
    n = max(64, len(cents) * 4)
    spec = np.abs(np.fft.rfft(cents - np.mean(cents), n=n))
    freqs = np.fft.rfftfreq(n, d=frame_dt)
    band = (freqs >= 2.0) & (freqs <= 10.0)
    if not np.any(band):
        return VibratoMetrics(0.0, extent, "weak")
    peak_i = np.argmax(spec[band])
    rate = float(freqs[band][peak_i])

    if rate < VIBRATO_WOBBLE_MAX_HZ:
        quality = "wobble"
    elif rate > VIBRATO_BLEAT_MIN_HZ:
        quality = "bleat"
    elif VIBRATO_RATE_MIN_HZ <= rate <= VIBRATO_RATE_MAX_HZ:
        quality = "normal"
    else:
        quality = "weak"

    return VibratoMetrics(rate_hz=round(rate, 2), extent_cents=round(extent, 1), quality=quality)


def classify_voiced_chunk_research(
    f0_chunk: np.ndarray,
    duration_sec: float,
    frame_dt: float,
) -> tuple[str, VibratoMetrics | None]:
    """sustained | vibrato | transition + 비브라토 메트릭."""
    if duration_sec < 0.2:
        return "transition", None
    vib = analyze_vibrato_chunk(f0_chunk, frame_dt)
    if vib and vib.quality in ("normal", "wobble", "bleat", "weak") and vib.extent_cents >= VIBRATO_EXTENT_MIN_CENTS:
        if vib.quality != "none":
            return "vibrato", vib
    cents = _detrend_f0_cents(f0_chunk)
    if duration_sec >= 0.35 and float(np.max(cents) - np.min(cents)) < 42:
        return "sustained", vib
    return "transition", vib


def weighted_melody_match(
    cents_ref: np.ndarray,
    voiced_probs: np.ndarray,
    eval_mask: np.ndarray,
    threshold_cents: float = MELODY_MATCH_STRICT_CENTS,
) -> tuple[float, float]:
    """voiced probability 가중 멜로디 일치율 + 평균 절대 센트."""
    if not np.any(eval_mask):
        return 0.0, 0.0
    abs_c = np.abs(cents_ref[eval_mask])
    probs = voiced_probs[eval_mask]
    probs = np.clip(probs, 0.05, 1.0)
    weights = probs / np.sum(probs)
    match = float(np.sum(weights * (abs_c <= threshold_cents)))
    # MR/가이드 불일치 outlier 제외 — median inlier (≤100 cent)
    inliers = abs_c[abs_c <= 100.0]
    if inliers.size >= 5:
        mean_abs = float(np.median(inliers))
    else:
        mean_abs = float(np.median(abs_c)) if abs_c.size else 0.0
    return match, mean_abs


def pitch_tier_from_cents(mean_abs_cents: float, melody_match: float = 0.0) -> str:
    """훈련 가수 ~22 cent (PMC11026466) + 멜로디 일치율 복합."""
    if melody_match >= 0.70 and mean_abs_cents <= PITCH_EXCELLENT_CENTS:
        return "pro"
    if melody_match >= 0.55 and mean_abs_cents <= PITCH_GOOD_CENTS:
        return "good"
    if melody_match >= 0.40 and mean_abs_cents <= PITCH_ACCEPTABLE_CENTS:
        return "fair"
    if mean_abs_cents <= PITCH_ACCEPTABLE_CENTS:
        return "fair"
    return "needs_work"


def estimate_jitter_shimmer(
    f0_hz: np.ndarray,
    rms: np.ndarray,
) -> tuple[float | None, float | None]:
    """
    Praat local jitter/shimmer 근사 (sustained 유성 구간).
    """
    n = min(len(f0_hz), len(rms))
    f0_hz = f0_hz[:n]
    rms = rms[:n]
    valid = np.isfinite(f0_hz) & (f0_hz > 0)
    if np.sum(valid) < 6:
        return None, None
    periods = 1.0 / f0_hz[valid]
    if len(periods) < 3:
        return None, None
    dT = np.abs(np.diff(periods))
    jitter = float(np.mean(dT) / (np.mean(periods) + 1e-12) * 100.0)

    rms_v = rms[valid]
    if len(rms_v) < 3:
        return round(jitter, 3), None
    dA = np.abs(np.diff(rms_v))
    shimmer = float(np.mean(dA) / (np.mean(rms_v) + 1e-12) * 100.0)
    return round(jitter, 3), round(shimmer, 3)


def estimate_hnr_db(y: np.ndarray, sr: int) -> float | None:
    """
    Harmonic-to-noise ratio 근사 (autocorrelation peak / valley).
    PMC11026466: HNR↑ → 덜 허스(hoarse).
    """
    if len(y) < sr // 4:
        return None
    y = y - np.mean(y)
    r = librosa.autocorrelate(y, max_size=2 * sr // 4)
    r = r[len(r) // 2 :]
    if len(r) < 20:
        return None
    # F0 band 70–400 Hz
    lag_min = int(sr / 400)
    lag_max = int(sr / 70)
    lag_max = min(lag_max, len(r) - 1)
    if lag_max <= lag_min:
        return None
    segment = r[lag_min:lag_max]
    peak = float(np.max(segment))
    noise = float(np.mean(segment) + 1e-12)
    if peak <= noise:
        return None
    hnr = 10.0 * np.log10(peak / noise)
    return round(float(hnr), 2)


def singer_formant_ratio(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    *,
    y_harm: np.ndarray | None = None,
) -> float | None:
    """
    Singer's formant band (2–4 kHz) / low (0–1 kHz) energy ratio — Sundberg.
    """
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    S = np.abs(librosa.stft(y_harm, hop_length=hop_length)) ** 2
    freqs = librosa.fft_frequencies(sr=sr)
    low = S[freqs < 1000].sum()
    mid = S[(freqs >= SINGER_FORMANT_LOW_HZ) & (freqs <= SINGER_FORMANT_HIGH_HZ)].sum()
    if low <= 0:
        return None
    return round(float(mid / low), 4)


def rhythm_superflux_cv(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    times: np.ndarray,
    *,
    y_harm: np.ndarray | None = None,
) -> tuple[float | None, int, np.ndarray]:
    """
    Superflux onset (Böck & Widmer 2013) → IOI CV.
    비브라토 구간에서 false onset 감소.
    """
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    S = np.abs(librosa.stft(y_harm, hop_length=hop_length))
    S_db = librosa.power_to_db(S, ref=np.max)
    odf = librosa.onset.onset_strength(
        S=S_db, sr=sr, hop_length=hop_length, lag=1, max_size=1, aggregate=np.median
    )
    try:
        onset_times = librosa.onset.onset_detect(
            onset_envelope=odf,
            sr=sr,
            hop_length=hop_length,
            units="time",
            backtrack=True,
            delta=0.07,
            wait=4,
        )
    except Exception:
        return None, 0, np.array([])
    if onset_times.size < 3:
        return None, int(onset_times.size), onset_times

    # 유성 구간 onset만 (노래 구간)
    voiced_times = times[np.isfinite(f0) & (f0 > 0)]
    if voiced_times.size >= 2:
        v0, v1 = float(voiced_times[0]), float(voiced_times[-1])
        onset_times = onset_times[(onset_times >= v0) & (onset_times <= v1)]

    if onset_times.size < 3:
        return None, int(onset_times.size), onset_times

    ioi = np.diff(onset_times)
    ioi = ioi[(ioi > 0.12) & (ioi < 3.0)]
    if ioi.size < 2:
        return None, int(onset_times.size), onset_times
    cv = float(np.std(ioi) / (np.mean(ioi) + 1e-6))
    return round(cv, 3), int(onset_times.size), onset_times


def build_research_metrics(
    *,
    y: np.ndarray,
    sr: int,
    hop_length: int,
    times: np.ndarray,
    f0: np.ndarray,
    voiced_probs: np.ndarray,
    cents_ref: np.ndarray,
    eval_mask: np.ndarray,
    frame_labels: np.ndarray,
    y_harm: np.ndarray | None = None,
    fast: bool = False,
    melody_match_cents: float = MELODY_MATCH_STRICT_CENTS,
) -> VoiceResearchMetrics:
    notes: list[str] = []
    match_w, mean_abs = weighted_melody_match(
        cents_ref, voiced_probs, eval_mask, threshold_cents=melody_match_cents
    )
    tier = pitch_tier_from_cents(mean_abs, match_w)

    voiced_p = voiced_probs[np.isfinite(voiced_probs)]
    vp_mean = float(np.mean(voiced_p)) if voiced_p.size else 0.0

    # 대표 비브라토 (가장 긴 vibrato 구간)
    best_vib: VibratoMetrics | None = None
    voiced = np.isfinite(f0) & (f0 > 0)
    frame_dt = float(np.median(np.diff(times))) if len(times) > 1 else 0.01
    for group in _group_indices(voiced):
        if frame_labels[group[0]] != "vibrato":
            continue
        chunk = f0[group]
        vib = analyze_vibrato_chunk(chunk, frame_dt)
        if vib and (best_vib is None or vib.extent_cents > best_vib.extent_cents):
            best_vib = vib

    if best_vib:
        if best_vib.quality == "wobble":
            notes.append(
                f"비브라토가 느림({best_vib.rate_hz}Hz, 정상 4.5–6.5Hz) — '떨림'처럼 들릴 수 있음"
            )
        elif best_vib.quality == "bleat":
            notes.append(
                f"비브라토가 빠름({best_vib.rate_hz}Hz) — 긴장·조급한 느낌"
            )

    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    rms = librosa.feature.rms(y=y_harm, hop_length=hop_length)[0]
    n = min(len(rms), len(f0))
    sustained_mask = (frame_labels[:n] == "sustained") & voiced[:n]
    f0_slice = f0[:n]
    rms_slice = rms[:n]
    jitter, shimmer = None, None
    if not fast:
        if sustained_mask.sum() >= 6:
            jitter, shimmer = estimate_jitter_shimmer(
                f0_slice[sustained_mask], rms_slice[sustained_mask]
            )
        else:
            vmask = voiced[:n]
            jitter, shimmer = estimate_jitter_shimmer(f0_slice[vmask], rms_slice[vmask])
        if jitter is not None and jitter > JITTER_NORMAL_MAX_PCT:
            notes.append(f"지터(jitter) {jitter}% — 롱톤에서 F0 미세 흔들림 (정상 ~1% 이하)")
        if shimmer is not None and shimmer > SHIMMER_NORMAL_MAX_PCT:
            notes.append(f"셰이머(shimmer) {shimmer}% — 음량 미세 흔들림 (호흡 지지 점검)")

    hnr = None
    sfr = None
    rhythm_cv = None
    onset_n = 0
    if not fast:
        hnr = estimate_hnr_db(y_harm, sr)
        if hnr is not None and hnr < HNR_WEAK_MAX_DB:
            notes.append(f"HNR {hnr}dB — 공기·잡음 성분 많음 (성대 닫힘·허스)")
        elif hnr is not None and hnr >= HNR_GOOD_MIN_DB:
            notes.append(f"HNR {hnr}dB — 목소리 톤이 비교적 깨끗함")

        sfr = singer_formant_ratio(y, sr, hop_length, y_harm=y_harm)
        if sfr is not None and sfr < SINGER_FORMANT_RATIO_GOOD:
            notes.append("2–4kHz 마스크 공명 약함 — 멀리 전달력·밝기 부족할 수 있음")

        rhythm_cv, onset_n, _ = rhythm_superflux_cv(
            y, sr, hop_length, f0, times, y_harm=y_harm
        )

    if tier == "pro":
        notes.append(f"평균 음정 편차 {mean_abs:.0f}센트 — 훈련 가수 평균(22센트) 근접")
    elif tier == "needs_work":
        notes.append(f"평균 음정 편차 {mean_abs:.0f}센트 — 50센트(반음 절반) 이상 구간 많음")

    return VoiceResearchMetrics(
        voiced_prob_mean=round(vp_mean, 3),
        melody_match_weighted=round(match_w, 3),
        mean_abs_cents_ref=round(mean_abs, 1),
        pitch_tier=tier,
        vibrato=best_vib,
        jitter_local_pct=jitter,
        shimmer_local_pct=shimmer,
        hnr_db=hnr,
        singer_formant_ratio=sfr,
        rhythm_cv_superflux=rhythm_cv,
        rhythm_onset_count=onset_n,
        research_notes=notes,
    )


def _group_indices(mask: np.ndarray) -> list[np.ndarray]:
    idx = np.where(mask)[0]
    if idx.size == 0:
        return []
    breaks = np.where(np.diff(idx) > 1)[0] + 1
    return [g for g in np.split(idx, breaks) if g.size > 0]


def research_pitch_score(metrics: VoiceResearchMetrics, base_match_pct: float) -> float:
    """연구 지표 반영 음정 점수."""
    score = base_match_pct * 0.75
    tier_bonus = {"pro": 15, "good": 10, "fair": 5, "needs_work": 0, "unknown": 0}
    score += tier_bonus.get(metrics.pitch_tier, 0)
    score += metrics.voiced_prob_mean * 10
    if metrics.vibrato and metrics.vibrato.quality == "normal":
        score += 5
    if metrics.jitter_local_pct and metrics.jitter_local_pct > JITTER_NORMAL_MAX_PCT:
        score -= 5
    return max(0.0, min(100.0, score))


def research_rhythm_score(
    cv_superflux: float | None,
    cv_legacy: float,
    *,
    cv_target: float = RHYTHM_IOI_CV_TARGET,
) -> float:
    """Superflux IOI CV 우선, legacy envelope CV 보조."""
    cv = cv_superflux if cv_superflux is not None else cv_legacy
    base = max(0.0, min(100.0, 100 - cv * (100.0 / max(cv_target, 0.12))))
    if cv_superflux is not None and cv_legacy is not None:
        if cv_superflux <= cv_target and cv_legacy <= cv_target + 0.07:
            base = min(100.0, base + 8)
    return round(base, 1)


def research_breath_score(
    env_cv: float,
    metrics: VoiceResearchMetrics,
    timbre_penalty: float,
) -> float:
    score = max(0.0, min(100.0, 100 - env_cv * 100 - timbre_penalty))
    if metrics.hnr_db is not None:
        if metrics.hnr_db >= HNR_GOOD_MIN_DB:
            score = min(100.0, score + 6)
        elif metrics.hnr_db < HNR_WEAK_MAX_DB:
            score = max(0.0, score - 8)
    if metrics.shimmer_local_pct and metrics.shimmer_local_pct > SHIMMER_NORMAL_MAX_PCT:
        score = max(0.0, score - 5)
    if metrics.singer_formant_ratio and metrics.singer_formant_ratio >= SINGER_FORMANT_RATIO_GOOD:
        score = min(100.0, score + 4)
    return round(score, 1)
