"""분석 예상·남은 시간."""

from __future__ import annotations

import time


def default_total_seconds(
    *,
    fast_mode: bool,
    use_gpt: bool = False,
    use_youtube: bool = False,
    mr_likely: bool = False
) -> int:
    base = 55 if fast_mode else 150
    if use_youtube:
        base += 50 if fast_mode else 70
    if mr_likely and not fast_mode:
        base += 25
    elif mr_likely and fast_mode:
        base += 10
    if use_gpt:
        base += 35
    return base


def format_eta(seconds: int) -> str:
    if seconds <= 0:
        return "거의 다 됐어요"
    if seconds < 60:
        return f"약 {seconds}초 남음"
    m, s = divmod(seconds, 60)
    if s == 0:
        return f"약 {m}분 남음"
    return f"약 {m}분 {s}초 남음"


def remaining_seconds(
    pct: float,
    *,
    fast_mode: bool,
    started_at: float | None,
    use_gpt: bool = False,
    use_youtube: bool = False,
    mr_likely: bool = False
) -> int:
    """pct: 0~1. 경과 시간 기반 남은 시간 추정."""
    total_default = default_total_seconds(
        fast_mode=fast_mode,
        use_gpt=use_gpt,
        use_youtube=use_youtube,
        mr_likely=mr_likely
    )
    pct = min(max(pct, 0.0), 1.0)

    if started_at is None:
        return int(total_default * (1.0 - pct))

    elapsed = max(0.0, time.time() - started_at)
    if pct >= 0.99:
        return 0
    if pct < 0.03:
        return total_default

    total_est = elapsed / pct
    remaining = int(total_est - elapsed)
    cap = total_default * 2.5
    return max(0, min(remaining, int(cap)))
