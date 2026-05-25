"""
보컬 학원 4단계 커리큘럼 + 기준 멜로디(Reference Melody) 음정 채점.

[실행 - 프로젝트 MP3 분석]
    cd vocal-coach
    .\\venv\\Scripts\\Activate.ps1
    python analysis.py sample.mp3

[기준 멜로디 MIDI가 있을 때]
    python analysis.py sample.mp3 --reference reference.mid

[유튜브 레퍼런스 + DTW + GPT 코칭]
    python analysis.py sample.mp3 --song "노래제목" --gpt

[메모] MIDI/가이드 없으면 조화음(HPSS)에서 기준 멜로디를 자동 추출합니다.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
from coaching_vocab import (
    STAGE_TITLES,
    breath_summary,
    cent_to_words,
    env_cv_to_words,
    hf_drop_to_words,
    pitch_summary,
    rhythm_cv_to_words,
    rhythm_summary,
    time_range as _vocab_time_range,
)
from vocal_research import (
    PITCH_ACCEPTABLE_CENTS,
    VOICED_PROB_MIN,
    VoiceResearchMetrics,
    build_research_metrics,
    classify_voiced_chunk_research,
    extract_pitch_pyin,
    research_breath_score,
    research_pitch_score,
    research_rhythm_score,
)
from scipy.ndimage import median_filter, uniform_filter1d

PROJECT_DIR = Path(__file__).resolve().parent
FALLBACK_AUDIO = PROJECT_DIR / "test_voice.wav"
DEFAULT_REFERENCE = PROJECT_DIR / "reference.mid"
AUDIO_CANDIDATES = (
    PROJECT_DIR / "sample.mp3",
    PROJECT_DIR / "sample.wav",
    FALLBACK_AUDIO,
)
ANALYSIS_SR = 22050
FAST_ANALYSIS_SR = 16000
FAST_MAX_DURATION_SEC = 120.0  # 빠른 모드: 앞 2분만 분석
NORMALIZE_BEFORE_ANALYSIS = True  # 44.1kHz mono -14 LUFS 전처리

from ui.runtime_env import configure_matplotlib

configure_matplotlib()

FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")

SUSTAINED_DEVIATION_CENTS = 45
SUSTAINED_STABLE_CENTS = 28
MELODY_MATCH_CENTS = 25
REFERENCE_DEVIATION_CENTS = 50
MIN_SEGMENT_SEC = 0.35

VIBRATO_EXTENT_MIN_CENTS = 18
VIBRATO_EXTENT_MAX_CENTS = 220
VIBRATO_ZCR_MIN = 3.0
VIBRATO_ZCR_MAX = 16.0
SUSTAINED_MIN_SEC = 0.35

BREATH_DROP_THRESHOLD = -0.38
BREATH_SURGE_THRESHOLD = 0.42
BREATH_MIN_DURATION_SEC = 0.22
HF_DROP_PERCENT = 15.0
HF_CUTOFF_HZ = 2000.0


# ═══════════════════════════════════════════════════════════════════════════
# 데이터 구조
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class CoachingBlock:
    """학원 표준 코칭 출력: [결과] / [원인] / [해결]"""

    result: str
    cause: str
    solution: str


@dataclass
class PitchDeviationSegment:
    start_sec: float
    end_sec: float
    avg_deviation_cents: float
    max_deviation_cents: float
    note_hint: str
    region_type: str = "sustained"
    vs_reference: bool = False


@dataclass
class BreathMismatchSegment:
    start_sec: float
    end_sec: float
    issue_type: str


@dataclass
class TimbreIssueSegment:
    start_sec: float
    end_sec: float
    hf_drop_percent: float


@dataclass
class StageResult:
    stage: int
    title: str
    score: float
    summary: str
    coaching_blocks: list[CoachingBlock] = field(default_factory=list)
    details: dict = field(default_factory=dict)


@dataclass
class PitchAnalysis:
    cents: np.ndarray
    cents_vs_reference: np.ndarray
    frame_labels: np.ndarray
    deviation_segments: list[PitchDeviationSegment]
    stable_regions: list[tuple[float, float]]
    sustained_ratio: float
    vibrato_ratio: float
    melody_match_ratio: float
    reference_source: str
    f0_reference: np.ndarray
    voiced_probs: np.ndarray = field(default_factory=lambda: np.array([]))
    research: VoiceResearchMetrics | None = None
    f0_user: np.ndarray = field(default_factory=lambda: np.array([]))
    interval_match_ratio: float = 0.0


@dataclass
class CurriculumReport:
    audio_path: Path
    duration_sec: float
    pitch_deviation_segments: list[PitchDeviationSegment]
    stable_regions: list[tuple[float, float]]
    breath_mismatch_segments: list[BreathMismatchSegment]
    timbre_issue_segments: list[TimbreIssueSegment]
    stages: list[StageResult]
    overall_score: float
    coaching_text: str
    reference_source: str
    song_title: str | None = None
    times: np.ndarray = field(default_factory=lambda: np.array([]))
    f0: np.ndarray = field(default_factory=lambda: np.array([]))
    f0_reference: np.ndarray = field(default_factory=lambda: np.array([]))
    dtw_result: object | None = None  # dtw_compare.DTWComparisonResult
    mr_likely: bool = False
    mr_message: str = ""
    research: VoiceResearchMetrics | None = None
    style_preset_id: str = "standard"
    style_preset_label: str = "균형 (기본)"


# ═══════════════════════════════════════════════════════════════════════════
# 코칭 출력 포맷 (추상 표현 금지, 업계 표준 용어 + 인과 구조)
# ═══════════════════════════════════════════════════════════════════════════


def format_coaching_block(block: CoachingBlock) -> str:
    return (
        f"🎤 선생님: {block.result}\n"
        f"   왜 그럴까요? {block.cause}\n"
        f"   이렇게 해보세요: {block.solution}"
    )


def _time_range(start: float, end: float) -> str:
    return _vocab_time_range(start, end)


# ═══════════════════════════════════════════════════════════════════════════
# 공통 유틸
# ═══════════════════════════════════════════════════════════════════════════


def _hop_length(duration_sec: float, *, fast: bool = False) -> int:
    """fast=True: 더 큰 hop → pYIN/STFT 프레임 수 감소."""
    if fast:
        return 2048 if duration_sec >= 45 else 1024
    if duration_sec < 60:
        return 512
    if duration_sec < 180:
        return 1024
    return 2048


def _note_name(hz: float) -> str:
    return librosa.hz_to_note(hz, unicode=False)


def ensure_default_audio() -> Path:
    for path in AUDIO_CANDIDATES:
        if path.exists():
            return path
    t = np.linspace(0, 3.0, int(ANALYSIS_SR * 3), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(FALLBACK_AUDIO, y, ANALYSIS_SR)
    return FALLBACK_AUDIO


def resolve_audio(path: Path | None) -> Path:
    if path is not None:
        return path
    return ensure_default_audio()


def resolve_reference(reference: Path | None) -> Path | None:
    if reference is not None:
        return reference if reference.exists() else None
    return DEFAULT_REFERENCE if DEFAULT_REFERENCE.exists() else None


def load_audio(
    audio_path: Path, *, fast: bool = False, skip_normalize: bool = False
) -> tuple[np.ndarray, int, int, float | None]:
    """
    Returns (y, sr, hop_length, full_duration_if_truncated).
    빠른 모드: 16kHz · 앞 2분만 로드.
    """
    import soundfile as sf

    src = audio_path
    if NORMALIZE_BEFORE_ANALYSIS and not skip_normalize:
        from audio_normalize import ensure_normalized

        src = ensure_normalized(audio_path)

    info = sf.info(str(src))
    full_dur = float(info.duration)
    sr_target = FAST_ANALYSIS_SR if fast else ANALYSIS_SR
    load_dur = (
        FAST_MAX_DURATION_SEC if fast and full_dur > FAST_MAX_DURATION_SEC else None
    )
    y, sr = librosa.load(src, sr=sr_target, mono=True, duration=load_dur)
    analyzed_dur = len(y) / sr
    hop = _hop_length(analyzed_dur, fast=fast)
    truncated = full_dur if load_dur else None
    return y, sr, hop, truncated


def emphasize_vocal_track(
    y: np.ndarray, sr: int, audio_path: Path | None = None
) -> np.ndarray:
    """MR·스테레오 믹스에서 보컬 성분 강조 (유튜브·가수 영상 대응)."""
    if audio_path and audio_path.exists():
        try:
            y_st, _ = librosa.load(audio_path, sr=sr, mono=False, duration=len(y) / sr)
            if y_st.ndim == 2 and y_st.shape[0] >= 2:
                # 센터(보컬) 강조: L-R / Mid
                vocal = y_st[0].astype(float) - y_st[1].astype(float)
                peak = float(np.max(np.abs(vocal)))
                if peak > 1e-6:
                    return librosa.util.normalize(vocal)
        except Exception:
            pass

    y_harm, y_perc = librosa.effects.hpss(y)
    vocal = y_harm.astype(float) - 0.3 * y_perc.astype(float)
    return librosa.util.normalize(vocal)


def extract_pitch_robust(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    *,
    y_harm: np.ndarray | None = None,
    audio_path: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """
    raw / harmonic / vocal-emphasis 중 pYIN 품질이 가장 좋은 F0 선택.
    유튜브·MR 믹스에서 0점 방지.
    """
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    y_vocal = emphasize_vocal_track(y, sr, audio_path)

    best: tuple[float, np.ndarray, np.ndarray, np.ndarray, str] | None = None
    for label, sig in (("raw", y), ("harmonic", y_harm), ("vocal", y_vocal)):
        times, f0, _, voiced_probs = extract_pitch_pyin(
            sig, sr, hop_length, fmin=FMIN, fmax=FMAX
        )
        voiced = np.isfinite(f0) & (f0 > 0)
        n_voiced = int(np.sum(voiced))
        if n_voiced == 0:
            quality = 0.0
        else:
            vp_mean = float(np.mean(voiced_probs[voiced]))
            quality = n_voiced * 0.01 + vp_mean * 50.0
        if best is None or quality > best[0]:
            best = (quality, times, f0, voiced_probs, label)

    assert best is not None
    _, times, f0, voiced_probs, source = best
    return times, f0, voiced_probs, source


def extract_pitch(
    y: np.ndarray, sr: int, hop_length: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """pYIN F0 + voiced probability (Mauch & Dixon 2014)."""
    times, f0, _, voiced_probs = extract_pitch_pyin(
        y, sr, hop_length, fmin=FMIN, fmax=FMAX
    )
    return times, f0, voiced_probs


def _smooth_f0(f0: np.ndarray, size: int = 7) -> np.ndarray:
    """NaN 구간을 보간한 뒤 median으로 기준 멜로디 곡선을 부드럽게."""
    out = f0.copy().astype(float)
    valid = np.isfinite(out) & (out > 0)
    if not np.any(valid):
        return out
    idx = np.arange(len(out))
    out[~valid] = np.interp(idx[~valid], idx[valid], out[valid])
    out = median_filter(out, size=size)
    out[~valid] = np.nan
    return out


def extract_melody_from_harmonic(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    n_frames: int,
    *,
    y_harm: np.ndarray | None = None,
) -> np.ndarray:
    """
    [메모] MR 포함 녹음에서 HPSS 조화음 성분의 F0 = 기준 멜로디(Reference Melody) 추정.
    """
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    f0, _, _ = librosa.pyin(
        y_harm, fmin=FMIN, fmax=FMAX, sr=sr, hop_length=hop_length
    )
    if len(f0) < n_frames:
        f0 = np.pad(f0, (0, n_frames - len(f0)), constant_values=np.nan)
    else:
        f0 = f0[:n_frames]
    return _smooth_f0(f0)


def load_melody_from_midi(
    midi_path: Path, times: np.ndarray
) -> np.ndarray:
    """MIDI 악보에서 프레임별 기준 피치(Hz) 생성."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(str(midi_path))
    f0_ref = np.full(len(times), np.nan, dtype=float)
    notes = []
    for inst in pm.instruments:
        if not inst.is_drum:
            notes.extend(inst.notes)
    if not notes:
        return f0_ref
    for note in notes:
        hz = pretty_midi.note_number_to_hz(note.pitch)
        mask = (times >= note.start) & (times <= note.end)
        f0_ref[mask] = hz
    return _smooth_f0(f0_ref, size=5)


def build_reference_from_guide_audio(
    guide_path: Path, sr: int, hop_length: int, n_frames: int
) -> tuple[np.ndarray, str]:
    """다운로드한 가이드 멜로디 WAV → 기준 F0."""
    y_g, _ = librosa.load(guide_path, sr=sr, mono=True)
    f0_g, _, _ = extract_pitch_pyin(y_g, sr, hop_length, fmin=FMIN, fmax=FMAX)
    if len(f0_g) < n_frames:
        f0_g = np.pad(f0_g, (0, n_frames - len(f0_g)), constant_values=np.nan)
    else:
        f0_g = f0_g[:n_frames]
    return _smooth_f0(f0_g), f"가이드 멜로디 ({guide_path.name})"


def build_reference_melody(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    times: np.ndarray,
    reference_path: Path | None,
    guide_audio_path: Path | None = None,
    *,
    y_harm: np.ndarray | None = None,
    f0_vocal: np.ndarray | None = None,
    fast: bool = False,
    mix_mode: bool = False,
) -> tuple[np.ndarray, str]:
    if guide_audio_path and guide_audio_path.exists():
        return build_reference_from_guide_audio(
            guide_audio_path, sr, hop_length, len(times)
        )
    if reference_path and reference_path.suffix.lower() in {".mid", ".midi"}:
        try:
            f0_ref = load_melody_from_midi(reference_path, times)
            voiced = np.isfinite(f0_ref) & (f0_ref > 0)
            if np.mean(voiced) > 0.05:
                return f0_ref, f"MIDI 악보 ({reference_path.name})"
        except Exception as exc:
            print(f"[안내] MIDI 로드 실패, 조화음 추출로 전환: {exc}")

    if fast and f0_vocal is not None and not mix_mode:
        n = len(times)
        f0_ref = _smooth_f0(f0_vocal.copy())
        if len(f0_ref) < n:
            f0_ref = np.pad(f0_ref, (0, n - len(f0_ref)), constant_values=np.nan)
        else:
            f0_ref = f0_ref[:n]
        return f0_ref, "보컬 F0 기반 기준 멜로디 (빠른 모드)"

    if mix_mode and f0_vocal is not None:
        # MR/유튜브 믹스: 조화음 멜로디 + 보컬 F0 블렌드
        n = len(times)
        f0_harm = extract_melody_from_harmonic(
            y, sr, hop_length, n, y_harm=y_harm
        )
        f0_vocal_smooth = _smooth_f0(f0_vocal.copy())[:n]
        if len(f0_vocal_smooth) < n:
            f0_vocal_smooth = np.pad(
                f0_vocal_smooth, (0, n - len(f0_vocal_smooth)), constant_values=np.nan
            )
        both = (
            np.isfinite(f0_harm)
            & (f0_harm > 0)
            & np.isfinite(f0_vocal_smooth)
            & (f0_vocal_smooth > 0)
        )
        f0_ref = f0_harm.copy()
        if np.any(both):
            f0_ref[both] = 0.55 * f0_harm[both] + 0.45 * f0_vocal_smooth[both]
        return f0_ref, "믹스 대응 기준 멜로디 (조화음+보컬 블렌드)"

    f0_ref = extract_melody_from_harmonic(
        y, sr, hop_length, len(times), y_harm=y_harm
    )
    return f0_ref, "조화음 기반 기준 멜로디 (HPSS + F0 추정)"


def pitch_to_cents_deviation(f0_hz: np.ndarray) -> np.ndarray:
    voiced = np.isfinite(f0_hz) & (f0_hz > 0)
    cents = np.full_like(f0_hz, np.nan, dtype=float)
    if not np.any(voiced):
        return cents
    midi = librosa.hz_to_midi(f0_hz[voiced])
    nearest = np.round(midi)
    cents[voiced] = (midi - nearest) * 100
    return cents


def cents_vs_reference(f0: np.ndarray, f0_ref: np.ndarray) -> np.ndarray:
    """기준 멜로디 대비 센트 편차 (Cent deviation vs reference)."""
    both = (
        np.isfinite(f0)
        & np.isfinite(f0_ref)
        & (f0 > 0)
        & (f0_ref > 0)
    )
    err = np.full_like(f0, np.nan, dtype=float)
    err[both] = 1200.0 * np.log2(f0[both] / f0_ref[both])
    return err


def _group_consecutive_indices(mask: np.ndarray) -> list[np.ndarray]:
    idx = np.where(mask)[0]
    if idx.size == 0:
        return []
    breaks = np.where(np.diff(idx) > 1)[0] + 1
    return [g for g in np.split(idx, breaks) if g.size > 0]


def _classify_voiced_chunk(f0_chunk: np.ndarray, duration_sec: float) -> str:
    if duration_sec < 0.2:
        return "transition"
    midi = librosa.hz_to_midi(f0_chunk)
    t = np.linspace(0, 1, len(midi))
    detrended = midi - np.polyval(np.polyfit(t, midi, 1), t)
    extent_cents = float((np.max(detrended) - np.min(detrended)) * 100)
    zcr = float(np.sum(np.diff(np.sign(detrended)) != 0) / max(duration_sec, 1e-6))
    if (
        duration_sec >= 0.35
        and VIBRATO_EXTENT_MIN_CENTS <= extent_cents <= VIBRATO_EXTENT_MAX_CENTS
        and VIBRATO_ZCR_MIN <= zcr <= VIBRATO_ZCR_MAX
    ):
        return "vibrato"
    if duration_sec >= SUSTAINED_MIN_SEC and extent_cents < 42:
        return "sustained"
    return "transition"


def _segments_from_mask(
    times: np.ndarray,
    f0: np.ndarray,
    mask: np.ndarray,
    values: np.ndarray,
    *,
    vs_reference: bool,
    threshold_cents: float,
) -> list[PitchDeviationSegment]:
    segments: list[PitchDeviationSegment] = []
    for group in _group_consecutive_indices(mask):
        start_t, end_t = float(times[group[0]]), float(times[group[-1]])
        if end_t - start_t < MIN_SEGMENT_SEC:
            continue
        seg_v = np.abs(values[group])
        segments.append(
            PitchDeviationSegment(
                start_sec=round(start_t, 2),
                end_sec=round(end_t, 2),
                avg_deviation_cents=round(float(np.mean(seg_v)), 1),
                max_deviation_cents=round(float(np.max(seg_v)), 1),
                note_hint=_note_name(float(np.median(f0[group]))),
                vs_reference=vs_reference,
            )
        )
    return segments


def _local_interval_match(f0: np.ndarray, f0_ref: np.ndarray) -> float:
    """F0 vs 기준 멜로디 '간격(Interval)' 일치율 — 절대 높이가 아닌 패턴."""
    both = (
        np.isfinite(f0)
        & np.isfinite(f0_ref)
        & (f0 > 0)
        & (f0_ref > 0)
    )
    if np.sum(both) < 4:
        return 0.0
    u_m = librosa.hz_to_midi(f0[both])
    g_m = librosa.hz_to_midi(f0_ref[both])
    err = np.abs(np.diff(u_m) - np.diff(g_m))
    return float(np.mean(err <= 1.0) * 100.0)


def analyze_pitch_regions(
    times: np.ndarray,
    f0: np.ndarray,
    cents: np.ndarray,
    cents_ref: np.ndarray,
    f0_reference: np.ndarray,
    reference_source: str,
    voiced_probs: np.ndarray | None = None,
    y: np.ndarray | None = None,
    sr: int = ANALYSIS_SR,
    hop_length: int = 512,
    y_harm: np.ndarray | None = None,
    fast: bool = False,
) -> PitchAnalysis:
    n = len(f0)
    frame_labels = np.array([""] * n, dtype=object)
    voiced = np.isfinite(f0) & (f0 > 0)
    frame_labels[~voiced] = ""

    if voiced_probs is None or len(voiced_probs) != n:
        voiced_probs = np.where(voiced, 0.85, 0.0).astype(float)

    frame_dt = float(np.median(np.diff(times))) if len(times) > 1 else 0.01
    for group in _group_consecutive_indices(voiced):
        label, _ = classify_voiced_chunk_research(
            f0[group], float(times[group[-1]] - times[group[0]]), frame_dt
        )
        frame_labels[group] = label

    voiced_labels = frame_labels[voiced]
    sustained_ratio = float(np.mean(voiced_labels == "sustained")) if voiced_labels.size else 0.0
    vibrato_ratio = float(np.mean(voiced_labels == "vibrato")) if voiced_labels.size else 0.0

    eval_mask = (
        voiced
        & (frame_labels != "vibrato")
        & np.isfinite(cents_ref)
        & (voiced_probs >= VOICED_PROB_MIN)
    )
    if not np.any(eval_mask):
        eval_mask = voiced & (frame_labels != "vibrato") & np.isfinite(cents_ref)
    if not np.any(eval_mask):
        eval_mask = voiced & np.isfinite(cents_ref)
    if not np.any(eval_mask):
        eval_mask = np.isfinite(cents_ref) & (np.abs(cents_ref) < 400)

    if np.any(eval_mask):
        melody_match_ratio = float(
            np.mean(np.abs(cents_ref[eval_mask]) <= MELODY_MATCH_CENTS)
        )
    else:
        melody_match_ratio = 0.0

    research = None
    if y is not None:
        research = build_research_metrics(
            y=y,
            sr=sr,
            hop_length=hop_length,
            times=times,
            f0=f0,
            voiced_probs=voiced_probs,
            cents_ref=cents_ref,
            eval_mask=eval_mask,
            frame_labels=frame_labels,
            y_harm=y_harm,
            fast=fast,
        )
        if research.melody_match_weighted > 0:
            melody_match_ratio = research.melody_match_weighted
        elif melody_match_ratio <= 0 and np.any(eval_mask):
            melody_match_ratio = float(
                np.mean(np.abs(cents_ref[eval_mask]) <= MELODY_MATCH_CENTS)
            )

    stable_mask = (
        eval_mask & (np.abs(cents_ref) <= MELODY_MATCH_CENTS)
    )
    if not np.any(stable_mask):
        stable_mask = (
            voiced
            & (frame_labels != "vibrato")
            & np.isfinite(cents)
            & (np.abs(cents) <= SUSTAINED_STABLE_CENTS)
        )

    stable_regions: list[tuple[float, float]] = []
    for group in _group_consecutive_indices(stable_mask):
        if times[group[-1]] - times[group[0]] >= MIN_SEGMENT_SEC:
            stable_regions.append(
                (round(float(times[group[0]]), 2), round(float(times[group[-1]]), 2))
            )

    ref_off = (
        eval_mask
        & (frame_labels == "sustained")
        & (np.abs(cents_ref) >= REFERENCE_DEVIATION_CENTS)
    )
    deviation_segments = _segments_from_mask(
        times, f0, ref_off, cents_ref, vs_reference=True, threshold_cents=REFERENCE_DEVIATION_CENTS
    )
    if not deviation_segments:
        local_off = (
            voiced
            & (frame_labels != "vibrato")
            & np.isfinite(cents)
            & (np.abs(cents) >= SUSTAINED_DEVIATION_CENTS)
        )
        deviation_segments = _segments_from_mask(
            times, f0, local_off, cents, vs_reference=False, threshold_cents=SUSTAINED_DEVIATION_CENTS
        )

    return PitchAnalysis(
        cents=cents,
        cents_vs_reference=cents_ref,
        frame_labels=frame_labels,
        deviation_segments=deviation_segments,
        stable_regions=stable_regions,
        sustained_ratio=sustained_ratio,
        vibrato_ratio=vibrato_ratio,
        melody_match_ratio=melody_match_ratio,
        reference_source=reference_source,
        f0_reference=f0_reference,
        voiced_probs=voiced_probs,
        research=research,
        f0_user=f0.copy(),
        interval_match_ratio=_local_interval_match(f0, f0_reference),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Stage 1 — 음정 (기준 멜로디 대비 센트 편차)
# ═══════════════════════════════════════════════════════════════════════════


def stage1_pitch_accuracy(
    pitch: PitchAnalysis, dtw_result: object | None = None
) -> StageResult:
    blocks: list[CoachingBlock] = []
    ref_valid = np.isfinite(pitch.cents_vs_reference) & (np.abs(pitch.cents_vs_reference) < 300)
    eval_frames = int(np.sum(ref_valid))
    abs_voiced = int(np.sum(np.isfinite(pitch.cents)))

    if eval_frames < 10:
        if abs_voiced >= 15:
            valid = np.isfinite(pitch.cents)
            stable_pct = float(np.mean(np.abs(pitch.cents[valid]) <= SUSTAINED_STABLE_CENTS)) * 100
            score = max(30.0, min(100.0, stable_pct * 0.88 + pitch.sustained_ratio * 12))
            if pitch.research and pitch.research.mean_abs_cents_ref < PITCH_ACCEPTABLE_CENTS:
                score = max(score, 75.0)
            summary = (
                f"MR/유튜브 믹스 — 반음 기준 음정 안정도 {stable_pct:.0f}% "
                f"(지속음 {pitch.sustained_ratio * 100:.0f}%)"
            )
            blocks.append(
                CoachingBlock(
                    result=f"믹스 녹음에서도 음정 안정도 {stable_pct:.0f}%로 측정됐습니다.",
                    cause=(
                        "유튜브·MR 포함 녹음은 가이드 멜로디 대비 점수가 낮게 나올 수 있어 "
                        "반음(크로매틱) 기준 안정도로 재평가했습니다."
                    ),
                    solution=(
                        "더 정확한 분석: 이어폰 MR + 마이크 목소리만 녹음, "
                        "또는 사이드바에서 「정밀 분석」+ 곡 제목(유튜브 가이드) 사용"
                    ),
                )
            )
            return StageResult(
                stage=1,
                title=STAGE_TITLES[1],
                score=round(score, 1),
                summary=summary,
                coaching_blocks=blocks,
                details={"mix_fallback": True, "stable_pct": stable_pct},
            )
        return StageResult(
            stage=1,
            title=STAGE_TITLES[1],
            score=0.0,
            summary="노래 소리가 너무 적게 잡혀 음정 분석이 어렵습니다.",
            coaching_blocks=[
                CoachingBlock(
                    result="음정을 채점할 만큼 목소리가 녹음에 안 잡혔어요.",
                    cause=(
                        "마이크가 멀거나, 소리 없이 쉬는 구간이 너무 길거나, "
                        "녹음 볼륨이 너무 낮을 때 이렇게 나옵니다."
                    ),
                    solution=(
                        "① 마이크에서 15~20cm 거리 ② '아—' 5초 롱톤을 3번 녹음 "
                        "③ 스마트폰이면 녹음 앱에서 입력 레벨을 올린 뒤 다시 업로드하세요."
                    ),
                )
            ],
        )

    match_pct = pitch.melody_match_ratio * 100
    seg_penalty = min(20.0, len(pitch.deviation_segments) * 2.5)
    score = max(0.0, min(100.0, match_pct * 0.85 + pitch.sustained_ratio * 15 - seg_penalty))
    if pitch.research:
        score = research_pitch_score(pitch.research, match_pct)
        if pitch.research.pitch_tier == "pro" and score < 70:
            score = max(score, 72.0)
        if pitch.research.pitch_tier == "good" and score < 55:
            score = max(score, 58.0)

    # 인터벌(음정 간격) 일치 — 절대 높이보다 멜로디 '패턴' 반영
    if pitch.interval_match_ratio > 0:
        score = max(
            score,
            min(100.0, pitch.interval_match_ratio * 0.55 + match_pct * 0.25 + 15),
        )

    dtw_accuracy = None
    dtw_interval = None
    if dtw_result is not None:
        dtw_accuracy = getattr(
            dtw_result, "musical_accuracy_percent", None
        ) or getattr(dtw_result, "accuracy_percent", None)
        dtw_interval = getattr(dtw_result, "interval_match_percent", None)
        if dtw_accuracy is not None:
            score = max(0.0, min(100.0, score * 0.35 + float(dtw_accuracy) * 0.65))
        if getattr(dtw_result, "expressiveness_bonus", 0):
            score = min(100.0, score + float(dtw_result.expressiveness_bonus) * 0.4)

    summary = pitch_summary(
        match_pct,
        pitch.sustained_ratio * 100,
        pitch.vibrato_ratio * 100,
        len(pitch.deviation_segments),
        float(dtw_accuracy) if dtw_accuracy is not None else None,
    )
    if pitch.research:
        tier_ko = {
            "pro": "프로급 근접",
            "good": "양호",
            "fair": "보통",
            "needs_work": "보완 필요",
        }.get(pitch.research.pitch_tier, "")
        summary += f" · 평균 음정 편차 {pitch.research.mean_abs_cents_ref:.0f}센트 ({tier_ko})"
        if pitch.research.vibrato and pitch.research.vibrato.rate_hz > 0:
            summary += f" · 비브라토 {pitch.research.vibrato.rate_hz}Hz"
    if pitch.interval_match_ratio > 0:
        summary += f" · 인터벌 일치 {pitch.interval_match_ratio:.0f}%"
    if dtw_interval is not None:
        summary += f" · DTW 간격 {dtw_interval:.0f}%"
    if dtw_result and getattr(dtw_result, "rubato_detected", False):
        summary += " · 루바토(표현적 박자) 인정"

    if match_pct < 70:
        blocks.append(
            CoachingBlock(
                result=(
                    f"가이드 멜로디와 맞지 않는 구간이 많아요. "
                    f"전체의 {100 - match_pct:.0f}% 정도에서 음정이 흔들립니다."
                ),
                cause=(
                    f"같은 멜로디인데 피치(높낮이)가 ±{MELODY_MATCH_CENTS}센트(반음의 ¼ 정도) "
                    f"이상 벗어난 구간이 반복됐습니다. "
                    f"기준: {pitch.reference_source}."
                ),
                solution=(
                    "① 피아노·피아노 앱으로 해당 구간 음을 먼저 듣기 "
                    "② 5초 롱톤 10번 (입 모양 고정) "
                    "③ 틀린 구간만 유튜브 0.5배속으로 따라 부르기 10회 "
                    "④ 다시 녹음해서 같은 구간 점수 비교"
                ),
            )
        )

    if dtw_result is not None and getattr(dtw_result, "deviation_segments", None):
        worst_dtw = max(
            dtw_result.deviation_segments,
            key=lambda s: s.max_cent_error,
        )
        blocks.append(
            CoachingBlock(
                result=(
                    f"{_time_range(worst_dtw.user_start_sec, worst_dtw.user_end_sec)} 구간에서 "
                    f"가이드보다 음정이 많이 어긋났어요."
                ),
                cause=(
                    f"가이드 {_time_range(worst_dtw.ref_start_sec, worst_dtw.ref_end_sec)}와 비교했을 때 "
                    f"평균 {cent_to_words(worst_dtw.avg_cent_error)}, "
                    f"최대 {cent_to_words(worst_dtw.max_cent_error)}. "
                    f"박자가 살짝 밀려도 음정만 따로 맞춰 본 결과입니다."
                ),
                solution=(
                    f"① 해당 구간만 0.5배속 재생 ② 가이드 한 음 → 내 목소리 한 음 순서로 맞추기 "
                    f"③ 메트로놈 60BPM으로 8번 반복 ④ 원템포로 4번"
                ),
            )
        )

    if pitch.deviation_segments:
        worst = max(pitch.deviation_segments, key=lambda s: s.max_deviation_cents)
        ref_tag = "기준 멜로디 대비" if worst.vs_reference else "반음 기준"
        blocks.append(
            CoachingBlock(
                result=(
                    f"{_time_range(worst.start_sec, worst.end_sec)} ({worst.note_hint})에서 "
                    f"음정이 특히 흔들렸어요."
                ),
                cause=(
                    f"{ref_tag} {cent_to_words(worst.max_deviation_cents)} "
                    f"(최대 {worst.max_deviation_cents:.0f}센트). "
                    f"길게 붙인 음(롱톤) 구간에서 자주 나타납니다."
                ),
                solution=(
                    f"① {_time_range(worst.start_sec, worst.end_sec)}만 10번 루프 재생하며 듣기 "
                    f"② 피아노 {worst.note_hint} 롱톤 5초 × 5회 "
                    f"③ 해당 가사 한 줄만 메트로놈 60BPM으로 8번 "
                    f"④ 입 모양·혀 위치를 녹음과 똑같이 유지"
                ),
            )
        )

    if pitch.vibrato_ratio > 0.12 and match_pct >= 65:
        blocks.append(
            CoachingBlock(
                result="비브라토는 들리는데, 그 전후로 음정을 먼저 고정해야 해요.",
                cause=(
                    f"비브라토 구간이 {pitch.vibrato_ratio * 100:.0f}% 감지됐습니다. "
                    "비브라토 들어가기 전 음이 흔들리면 전체적으로 음정이 안 맞아 보입니다."
                ),
                solution=(
                    "① 비브라토 넣기 전 1초는 떨림 없이 롱톤 "
                    "② 비브라토 후 1초도 같은 음으로 마무리 "
                    "③ 피아노 기준음 위에서 '와—와—' 느리게 연습"
                ),
            )
        )

    if pitch.research and pitch.research.vibrato and pitch.research.vibrato.quality == "wobble":
        v = pitch.research.vibrato
        blocks.append(
            CoachingBlock(
                result=f"비브라토가 느려요 ({v.rate_hz}Hz) — '떨림'처럼 들릴 수 있어요.",
                cause=(
                    f"가수 평균 비브라토 4.5–6.5Hz인데 지금 {v.rate_hz}Hz · "
                    f"흔들림 폭 {v.extent_cents:.0f}센트."
                ),
                solution="호흡 지지 유지 · '와—와—' 1초에 5회 흔들리게 · 속도만 점점 올리기.",
            )
        )
    elif pitch.research and pitch.research.vibrato and pitch.research.vibrato.quality == "bleat":
        v = pitch.research.vibrato
        blocks.append(
            CoachingBlock(
                result=f"비브라토가 빨라요 ({v.rate_hz}Hz) — 긴장된 느낌.",
                cause="7Hz 이상은 bleat 구간 — 목·턱 긴장과 연관.",
                solution="어깨·목 힘 빼고 · 비브라토 폭 유지한 채 속도 5Hz 전후로 낮추기.",
            )
        )

    if not blocks:
        blocks.append(
            CoachingBlock(
                result="전체적으로 가이드 멜로디와 음정이 잘 맞아요.",
                cause=(
                    f"일치율 {match_pct:.0f}%, 틀린 구간 {len(pitch.deviation_segments)}곳. "
                    "다음 단계는 고음·긴 구간에서도 같은 안정감 유지입니다."
                ),
                solution=(
                    "고음만 키를 반음 낮춰(승키 연습) 편하게 부른 뒤, "
                    "원키로 올라오며 같은 입 모양을 유지해 보세요."
                ),
            )
        )

    if score < 25 and abs_voiced >= 15:
        valid = np.isfinite(pitch.cents)
        stable_pct = float(np.mean(np.abs(pitch.cents[valid]) <= SUSTAINED_STABLE_CENTS)) * 100
        abs_score = max(35.0, min(100.0, stable_pct * 0.85 + pitch.sustained_ratio * 12))
        if abs_score > score:
            score = abs_score
            summary = (
                f"믹스/MR 녹음 보정 — 반음 기준 안정도 {stable_pct:.0f}% "
                f"(멜로디 일치 {match_pct:.0f}%)"
            )

    return StageResult(
        stage=1,
        title=STAGE_TITLES[1],
        score=round(score, 1),
        summary=summary,
        coaching_blocks=blocks,
        details={
            "melody_match_ratio": round(pitch.melody_match_ratio, 3),
            "mean_abs_cents": pitch.research.mean_abs_cents_ref if pitch.research else None,
            "pitch_tier": pitch.research.pitch_tier if pitch.research else None,
            "voiced_prob_mean": pitch.research.voiced_prob_mean if pitch.research else None,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2 — 박자 (보컬 Energy Envelope)
# ═══════════════════════════════════════════════════════════════════════════


def extract_vocal_energy_envelope(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    *,
    y_harm: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    rms = librosa.feature.rms(y=y_harm, hop_length=hop_length)[0]
    rms = uniform_filter1d(rms, size=5)
    n = min(len(rms), len(f0))
    voiced = np.isfinite(f0[:n]) & (f0[:n] > 0)
    env = np.full(n, np.nan)
    env[voiced] = rms[:n][voiced]
    env_times = librosa.frames_to_time(np.arange(n), sr=sr, hop_length=hop_length)
    return env_times, env


def stage2_rhythm_stability(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    research: VoiceResearchMetrics | None = None,
    *,
    y_harm: np.ndarray | None = None,
    dtw_result: object | None = None,
) -> StageResult:
    env_times, env = extract_vocal_energy_envelope(
        y, sr, hop_length, f0, y_harm=y_harm
    )
    valid = np.isfinite(env)
    blocks: list[CoachingBlock] = []

    if np.sum(valid) < 20:
        return StageResult(
            stage=2,
            title=STAGE_TITLES[2],
            score=50.0,
            summary="목소리 세기 변화가 적어 박자 분석이 어렵습니다.",
            coaching_blocks=[
                CoachingBlock(
                    result="박자를 볼 만큼 ‘소리 뱉는 타이밍’이 충분히 잡히지 않았어요.",
                    cause="녹음이 너무 짧거나, 목소리가 너무 작거나, MR만 크고 보컬이 작을 때 이렇게 나옵니다.",
                    solution=(
                        "① 메트로놈 60BPM ② 박마다 '라—' 한 음씩 8번 (손뼉과 동시에) "
                        "③ MR 줄이고 목소리만 다시 녹음"
                    ),
                )
            ],
        )

    log_env = np.log(env[valid] + 1e-8)
    d_env = np.diff(log_env)
    attack_idx = np.where(d_env > np.percentile(d_env, 72))[0] + 1
    attack_times = env_times[valid][attack_idx]

    if attack_times.size < 4:
        return StageResult(
            stage=2,
            title=STAGE_TITLES[2],
            score=55.0,
            summary="박자 포인트가 적어 리듬 점수를 낮게 잡았습니다.",
            coaching_blocks=[
                CoachingBlock(
                    result="한 박 한 박 ‘딱’ 소리 내는 지점이 적어요.",
                    cause="쉬는 구간이 길거나, 한 음을 길게만 끌면 박자 분석이 어렵습니다.",
                    solution=(
                        "메트로놈 80BPM · 박마다 '다—' 한 음절씩 8번 · "
                        "손뼉 칠 때와 입을 여는 타이밍이 같아야 합니다."
                    ),
                )
            ],
        )

    gaps = np.diff(attack_times)
    gaps = gaps[(gaps > 0.1) & (gaps < 3.0)]
    rhythm_cv = float(np.std(gaps) / (np.mean(gaps) + 1e-6)) if gaps.size >= 2 else 1.0
    cv_superflux = research.rhythm_cv_superflux if research else None
    score = research_rhythm_score(cv_superflux, rhythm_cv)

    summary = rhythm_summary(int(attack_times.size), rhythm_cv)
    if cv_superflux is not None:
        summary += f" · Superflux 박자 지수 {cv_superflux:.2f} ({rhythm_cv_to_words(cv_superflux)})"

    rhythm_cv_eval = cv_superflux if cv_superflux is not None else rhythm_cv
    if score < 30 and int(np.sum(np.isfinite(f0) & (f0 > 0))) >= 50:
        score = max(score, 45.0)
        summary += " · MR/믹스 녹음 박자 보정 적용"

    if dtw_result is not None and getattr(dtw_result, "rubato_detected", False):
        rubato_s = float(getattr(dtw_result, "rubato_score", 0) or 0)
        bonus = float(getattr(dtw_result, "expressiveness_bonus", 0) or 0)
        score = min(100.0, max(score, rubato_s * 0.5 + score * 0.5) + bonus * 0.3)
        summary += f" · 루바토 표현력 {rubato_s:.0f}점"
        blocks.append(
            CoachingBlock(
                result="박자를 살짝 당기거나 밀어도 멜로디 라인은 유지하고 있어요.",
                cause="루바토(Rubato) — 가수의 의도적 시간 해석으로 판단됩니다.",
                solution="이 표현은 강점입니다. 원곡 따라 부를 때는 메트로놈으로 기준 박도 함께 연습하세요.",
            )
        )

    if rhythm_cv_eval > 0.28:
        avg_gap = float(np.mean(gaps)) if gaps.size >= 2 else 0.0
        blocks.append(
            CoachingBlock(
                result=f"박자가 자주 어긋나요. {rhythm_cv_to_words(rhythm_cv)}",
                cause=(
                    f"소리를 내는 간격이 들쭉날쭉합니다 (지수 {rhythm_cv_eval:.2f}, 목표 0.28 이하). "
                    f"{f'평균 {avg_gap:.1f}초마다 한 번씩 소리를 내는데 간격이 일정하지 않아요. ' if avg_gap else ''}"
                    "Superflux onset(논문 Böck 2013)으로 비브라토 오검출을 줄여 분석했습니다."
                ),
                solution=(
                    "① 메트로놈 70BPM 켜기 ② 문제 구간 2마디만 골라 "
                    "③ 손뼉 1번 → 가사 1음절 (동시에) 5세트 "
                    "④ 맞으면 75BPM → 80BPM으로 올리기 "
                    "⑤ 유튜브에서 '자음은 박 직전, 모음은 박에' 연습 영상 참고"
                ),
            )
        )
    else:
        blocks.append(
            CoachingBlock(
                result="박자·리듬이 비교적 안정적이에요.",
                cause=f"박 간격 지수 {rhythm_cv:.2f} — 학원·유튜브에서 말하는 '박 잘 탄다' 수준입니다.",
                solution="빠른 후렴만 0.75배속으로 5번 연습한 뒤 원템포로 돌아오세요.",
            )
        )

    return StageResult(
        stage=2,
        title=STAGE_TITLES[2],
        score=round(score, 1),
        summary=summary,
        coaching_blocks=blocks,
        details={
            "rhythm_cv": round(rhythm_cv, 3),
            "rhythm_cv_superflux": cv_superflux,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3 — 호흡·음색 (Energy Envelope + 고주파 배음)
# ═══════════════════════════════════════════════════════════════════════════


def detect_breath_mismatch_segments(
    rms: np.ndarray, rms_times: np.ndarray, voiced: np.ndarray
) -> list[BreathMismatchSegment]:
    log_r = np.log(rms + 1e-8)
    smooth = uniform_filter1d(log_r, size=9)
    d = np.diff(smooth)
    raw: list[BreathMismatchSegment] = []
    for i, delta in enumerate(d):
        if not (voiced[i] and voiced[i + 1]):
            continue
        if delta <= BREATH_DROP_THRESHOLD:
            kind = "drop"
        elif delta >= BREATH_SURGE_THRESHOLD:
            kind = "surge"
        else:
            continue
        t0, t1 = float(rms_times[i]), float(rms_times[i + 1])
        if raw and raw[-1].issue_type == kind and abs(raw[-1].end_sec - t0) < 0.2:
            raw[-1] = BreathMismatchSegment(raw[-1].start_sec, round(t1, 2), kind)
        else:
            raw.append(BreathMismatchSegment(round(t0, 2), round(t1, 2), kind))

    merged: list[BreathMismatchSegment] = []
    for seg in raw:
        if seg.end_sec - seg.start_sec < BREATH_MIN_DURATION_SEC:
            seg = BreathMismatchSegment(
                seg.start_sec,
                round(seg.start_sec + BREATH_MIN_DURATION_SEC, 2),
                seg.issue_type,
            )
        if merged and merged[-1].issue_type == seg.issue_type:
            if seg.start_sec - merged[-1].end_sec < 0.35:
                merged[-1] = BreathMismatchSegment(
                    merged[-1].start_sec, seg.end_sec, seg.issue_type
                )
                continue
        merged.append(seg)
    return merged


def analyze_timbre_hf_segments(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    times: np.ndarray,
    *,
    y_harm: np.ndarray | None = None,
) -> tuple[np.ndarray, list[TimbreIssueSegment]]:
    """고주파 배음 에너지 비율 하락 → 음색 일관성(Timbre consistency) 이슈."""
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    n_fft = 2048
    S = np.abs(librosa.stft(y_harm, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    hf_mask = freqs >= HF_CUTOFF_HZ
    hf_ratio = S[hf_mask, :].sum(axis=0) / (S.sum(axis=0) + 1e-8)

    n = min(len(hf_ratio), len(f0), len(times))
    voiced = np.isfinite(f0[:n]) & (f0[:n] > 0)
    ratio = hf_ratio[:n]
    t = times[:n]

    baseline = float(np.median(ratio[voiced])) if np.any(voiced) else 0.0
    issue_mask = np.zeros(n, dtype=bool)
    if baseline > 0:
        drop = (baseline - ratio) / baseline * 100.0
        issue_mask = voiced & (drop >= HF_DROP_PERCENT)

    segments: list[TimbreIssueSegment] = []
    for group in _group_consecutive_indices(issue_mask):
        start_t, end_t = float(t[group[0]]), float(t[group[-1]])
        if end_t - start_t < MIN_SEGMENT_SEC:
            continue
        seg_drop = (baseline - ratio[group]) / baseline * 100.0
        segments.append(
            TimbreIssueSegment(
                start_sec=round(start_t, 2),
                end_sec=round(end_t, 2),
                hf_drop_percent=round(float(np.mean(seg_drop)), 1),
            )
        )
    return ratio, segments


def stage3_breath_support(
    y: np.ndarray,
    sr: int,
    hop_length: int,
    f0: np.ndarray,
    times: np.ndarray,
    research: VoiceResearchMetrics | None = None,
    *,
    y_harm: np.ndarray | None = None,
    skip_timbre: bool = False,
) -> tuple[StageResult, list[BreathMismatchSegment], list[TimbreIssueSegment]]:
    if y_harm is None:
        y_harm, _ = librosa.effects.hpss(y)
    rms = librosa.feature.rms(y=y_harm, hop_length=hop_length)[0]
    rms = median_filter(rms, size=5)
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    n = min(len(rms), len(f0))
    voiced = np.isfinite(f0[:n]) & (f0[:n] > 0)
    rms_v = rms[:n][voiced]
    blocks: list[CoachingBlock] = []

    _, timbre_issues = (
        (np.array([]), [])
        if skip_timbre
        else analyze_timbre_hf_segments(
            y, sr, hop_length, f0, times, y_harm=y_harm
        )
    )

    if rms_v.size < 10 and int(np.sum(voiced)) >= 20:
        from musical_analysis import analyze_harmonic_timbre

        harm = analyze_harmonic_timbre(
            y, sr, hop_length, f0, times, y_harm=y_harm
        )
        f0_score = min(85.0, 45.0 + float(np.sum(voiced)) * 0.05)
        score = max(f0_score, harm.timbre_score * 0.7)
        if harm.is_pro_like:
            score = max(score, 80.0)
        return (
            StageResult(
                stage=3,
                title=STAGE_TITLES[3],
                score=round(score, 1),
                summary=(
                    f"믹스 녹음 — 배음 조화 {harm.harmonic_density:.2f} "
                    f"({'프로급' if harm.is_pro_like else '분석'})"
                ),
                coaching_blocks=[
                    CoachingBlock(
                        result="MR/유튜브 믹스라 호흡·음색 세부 분석이 제한됐습니다.",
                        cause="반주가 크면 목소리 세기 변화가 묻혀 호흡 지표가 낮게 나옵니다.",
                        solution="마이크에 목소리만 녹음하면 호흡·음색 점수가 정확해집니다.",
                    )
                ],
                details={
                    "mix_fallback": True,
                    "is_pro_like": harm.is_pro_like,
                    "timbre_score": harm.timbre_score,
                    "harmonic_density": harm.harmonic_density,
                },
            ),
            [],
            timbre_issues,
        )

    if rms_v.size < 10:
        return (
            StageResult(
                stage=3,
                title=STAGE_TITLES[3],
                score=0.0,
                summary="호흡·음색을 볼 만큼 녹음 데이터가 부족합니다.",
                coaching_blocks=[
                    CoachingBlock(
                        result="호흡과 음색 점수를 매기기 어려워요.",
                        cause="노래하는 구간이 너무 짧거나 목소리가 거의 안 잡혔습니다.",
                        solution=(
                            "복식호흡(배로 숨) 후 '아—' 8초 롱톤 5번 녹음 → "
                            "씨(S) 소리 10초 내뱉기 연습 후 다시 업로드"
                        ),
                    )
                ],
            ),
            [],
            timbre_issues,
        )

    mismatch = detect_breath_mismatch_segments(rms[:n], rms_times[:n], voiced)
    drops = [m for m in mismatch if m.issue_type == "drop"]
    surges = [m for m in mismatch if m.issue_type == "surge"]

    env_cv = float(np.std(rms_v) / (np.mean(rms_v) + 1e-6))
    penalty = min(28.0, len(drops) * 2 + len(surges) * 1.5 + len(timbre_issues) * 2)
    if research:
        score = research_breath_score(env_cv, research, penalty)
    else:
        score = max(0.0, min(100.0, 100 - env_cv * 100 - penalty))

    from musical_analysis import analyze_harmonic_timbre

    harm = analyze_harmonic_timbre(y, sr, hop_length, f0, times, y_harm=y_harm)
    score = max(score, harm.timbre_score * 0.45 + score * 0.55)
    if harm.is_pro_like:
        score = max(score, 80.0)

    summary = breath_summary(env_cv, len(drops) + len(surges), len(timbre_issues))
    summary += f" · 배음 조화 {harm.harmonic_density:.2f}"
    if harm.is_pro_like:
        summary += " · 프로급 음색"
    if research and research.hnr_db is not None:
        summary += f" · HNR {research.hnr_db}dB"
    if research and research.jitter_local_pct is not None:
        summary += f" · 지터 {research.jitter_local_pct}%"

    if env_cv > 0.38:
        blocks.append(
            CoachingBlock(
                result=f"한 번에 쭉 부를 때 힘이 들쭉날쭉해요. {env_cv_to_words(env_cv)}",
                cause=(
                    f"같은 한 줄 안에서도 음량·힘이 {env_cv:.2f}만큼 요동칩니다. "
                    "복식호흡·호흡 지지가 중간에 끊기면 이렇게 나옵니다."
                ),
                solution=(
                    "① '씨—' 소리 10초 내뱉기 (마지막 3초도 힘 유지) 5세트 "
                    "② 한 문장 부를 때 배(복부)에 손 대고 힘 빠지는 순간 다시 시작 "
                    "③ 어깨 올라가면 멈추고 숨 다시 고르기"
                ),
            )
        )

    if timbre_issues:
        t0 = timbre_issues[0]
        blocks.append(
            CoachingBlock(
                result=(
                    f"{_time_range(t0.start_sec, t0.end_sec)}에서 "
                    f"목소리가 탁해지거나 공기 섞인 소리가 났어요."
                ),
                cause=(
                    f"{hf_drop_to_words(t0.hf_drop_percent)} "
                    f"(밝은 소리 성분 {t0.hf_drop_percent:.0f}% 감소). "
                    "성대가 완전히 닫히지 않거나 호흡이 새면 흔히 나타납니다."
                ),
                solution=(
                    f"① {_time_range(t0.start_sec, t0.end_sec)} 구간만 10번 듣기 "
                    "② 피아노 한 음에 '아—' 롱톤, 입술 살짝 모아 성대 붙는 느낌 10분 "
                    "③ 같은 구간 가사만 속도 0.75배로 5번 "
                    "④ 녹음 후 ‘가사 없이 들어도 말처럼 들리는지’ 체크"
                ),
            )
        )

    if drops:
        w = drops[0]
        blocks.append(
            CoachingBlock(
                result=f"{_time_range(w.start_sec, w.end_sec)}에서 갑자기 소리가 작아졌어요 (힘 빠짐).",
                cause="호흡 지지가 끊기면서 음량이 급격히 떨어졌습니다. 긴 구절 끝에서 자주 나옵니다.",
                solution=(
                    "5초 롱톤: 매 1초마다 볼륨이 같은지 확인 · "
                    "3초째 작아지면 처음부터 · 하루 10세트"
                ),
            )
        )

    if surges:
        w = surges[0]
        blocks.append(
            CoachingBlock(
                result=f"{_time_range(w.start_sec, w.end_sec)}에서 갑자기 소리가 튀었어요.",
                cause="목이나 턱에 힘을 주면서 호흡 압이 순간적으로 올라갔습니다.",
                solution=(
                    "강하게 낼 때도 어깨·목 힘 빼기 · "
                    "배(복부)로만 세기 조절 · "
                    "같은 구간 부드럽게 5번 후 다시 강하게"
                ),
            )
        )

    if research and research.hnr_db is not None and research.hnr_db < 10:
        blocks.append(
            CoachingBlock(
                result="목소리에 공기·잡음이 많이 섞여 있어요 (허스·성대 닫힘 약함).",
                cause=f"HNR(하모닉 대 노이즈) {research.hnr_db}dB — 15dB 이상이면 깨끗한 편.",
                solution="성대 닫힘 '아—' 롱톤 10분 · 씨(S) 10초×5세트 · 녹음 후 가사 없이 들어보기.",
            )
        )

    if research and research.jitter_local_pct and research.jitter_local_pct > 1.04:
        blocks.append(
            CoachingBlock(
                result="롱톤에서 음 높이가 미세하게 떨려요 (지터).",
                cause=f"지터 {research.jitter_local_pct}% — Praat 기준 정상 ~1% 이하.",
                solution="한 음에 5초 붙잡기 · 턱·목 힘 빼기 · 피아노 기준음과 동시에 유지.",
            )
        )

    if not blocks:
        blocks.append(
            CoachingBlock(
                result="호흡 지지와 음색이 비교적 안정적이에요.",
                cause=f"호흡·음량 안정도 {env_cv:.2f}.",
                solution="고음 구간만 반음 낮춰 연습(승키) 후 원키로 — 두성·믹스 전환 연습에 좋습니다.",
            )
        )

    return (
        StageResult(
            stage=3,
            title=STAGE_TITLES[3],
            score=round(score, 1),
            summary=summary,
            coaching_blocks=blocks,
            details={
                "envelope_cv": round(env_cv, 3),
                "breath_mismatch": len(mismatch),
                "timbre_issues": len(timbre_issues),
                "hnr_db": research.hnr_db if research else None,
                "jitter_pct": research.jitter_local_pct if research else None,
                "shimmer_pct": research.shimmer_local_pct if research else None,
                "harmonic_density": harm.harmonic_density,
                "timbre_score": harm.timbre_score,
                "is_pro_like": harm.is_pro_like,
            },
        ),
        mismatch,
        timbre_issues,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Stage 4 — 종합
# ═══════════════════════════════════════════════════════════════════════════


def stage4_integrated_coaching(
    stages: list[StageResult],
    pitch: PitchAnalysis,
    breath_issues: list[BreathMismatchSegment],
    *,
    style_preset: object | None = None,
    dtw_result: object | None = None,
    is_pro_like: bool = False,
    teacher: object | None = None,
) -> StageResult:
    from style_presets import apply_score_floor, resolve_preset, weighted_overall

    preset = style_preset or resolve_preset("standard", pitch.reference_source)
    s1, s2, s3 = stages[0], stages[1], stages[2]
    overall = weighted_overall(s1.score, s2.score, s3.score, preset)

    musical_acc = None
    if dtw_result is not None:
        musical_acc = getattr(dtw_result, "musical_accuracy_percent", None)
    overall = apply_score_floor(
        overall,
        stages[:3],
        preset,
        is_pro_like=is_pro_like,
        musical_accuracy=musical_acc,
    )

    # 선생님 관점: 다이내믹·레가토 보너스 (최대 +3)
    if teacher is not None:
        dyn = getattr(teacher, "dynamics_score", 0) or 0
        leg = getattr(teacher, "phrase_legato_score", 0) or 0
        teacher_bonus = 0.0
        if dyn >= 75:
            teacher_bonus += 1.5
        if leg >= 75:
            teacher_bonus += 1.5
        overall = min(100.0, overall + teacher_bonus)

    weakest = min(stages[:3], key=lambda s: s.score)

    lines = [
        "=== 종합 레슨 리포트 ===",
        f"종합 점수: {overall}/100",
        f"평가 프로필: {getattr(preset, 'label', '균형')}",
    ]
    if teacher and getattr(teacher, "praise_line", ""):
        lines.append(f"선생님 한마디: {teacher.praise_line}")
    lines.extend([
        f"가장 먼저 손볼 곳: {weakest.title} ({weakest.score}점)",
        f"기준 멜로디: {pitch.reference_source}",
        "",
    ])
    for s in stages:
        lines.append(f"--- Stage {s.stage}: {s.title} ({s.score}점) ---")
        lines.append(s.summary)
        for block in s.coaching_blocks[:2]:
            lines.append(format_coaching_block(block))
            lines.append("")

    if pitch.deviation_segments:
        lines.append("[음정이 틀린 구간]")
        for seg in pitch.deviation_segments[:6]:
            tag = "가이드 대비" if seg.vs_reference else "해당 구간"
            lines.append(
                f"  - {_time_range(seg.start_sec, seg.end_sec)} | "
                f"{seg.note_hint} | {cent_to_words(seg.max_deviation_cents)} ({tag})"
            )

    if breath_issues:
        lines.append("[호흡·음량 이상 구간]")
        for b in breath_issues[:5]:
            kind = "힘 빠짐" if b.issue_type == "drop" else "소리 튐"
            lines.append(f"  - {_time_range(b.start_sec, b.end_sec)} | {kind}")

    coaching_text = "\n".join(lines)
    primary = weakest.coaching_blocks[0] if weakest.coaching_blocks else None

    blocks = []
    if teacher and getattr(teacher, "praise_line", ""):
        blocks.append(
            CoachingBlock(
                result=teacher.praise_line,
                cause="보컬 레슨에서는 잘하는 것부터 짚어 주는 게 동기부여에 중요해요.",
                solution="칭찬받은 부분은 유지하면서, 아래 ‘손볼 곳’만 집중 연습해 보세요.",
            )
        )
    for tb in getattr(teacher, "extra_blocks", []) or []:
        blocks.append(tb)

    if primary:
        blocks.append(
            CoachingBlock(
                result=(
                    f"종합 {overall}점이에요. 지금은 **{weakest.title}**({weakest.score}점)부터 "
                    f"함께 잡아보면 좋겠어요."
                ),
                cause=primary.cause,
                solution=primary.solution,
            )
        )

    return StageResult(
        stage=4,
        title=STAGE_TITLES[4],
        score=overall,
        summary=f"4단계 {overall}점 ({getattr(preset, 'label', '균형')}) | 우선: {weakest.title}",
        coaching_blocks=blocks,
        details={
            "coaching_text": coaching_text,
            "style_preset": getattr(preset, "id", "standard"),
            "stage_weights": list(getattr(preset, "stage_weights", (0.4, 0.3, 0.3))),
            "teacher_strengths": getattr(teacher, "strengths", []) if teacher else [],
            "dynamics_score": getattr(teacher, "dynamics_score", None) if teacher else None,
            "phrase_legato_score": getattr(teacher, "phrase_legato_score", None) if teacher else None,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# 실행
# ═══════════════════════════════════════════════════════════════════════════


def run_curriculum(
    audio_path: Path,
    reference_path: Path | None = None,
    guide_audio_path: Path | None = None,
    dtw_result: object | None = None,
    song_title: str | None = None,
    *,
    fast_mode: bool = False,
    style_preset: str | None = None,
    on_progress: callable | None = None,
) -> CurriculumReport:
    from style_presets import resolve_preset

    preset = resolve_preset(style_preset, song_title)

    def _prog(pct: float, msg: str) -> None:
        if on_progress:
            on_progress(pct, msg)

    _prog(0.05, "오디오 불러오는 중…")
    y, sr, hop, truncated_from = load_audio(audio_path, fast=fast_mode)
    duration = len(y) / sr

    _prog(0.12, "보컬·MR 분리 중…")
    y_harm, _ = librosa.effects.hpss(y)

    _prog(0.22, "음정(F0) 추출 중…")
    times, f0, voiced_probs, pitch_source = extract_pitch_robust(
        y, sr, hop, y_harm=y_harm, audio_path=audio_path
    )

    from mr_detect import detect_mr_content

    mr = detect_mr_content(y, sr)
    mix_mode = mr.likely_mr or pitch_source in ("vocal", "harmonic")

    ref_path = resolve_reference(reference_path)
    f0_ref, ref_source = build_reference_melody(
        y,
        sr,
        hop,
        times,
        ref_path,
        guide_audio_path=guide_audio_path,
        y_harm=y_harm,
        f0_vocal=f0,
        fast=fast_mode,
        mix_mode=mix_mode,
    )

    cents = pitch_to_cents_deviation(f0)
    cents_ref = cents_vs_reference(f0, f0_ref)
    _prog(0.38, "음정 구간 분석 중…")
    pitch = analyze_pitch_regions(
        times,
        f0,
        cents,
        cents_ref,
        f0_ref,
        ref_source,
        voiced_probs=voiced_probs,
        y=y,
        sr=sr,
        hop_length=hop,
        y_harm=y_harm,
        fast=fast_mode or mix_mode,
    )

    _prog(0.52, "박자·리듬 분석 중…")
    s1 = stage1_pitch_accuracy(pitch, dtw_result=dtw_result)
    s2 = stage2_rhythm_stability(
        y, sr, hop, f0, pitch.research, y_harm=y_harm, dtw_result=dtw_result
    )
    _prog(0.65, "호흡·음색 분석 중…")
    s3, breath_issues, timbre_issues = stage3_breath_support(
        y, sr, hop, f0, times, pitch.research, y_harm=y_harm, skip_timbre=fast_mode and not mix_mode
    )
    is_pro_like = bool(s3.details.get("is_pro_like"))
    _prog(0.72, "선생님 관점 분석 중…")
    from teacher_analysis import build_teacher_assessment

    teacher = build_teacher_assessment(
        stages=[s1, s2, s3],
        pitch=pitch,
        y=y,
        sr=sr,
        hop_length=hop,
        f0=f0,
        times=times,
        y_harm=y_harm,
        dtw_result=dtw_result,
        is_pro_like=is_pro_like,
    )
    _prog(0.75, "코칭 리포트 작성 중…")
    s4 = stage4_integrated_coaching(
        [s1, s2, s3],
        pitch,
        breath_issues,
        style_preset=preset,
        dtw_result=dtw_result,
        is_pro_like=is_pro_like,
        teacher=teacher,
    )

    mr_msg = mr.message
    if pitch_source == "vocal":
        mr_msg = (
            f"유튜브/MR 믹스 — 보컬 강조 추출({pitch_source})으로 분석했습니다. "
            + mr_msg
        )
    if truncated_from and fast_mode:
        mr_msg = (
            f"⚡ 빠른 분석: 전체 {truncated_from:.0f}초 중 앞 {FAST_MAX_DURATION_SEC:.0f}초만 분석. "
            f"정밀 분석으로 전체 구간 확인. "
            + mr_msg
        )

    return CurriculumReport(
        audio_path=audio_path,
        duration_sec=round(duration, 2),
        pitch_deviation_segments=pitch.deviation_segments,
        stable_regions=pitch.stable_regions,
        breath_mismatch_segments=breath_issues,
        timbre_issue_segments=timbre_issues,
        stages=[s1, s2, s3, s4],
        overall_score=s4.score,
        coaching_text=s4.details["coaching_text"],
        reference_source=ref_source,
        song_title=song_title,
        times=times,
        f0=f0,
        f0_reference=f0_ref,
        dtw_result=dtw_result,
        mr_likely=mr.likely_mr,
        mr_message=mr_msg,
        research=pitch.research,
        style_preset_id=preset.id,
        style_preset_label=preset.label,
    )


def _research_to_dict(r: VoiceResearchMetrics | None) -> dict | None:
    if r is None:
        return None
    return {
        "voiced_prob_mean": r.voiced_prob_mean,
        "melody_match_weighted": r.melody_match_weighted,
        "mean_abs_cents": r.mean_abs_cents_ref,
        "pitch_tier": r.pitch_tier,
        "vibrato_rate_hz": r.vibrato.rate_hz if r.vibrato else None,
        "vibrato_extent_cents": r.vibrato.extent_cents if r.vibrato else None,
        "vibrato_quality": r.vibrato.quality if r.vibrato else None,
        "jitter_local_pct": r.jitter_local_pct,
        "shimmer_local_pct": r.shimmer_local_pct,
        "hnr_db": r.hnr_db,
        "singer_formant_ratio": r.singer_formant_ratio,
        "rhythm_cv_superflux": r.rhythm_cv_superflux,
        "notes": r.research_notes,
    }


def report_to_gpt_payload(report: CurriculumReport) -> dict:
    """GPT·JSON 저장용 전체 분석 데이터."""
    pitch_devs = [
        {
            "user_time": f"{s.start_sec}-{s.end_sec}s",
            "note": s.note_hint,
            "max_cent": s.max_deviation_cents,
        }
        for s in report.pitch_deviation_segments[:12]
    ]
    timbre_list = [
        {
            "time": f"{t.start_sec}-{t.end_sec}s",
            "hf_drop_percent": t.hf_drop_percent,
        }
        for t in report.timbre_issue_segments[:12]
    ]
    dtw_dict = None
    if report.dtw_result is not None:
        d = report.dtw_result
        dtw_dict = {
            "accuracy_percent": getattr(d, "accuracy_percent", None),
            "musical_accuracy_percent": getattr(d, "musical_accuracy_percent", None),
            "interval_match_percent": getattr(d, "interval_match_percent", None),
            "absolute_match_percent": getattr(d, "absolute_match_percent", None),
            "rubato_score": getattr(d, "rubato_score", None),
            "expressiveness_bonus": getattr(d, "expressiveness_bonus", None),
            "rubato_detected": getattr(d, "rubato_detected", None),
            "transposition_cents": getattr(d, "transposition_cents", None),
            "mean_cent_error": getattr(d, "mean_cent_error", None),
            "max_cent_error": getattr(d, "max_cent_error", None),
            "matched_frames": getattr(d, "matched_frames", None),
            "deviation_segments": [
                {
                    "user_time": f"{x.user_start_sec}-{x.user_end_sec}s",
                    "reference_time": f"{x.ref_start_sec}-{x.ref_end_sec}s",
                    "max_cent_error": x.max_cent_error,
                    "note": x.note_hint,
                }
                for x in getattr(d, "deviation_segments", [])[:10]
            ],
        }

    s1, s2, s3 = (report.stages[i] if len(report.stages) > i else None for i in range(3))
    s4 = report.stages[3] if len(report.stages) > 3 else None
    stage_details = {
        "pitch": {
            "melody_match_ratio": s1.details.get("melody_match_ratio") if s1 else None,
            "deviation_count": len(report.pitch_deviation_segments),
        },
        "rhythm": {
            "rhythm_cv": s2.details.get("rhythm_cv") if s2 else None,
            "rhythm_cv_superflux": s2.details.get("rhythm_cv_superflux") if s2 else None,
            "rhythm_cv_target": 0.28,
        },
        "breath_timbre": {
            "envelope_cv": s3.details.get("envelope_cv") if s3 else None,
            "timbre_issue_count": len(report.timbre_issue_segments),
            "breath_mismatch_count": len(report.breath_mismatch_segments),
            "hnr_db": s3.details.get("hnr_db") if s3 else None,
            "jitter_pct": s3.details.get("jitter_pct") if s3 else None,
            "harmonic_density": s3.details.get("harmonic_density") if s3 else None,
            "timbre_score": s3.details.get("timbre_score") if s3 else None,
            "is_pro_like": s3.details.get("is_pro_like") if s3 else None,
        },
        "teacher": {
            "strengths": s4.details.get("teacher_strengths") if s4 else None,
            "dynamics_score": s4.details.get("dynamics_score") if s4 else None,
            "phrase_legato_score": s4.details.get("phrase_legato_score") if s4 else None,
        },
        "research": _research_to_dict(report.research),
    }

    from gpt_coach import build_analysis_json

    base = build_analysis_json(
        song_title=report.song_title,
        user_file=report.audio_path.name,
        report_summary={
            "overall_score": report.overall_score,
            "stage_scores": {s.stage: s.score for s in report.stages[:3]},
            "melody_match_percent": round(
                (s1.details.get("melody_match_ratio", 0) or 0) * 100, 1
            )
            if s1
            else None,
            "pitch_deviations": pitch_devs,
            "breath_issues": len(report.breath_mismatch_segments),
            "timbre_issues": len(report.timbre_issue_segments),
        },
        dtw_result=dtw_dict,
        reference_source=report.reference_source,
    )
    base["stage_details"] = stage_details
    base["timbre_segments"] = timbre_list
    base["duration_sec"] = report.duration_sec
    base["mr_likely"] = report.mr_likely
    base["style_preset"] = report.style_preset_id
    base["style_preset_label"] = report.style_preset_label
    return base


def run_full_session(
    audio_path: Path,
    *,
    song_title: str | None = None,
    use_youtube: bool = False,
    reference_path: Path | None = None,
    guide_path: Path | None = None,
    use_gpt: bool = False,
    save_record: bool = False,
    compare: bool = False,
    export_clips: bool = False,
    growth_chart: bool = False,
    save_plot: Path | None = None,
    json_out: Path | None = None,
    keep_cache: bool = False,
    fast_mode: bool = True,
    style_preset: str | None = None,
    user_id: str | None = None,
    on_progress: callable | None = None,
) -> dict:
    """
    CLI·웹 UI 공통 분석 파이프라인.
    Returns dict: report, full_record, paths, texts...
    """
    from action_plan import build_action_plan
    from clip_exporter import export_segment_clips, export_timbre_clips, format_clip_list
    from gpt_coach import generate_gpt_coaching, load_dotenv_if_present
    from progress_chart import generate_growth_chart
    from progress_tracker import (
        build_full_record,
        compare_records,
        find_previous_record,
        load_record,
        save_record as persist_record,
    )

    load_dotenv_if_present(PROJECT_DIR)

    def _prog(pct: float, msg: str) -> None:
        if on_progress:
            on_progress(pct, msg)

    _prog(0.05, "오디오 불러오는 중…")

    if use_youtube and song_title:
        _prog(0.15, "유튜브 가이드 검색 중…")
        report = run_advanced_pipeline(
            audio_path,
            song_title,
            reference_path=reference_path,
            use_youtube=True,
            keep_cache=keep_cache,
            fast_mode=fast_mode,
            style_preset=style_preset,
            on_progress=on_progress,
        )
    else:
        dtw_result = None
        if guide_path and guide_path.exists():
            from dtw_compare import load_and_compare_files

            _prog(0.12, "가이드와 타이밍 비교 중…")
            dtw_result = load_and_compare_files(audio_path, guide_path)
        report = run_curriculum(
            audio_path,
            reference_path,
            guide_audio_path=guide_path,
            dtw_result=dtw_result,
            song_title=song_title,
            fast_mode=fast_mode,
            style_preset=style_preset,
            on_progress=_prog,
        )

    try:
        from feedback_trainer import apply_calibration_to_report

        apply_calibration_to_report(report)
    except Exception:
        pass

    _prog(0.78, "코칭 리포트 정리 중…")

    payload = report_to_gpt_payload(report)
    action_plan = _action_items_to_dict(build_action_plan(report))
    full_record = build_full_record(payload, action_plan=action_plan)

    result = {
        "report": report,
        "full_record": full_record,
        "record_path": None,
        "chart_path": None,
        "clip_paths": [],
        "compare_text": "",
        "gpt_text": "",
        "plot_path": save_plot or PROJECT_DIR / "pitch_result.png",
    }

    saved_path = None
    if json_out:
        import json

        json_out.write_text(
            json.dumps(full_record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        saved_path = json_out

    if save_record:
        saved_path = persist_record(full_record, user_id=user_id)
        result["record_path"] = saved_path

    if compare:
        prev_path = find_previous_record(exclude=saved_path, user_id=user_id)
        if prev_path:
            prev = load_record(prev_path)
            result["compare_text"] = compare_records(full_record, prev)
            result["compare_text"] += f"\n(비교 대상: {prev_path.name})"
        else:
            result["compare_text"] = "비교할 이전 기록이 없습니다."

    if export_clips and not fast_mode:
        _prog(0.78, "문제 구간 클립 추출 중…")
        clips = export_segment_clips(audio_path, report.pitch_deviation_segments)
        if report.timbre_issue_segments:
            clips += export_timbre_clips(audio_path, report.timbre_issue_segments[:3])
        result["clip_paths"] = [c.path for c in clips]
        result["clips_info"] = format_clip_list(clips)

    if growth_chart and save_record and not fast_mode:
        _prog(0.82, "성장 그래프 생성 중…")
        chart = generate_growth_chart(user_id=user_id)
        result["chart_path"] = chart

    if use_gpt:
        _prog(0.85, "GPT 코칭 생성 중…")
        try:
            rag_block = None
            try:
                from coach_rag import build_query_from_analysis, retrieve_for_coaching

                bundle = retrieve_for_coaching(build_query_from_analysis(payload), payload)
                rag_block = bundle.prompt_block or None
            except Exception:
                pass
            result["gpt_text"] = generate_gpt_coaching(payload, rag_block=rag_block)
        except Exception as exc:
            result["gpt_error"] = str(exc)

    plot_path = save_plot or PROJECT_DIR / "pitch_result.png"
    _prog(0.92, "음정 그래프 저장 중…")
    try:
        plot_pitch(
            report.times,
            report.f0,
            report.f0_reference,
            report.stable_regions,
            report.pitch_deviation_segments,
            title=f"음정 맵 - {audio_path.name}",
            save_path=plot_path,
            dpi=72 if fast_mode else 150,
        )
        result["plot_path"] = plot_path
    except Exception as exc:
        result["plot_path"] = None
        result["plot_error"] = str(exc)
    result["fast_mode"] = fast_mode
    _prog(1.0, "완료")
    return result


def _action_items_to_dict(items) -> list[dict]:
    return [
        {
            "priority": i.priority,
            "title": i.title,
            "prescription": i.prescription,
            "practice": i.practice,
            "reason": i.reason,
            "stage": i.stage,
        }
        for i in items
    ]


def run_advanced_pipeline(
    audio_path: Path,
    song_title: str | None,
    *,
    reference_path: Path | None = None,
    use_youtube: bool = False,
    use_gpt: bool = False,
    keep_cache: bool = False,
    fast_mode: bool = False,
    style_preset: str | None = None,
    on_progress: callable | None = None,
) -> CurriculumReport:
    """
    레퍼런스 확보 → DTW 비교 → 커리큘럼 → (선택) GPT 코칭.
    """
    bundle = None
    guide_path = None
    dtw_result = None

    try:
        if use_youtube and song_title:
            from reference_fetcher import fetch_references

            if on_progress:
                on_progress(0.14, "유튜브 가이드 다운로드 중…")
            bundle = fetch_references(song_title, keep_cache=keep_cache)
            guide_path = bundle.guide_path

        if guide_path and guide_path.exists():
            from dtw_compare import load_and_compare_files

            print("[DTW] 가이드 멜로디와 사용자 피치 Time-aligned 비교 중...")
            if on_progress:
                on_progress(0.18, "가이드 멜로디와 비교 중…")
            dtw_result = load_and_compare_files(audio_path, guide_path)
            print(
                f"  DTW 음정 일치율: {dtw_result.accuracy_percent}% | "
                f"평균 센트 편차: {dtw_result.mean_cent_error}"
            )

        report = run_curriculum(
            audio_path,
            reference_path=reference_path,
            guide_audio_path=guide_path,
            dtw_result=dtw_result,
            song_title=song_title,
            fast_mode=fast_mode,
            style_preset=style_preset,
            on_progress=on_progress,
        )
        return report
    finally:
        if bundle is not None and not keep_cache:
            from reference_fetcher import cleanup_cache

            cleanup_cache(bundle)


def _configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def print_report(report: CurriculumReport) -> None:
    print(f"\n파일: {report.audio_path.name} | 길이: {report.duration_sec}초")
    print(f"종합 점수: {report.overall_score}/100")
    print(f"기준 멜로디: {report.reference_source}")
    if report.mr_message:
        tag = "[MR/반주 감지]" if report.mr_likely else "[녹음 환경]"
        print(f"\n{tag} {report.mr_message}")
    print("\n[그래프] 파란=음정 OK | 빨간=음정 틀림 | 초록=가이드 멜로디")

    if report.dtw_result is not None:
        d = report.dtw_result
        musical = getattr(d, "musical_accuracy_percent", None) or getattr(d, "accuracy_percent", None)
        interval = getattr(d, "interval_match_percent", None)
        rubato = getattr(d, "rubato_detected", False)
        print(
            f"\n[음악적 해석] 종합 {musical}%"
            + (f" · 인터벌 {interval}%" if interval is not None else "")
            + (" · 루바토 표현 감지" if rubato else "")
        )

    print("\n-- 음정 틀린 구간 --")
    if not report.pitch_deviation_segments:
        print("  없음 (전체적으로 가이드와 잘 맞음)")
    else:
        for i, seg in enumerate(report.pitch_deviation_segments, 1):
            print(
                f"  [{i}] {_time_range(seg.start_sec, seg.end_sec)} | "
                f"{seg.note_hint} | {cent_to_words(seg.max_deviation_cents)}"
            )

    for stage in report.stages:
        print(f"\n{'=' * 50}")
        print(f"Stage {stage.stage}: {stage.title} | {stage.score}점")
        print(f"요약: {stage.summary}")
        for j, block in enumerate(stage.coaching_blocks, 1):
            print(f"\n  [코칭 {j}]")
            print("  " + format_coaching_block(block).replace("\n", "\n  "))

    print(f"\n{'=' * 50}")
    print(report.coaching_text)

    from action_plan import build_action_plan, format_action_plan

    plan = build_action_plan(report)
    print(format_action_plan(plan))


def _pitch_hz_ylim(
    f0: np.ndarray,
    f0_reference: np.ndarray,
    *,
    default: tuple[float, float] = (80.0, 800.0),
) -> tuple[float, float]:
    """플롯 Y축 — 0Hz 미포함 (librosa midi 변환 NaN 방지)."""
    chunks: list[np.ndarray] = []
    for arr in (f0, f0_reference):
        ok = np.isfinite(arr) & (arr > 0)
        if np.any(ok):
            chunks.append(arr[ok].astype(float))
    if not chunks:
        return default
    vals = np.concatenate(chunks)
    lo = float(np.min(vals))
    hi = float(np.max(vals))
    if not np.isfinite(lo) or not np.isfinite(hi):
        return default
    if hi <= lo:
        hi = lo + 50.0
    pad = max(20.0, (hi - lo) * 0.08)
    lo = max(50.0, lo - pad)
    hi = min(2500.0, hi + pad)
    if lo >= hi:
        return default
    return lo, hi


def plot_pitch(
    times: np.ndarray,
    f0: np.ndarray,
    f0_reference: np.ndarray,
    stable_regions: list[tuple[float, float]],
    deviation_segments: list[PitchDeviationSegment],
    *,
    title: str,
    save_path: Path | None = None,
    dpi: int = 150,
) -> None:
    voiced = np.isfinite(f0)
    fig, ax = plt.subplots(figsize=(13, 5.5))

    for start, end in stable_regions:
        ax.axvspan(start, end, alpha=0.35, color="#3b82f6", zorder=0)
    for seg in deviation_segments:
        ax.axvspan(seg.start_sec, seg.end_sec, alpha=0.45, color="#ef4444", zorder=1)

    ref_ok = np.isfinite(f0_reference) & (f0_reference > 0)
    if np.any(ref_ok):
        ax.plot(
            times[ref_ok],
            f0_reference[ref_ok],
            color="#16a34a",
            linewidth=1.0,
            linestyle="--",
            alpha=0.85,
            zorder=2,
            label="기준 멜로디 (Reference)",
        )

    ax.plot(
        times[voiced],
        f0[voiced],
        color="#1e3a8a",
        linewidth=1.4,
        zorder=3,
        label="학생 F0",
    )

    hz_lo, hz_hi = _pitch_hz_ylim(f0, f0_reference)
    ax.set_ylim(hz_lo, hz_hi)
    if len(times) > 0 and np.isfinite(times).any():
        t_valid = times[np.isfinite(times)]
        ax.set_xlim(float(np.min(t_valid)), float(np.max(t_valid)))

    ax2 = ax.twinx()
    midi_bounds = librosa.hz_to_midi(np.array([hz_lo, hz_hi], dtype=float))
    if np.all(np.isfinite(midi_bounds)):
        ax2.set_ylim(float(np.min(midi_bounds)), float(np.max(midi_bounds)))
    else:
        ax2.set_ylim(36.0, 84.0)
    ax2.set_yticks(np.arange(36, 96, 4))
    ax2.set_yticklabels(
        [librosa.midi_to_note(n, unicode=False) for n in np.arange(36, 96, 4)]
    )
    ax2.set_ylabel("음이름")

    ax.set_xlabel("시간 (초)")
    ax.set_ylabel("주파수 (Hz)")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)

    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor="#3b82f6", alpha=0.45, label="음정 OK"),
        Patch(facecolor="#ef4444", alpha=0.45, label="음정 틀림"),
    ]
    if np.any(ref_ok):
        handles.append(
            plt.Line2D([0], [0], color="#16a34a", linestyle="--", label="기준 멜로디")
        )
    handles.append(
        plt.Line2D([0], [0], color="#1e3a8a", linewidth=1.4, label="학생 F0")
    )
    ax.legend(handles=handles, loc="upper right")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi)
        print(f"\n[안내] 그래프 저장: {save_path}")
    if plt.get_backend().lower() != "agg":
        plt.show()
    else:
        plt.close(fig)


def main() -> int:
    _configure_console_encoding()
    from gpt_coach import generate_gpt_coaching, load_dotenv_if_present

    load_dotenv_if_present(PROJECT_DIR)

    parser = argparse.ArgumentParser(
        description="보컬 학원 4단계 + DTW 비교 + GPT 코칭"
    )
    parser.add_argument(
        "audio",
        nargs="?",
        type=Path,
        default=None,
        help="사용자 녹음 (예: sample.mp3)",
    )
    parser.add_argument(
        "--song",
        type=str,
        default=None,
        help="노래 제목 (유튜브에서 MR/가이드 멜로디 검색)",
    )
    parser.add_argument(
        "--fetch-reference",
        action="store_true",
        help="--song과 함께 사용: yt-dlp로 레퍼런스 다운로드",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="로컬 기준 멜로디 MIDI",
    )
    parser.add_argument(
        "--guide",
        type=Path,
        default=None,
        help="로컬 가이드 멜로디 WAV/MP3 (DTW 비교)",
    )
    parser.add_argument(
        "--gpt",
        action="store_true",
        help="OpenAI API로 따뜻한 코칭 멘트 생성",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="유튜브 다운로드 캐시 유지 (기본: 분석 후 삭제)",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=PROJECT_DIR / "pitch_result.png",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="분석 JSON 저장 경로",
    )
    parser.add_argument(
        "--save-record",
        action="store_true",
        help="records/ 폴더에 날짜별 JSON 자동 저장",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="이전 record JSON과 점수 비교 출력",
    )
    parser.add_argument(
        "--export-clips",
        action="store_true",
        help="문제 구간 WAV 클립을 clips/ 폴더에 저장",
    )
    parser.add_argument(
        "--growth-chart",
        action="store_true",
        help="records 기반 성장 곡선 PNG (charts/growth_chart.png)",
    )
    args = parser.parse_args()
    args.audio = resolve_audio(args.audio)

    if not args.audio.exists():
        print(f"오류: 파일 없음 - {args.audio}", file=sys.stderr)
        return 1

    use_yt = bool(args.song and (args.fetch_reference or args.song))
    if args.song and not args.fetch_reference and not args.guide:
        print("[안내] --song만 입력됨 → --fetch-reference로 유튜브 검색을 켭니다.")
        use_yt = True

    print(f"[안내] 분석 시작: {args.audio.name}")
    if args.song:
        print(f"[안내] 곡명: {args.song}")

    try:
        session = run_full_session(
            args.audio,
            song_title=args.song,
            use_youtube=use_yt and bool(args.song),
            reference_path=args.reference,
            guide_path=args.guide,
            use_gpt=args.gpt,
            save_record=args.save_record,
            compare=args.compare,
            export_clips=args.export_clips,
            growth_chart=args.growth_chart,
            save_plot=args.save,
            json_out=args.json_out,
            keep_cache=args.keep_cache,
        )
    except RuntimeError as exc:
        print(f"[오류] {exc}", file=sys.stderr)
        return 1

    report = session["report"]
    print_report(report)

    if args.json_out:
        print(f"\n[안내] 분석 JSON 저장: {args.json_out}")
    if session.get("record_path"):
        print(f"\n[안내] 성장 기록 저장: {session['record_path']}")
    if session.get("compare_text"):
        print(session["compare_text"])
    if session.get("clips_info"):
        print(f"\n{session['clips_info']}")
    if session.get("chart_path"):
        print(f"\n[안내] 성장 그래프: {session['chart_path']}")
    if session.get("gpt_text"):
        print("\n" + "=" * 50)
        print("GPT 보컬 코치 멘트")
        print("=" * 50)
        print(session["gpt_text"])
    elif args.gpt and session.get("gpt_error"):
        print(f"[GPT 오류] {session['gpt_error']}", file=sys.stderr)
        return 1

    print(f"\n[안내] 그래프 저장: {session['plot_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
