"""usage_limits · analysis_eta 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_analysis_eta_youtube() -> None:
    from ui.analysis_eta import default_total_seconds

    assert default_total_seconds(fast_mode=True) == 55
    assert default_total_seconds(fast_mode=True, use_youtube=True) == 105
    assert default_total_seconds(fast_mode=False, use_youtube=True) == 220
    assert default_total_seconds(fast_mode=False, use_youtube=True, mr_likely=True) == 245


def test_usage_limits_disabled() -> None:
    import os

    import usage_limits as ul

    old = os.environ.get("VC_MONTHLY_ANALYSIS_LIMIT")
    os.environ["VC_MONTHLY_ANALYSIS_LIMIT"] = "0"
    try:
        ul.DEFAULT_MONTHLY_LIMIT = 0
        allowed, _, _, _ = ul.check_analysis_allowed("test")
        assert allowed is True
    finally:
        if old is None:
            os.environ.pop("VC_MONTHLY_ANALYSIS_LIMIT", None)
        else:
            os.environ["VC_MONTHLY_ANALYSIS_LIMIT"] = old


if __name__ == "__main__":
    test_analysis_eta_youtube()
    test_usage_limits_disabled()
    print("limits/eta tests passed.")
