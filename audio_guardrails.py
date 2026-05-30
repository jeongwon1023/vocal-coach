"""업로드 오디오 사전 검증 — 음성 구간 (서버/API 비용 방어)."""

from __future__ import annotations

from pathlib import Path

# 분석에 실제 사용하는 최대 구간 (초과분은 자동 컷, 에러 아님)
ANALYZE_MAX_DURATION_SEC = 150.0
MIN_VOICE_RATIO = 0.05
SPLIT_TOP_DB = 30
ANALYSIS_SR = 16000


class AudioGuardrailError(Exception):
    """유저에게 그대로 보여줄 수 있는 검증 실패."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_audio_file(audio_path: Path) -> None:
    """
    분석 전 오디오 검증. 실패 시 AudioGuardrailError.

    - 길이 제한 없음 (150초 초과는 analysis.load_audio에서 자동 컷)
    - librosa.effects.split 기준 유효 음성 구간이 5% 미만이면 차단
    """
    import librosa

    path = Path(audio_path)
    if not path.exists():
        raise AudioGuardrailError("⚠️ 오디오 파일을 찾을 수 없습니다. 다시 녹음해 주세요.")

    try:
        duration = float(librosa.get_duration(path=str(path)))
    except Exception as exc:
        raise AudioGuardrailError(
            "⚠️ 오디오 파일을 읽을 수 없습니다. MP3·WAV 형식인지 확인해 주세요."
        ) from exc

    if duration < 1.0:
        raise AudioGuardrailError(
            "⚠️ 녹음이 너무 짧아요. 최소 3초 이상 부른 뒤 다시 시도해 주세요."
        )

    load_dur = ANALYZE_MAX_DURATION_SEC if duration > ANALYZE_MAX_DURATION_SEC else None
    try:
        y, sr = librosa.load(str(path), sr=ANALYSIS_SR, mono=True, duration=load_dur)
    except Exception as exc:
        raise AudioGuardrailError(
            "⚠️ 오디오를 불러오지 못했습니다. 다른 파일로 다시 시도해 주세요."
        ) from exc

    if y.size == 0:
        raise AudioGuardrailError(
            "⚠️ 목소리가 감지되지 않았거나 주변 소음이 너무 큽니다. "
            "조용한 곳에서 다시 녹음해 주세요."
        )

    intervals = librosa.effects.split(y, top_db=SPLIT_TOP_DB)
    total_sec = len(y) / float(sr)
    voice_sec = sum((end - start) / float(sr) for start, end in intervals)

    if len(intervals) == 0 or voice_sec <= 0:
        raise AudioGuardrailError(
            "⚠️ 목소리가 감지되지 않았거나 주변 소음이 너무 큽니다. "
            "조용한 곳에서 다시 녹음해 주세요."
        )

    ratio = voice_sec / total_sec if total_sec > 0 else 0.0
    if ratio < MIN_VOICE_RATIO:
        raise AudioGuardrailError(
            "⚠️ 목소리가 감지되지 않았거나 주변 소음이 너무 큽니다. "
            "조용한 곳에서 다시 녹음해 주세요."
        )
