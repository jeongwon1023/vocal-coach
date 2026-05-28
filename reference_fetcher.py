"""
레퍼런스 확보 모듈 — 유튜브에서 MR·가이드 멜로디 일시 다운로드.

[저작권·운영 원칙]
- 분석 목적으로만 일시 다운로드하며, 재배포·상업 이용을 하지 않습니다.
- 사용자 본인 녹음(vocal)만 분석 데이터로 저장합니다.
- 캐시는 기본적으로 분석 종료 후 삭제합니다 (--keep-cache 시 유지).

[의존성] yt-dlp (pytube 미사용 — 유지보수·안정성 우선)
    pip install yt-dlp
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CACHE_ROOT = PROJECT_DIR / ".cache" / "references"


@dataclass
class ReferenceBundle:
    """검색·다운로드된 레퍼런스 파일 경로."""

    song_title: str
    mr_path: Path | None
    guide_path: Path | None
    cache_dir: Path

    @property
    def has_guide(self) -> bool:
        return self.guide_path is not None and self.guide_path.exists()


def _safe_dirname(title: str) -> str:
    slug = re.sub(r"[^\w\s가-힣]", "", title, flags=re.UNICODE).strip()
    slug = re.sub(r"\s+", "_", slug)[:60] or "song"
    digest = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{digest}"


def _yt_dlp_available() -> bool:
    return shutil.which("yt-dlp") is not None


def _run_yt_dlp(search_query: str, output_wav: Path) -> bool:
    """
    yt-dlp로 ytsearch1 검색 후 WAV 추출.
    [메모] 네트워크 필요. 실패 시 False 반환.
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    out_template = str(output_wav.with_suffix("")) + ".%(ext)s"

    cmd = [
        "yt-dlp",
        f"ytsearch1:{search_query}",
        "-x",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "-o",
        out_template,
        "--no-playlist",
        "--max-downloads",
        "1",
        "--quiet",
        "--no-warnings",
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"[레퍼런스] 다운로드 실패 ({search_query}): {exc}", file=sys.stderr)
        return False

    if output_wav.exists():
        return True
    # yt-dlp가 확장자를 다르게 둔 경우
    for p in output_wav.parent.glob(output_wav.stem + ".*"):
        if p.suffix.lower() in {".wav", ".m4a", ".webm", ".opus", ".mp3"}:
            if p != output_wav and p.suffix.lower() != ".wav":
                try:
                    import librosa
                    import soundfile as sf

                    y, sr = librosa.load(p, sr=22050, mono=True)
                    sf.write(output_wav, y, sr)
                    p.unlink(missing_ok=True)
                except Exception:
                    return p.exists()
            return True
    return False


def fetch_references(
    song_title: str,
    *,
    keep_cache: bool = False,
) -> ReferenceBundle:
    """
    곡 제목으로 MR(반주)·가이드 멜로디 WAV를 검색·다운로드.

    Parameters
    ----------
    song_title : 검색할 노래 제목
    keep_cache : True면 .cache 유지, False면 호출 측에서 cleanup_cache 사용
    """
    if not _yt_dlp_available():
        raise RuntimeError(
            "yt-dlp가 설치되어 있지 않습니다.\n"
            "  pip install yt-dlp\n"
            "  또는: https://github.com/yt-dlp/yt-dlp#installation"
        )

    cache_dir = CACHE_ROOT / _safe_dirname(song_title)
    cache_dir.mkdir(parents=True, exist_ok=True)

    mr_path = cache_dir / "reference_mr.wav"
    guide_path = cache_dir / "reference_guide.wav"

    print(f"[레퍼런스] 곡 검색: {song_title}")

    hint = None
    try:
        from song_hints import lookup_song_hint

        hint = lookup_song_hint(song_title)
    except Exception:
        pass

    if not mr_path.exists():
        q_mr = hint.youtube_query if hint else f"{song_title} instrumental MR"
        print(f"  MR 검색: {q_mr}")
        _run_yt_dlp(q_mr, mr_path)

    if not guide_path.exists():
        q_guide = (
            f"{hint.artist} {hint.title} vocal guide"
            if hint
            else f"{song_title} vocal guide"
        )
        print(f"  가이드 멜로디 검색: {q_guide}")
        ok = _run_yt_dlp(q_guide, guide_path)
        if not ok:
            q_alt = f"{song_title} guide vocal cover"
            print(f"  가이드 재검색: {q_alt}")
            _run_yt_dlp(q_alt, guide_path)

    mr_final = mr_path if mr_path.exists() else None
    guide_final = guide_path if guide_path.exists() else None

    try:
        from audio_normalize import normalize_reference_paths

        mr_final, guide_final = normalize_reference_paths(mr_final, guide_final)
    except Exception as exc:
        print(f"[레퍼런스] 오디오 정규화 건너뜀: {exc}", file=sys.stderr)

    if not guide_final:
        print(
            "[레퍼런스] 가이드 멜로디를 찾지 못했습니다. "
            "조화음 추출(HPSS) 기준으로 분석을 이어갑니다.",
            file=sys.stderr,
        )

    return ReferenceBundle(
        song_title=song_title,
        mr_path=mr_final,
        guide_path=guide_final,
        cache_dir=cache_dir,
    )


def cleanup_cache(bundle: ReferenceBundle | None) -> None:
    """분석 후 일시 파일 삭제 (저작권·디스크 관리)."""
    if bundle is None:
        return
    if bundle.cache_dir.exists():
        shutil.rmtree(bundle.cache_dir, ignore_errors=True)
        print(f"[레퍼런스] 캐시 삭제: {bundle.cache_dir.name}")
