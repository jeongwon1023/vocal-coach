"""배포·런타임 환경 감지 및 공통 설정."""

from __future__ import annotations

import os
from pathlib import Path


def is_streamlit_cloud() -> bool:
    if os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud":
        return True
    cwd = str(Path.cwd()).replace("\\", "/")
    return "/mount/src" in cwd or "streamlit/app" in cwd


def default_use_queue() -> bool:
    """Streamlit Cloud 무료 tier — 동기 분석이 더 안정적."""
    return not is_streamlit_cloud()


def configure_matplotlib() -> None:
    """Linux(Cloud)에서 Malgun Gothic 없음 → 안전한 폰트 스택."""
    try:
        import matplotlib.pyplot as plt

        plt.rcParams["font.family"] = [
            "Malgun Gothic",
            "Apple SD Gothic Neo",
            "NanumGothic",
            "DejaVu Sans",
            "sans-serif",
        ]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass
