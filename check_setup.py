"""
환경 점검 스크립트 — pip install 후 실행:
    python check_setup.py
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=== vocal-coach 환경 점검 ===\n")
    errors = 0
    warnings = 0

    packages = [
        "librosa",
        "numpy",
        "matplotlib",
        "scipy",
        "soundfile",
        "audioread",
        "pretty_midi",
        "yt_dlp",
        "openai",
        "streamlit",
    ]
    print("1. Python 패키지")
    for pkg in packages:
        try:
            __import__(pkg)
            ok(pkg)
        except ImportError:
            fail(f"{pkg} — pip install -r requirements.txt")
            errors += 1

    print("\n2. 프로젝트 모듈")
    for mod in (
        "analysis",
        "action_plan",
        "coaching_vocab",
        "vocal_research",
        "progress_tracker",
        "progress_chart",
        "clip_exporter",
        "mr_detect",
        "reference_fetcher",
        "dtw_compare",
        "gpt_coach",
    ):
        try:
            __import__(mod)
            ok(mod)
        except Exception as exc:
            fail(f"{mod}: {exc}")
            errors += 1

    if (PROJECT_DIR / "app.py").exists():
        ok("app.py (Streamlit 웹 UI)")
    else:
        fail("app.py 없음")
        errors += 1

    print("\n3. yt-dlp 실행 파일")
    if shutil.which("yt-dlp"):
        ok("yt-dlp 명령어 PATH 등록됨")
    else:
        ok("yt-dlp (python -m yt_dlp 로 동작)")

    print("\n4. 샘플 오디오")
    for name in ("sample.mp3", "sample.wav", "test_voice.wav"):
        p = PROJECT_DIR / name
        if p.exists():
            ok(f"{name} ({p.stat().st_size // 1024} KB)")

    print("\n5. OpenAI API 키 (.env)")
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        fail(".env 없음 — .env.example 을 복사해 OPENAI_API_KEY 입력")
        errors += 1
    else:
        key = ""
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
        if key and key.startswith("sk-") and len(key) > 20:
            ok("OPENAI_API_KEY 설정됨 (GPT --gpt 사용 가능)")
        else:
            print(
                "  [주의] OPENAI_API_KEY 비어 있음 - "
                "https://platform.openai.com/api-keys 발급 후 .env 에 입력"
            )
            print("         (키 없어도 음정/박자/호흡 분석은 가능)")
            warnings += 1

    print("\n" + ("=== 준비 완료 ===" if errors == 0 else f"=== 오류 {errors}개 ==="))
    if warnings:
        print(f"(참고: 주의 {warnings}개 - API 키만 추가하면 GPT 코칭 가능)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
