"""
성장 기록 — JSON 저장·이전 기록과 비교.

records/record_YYYYMMDD_HHMMSS.json 형식으로 자동 저장합니다.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
RECORDS_DIR = PROJECT_DIR / "records"


def user_records_dir(user_id: str | None = None) -> Path:
    if user_id:
        d = PROJECT_DIR / "records" / "users" / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    return RECORDS_DIR


def default_record_path(user_id: str | None = None) -> Path:
    d = user_records_dir(user_id)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return d / f"record_{stamp}.json"


def build_full_record(payload: dict[str, Any], *, action_plan: list[dict] | None = None) -> dict[str, Any]:
    """분석 JSON + 메타데이터 + 액션 플랜."""
    record = {
        "recorded_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "version": 1,
        **payload,
    }
    if action_plan:
        record["priority_actions"] = action_plan
    return record


def save_record(
    data: dict[str, Any],
    path: Path | None = None,
    *,
    user_id: str | None = None,
) -> Path:
    try:
        from db_store import is_cloud_user, save_analysis_record

        if is_cloud_user(user_id):
            return save_analysis_record(data, user_id=user_id, path=path)
    except Exception:
        pass

    path = path or default_record_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if user_id:
        data = {**data, "user_id": user_id}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if user_id:
        try:
            from db_store import mirror_analysis_record

            mirror_analysis_record(data, user_id=user_id)
        except Exception:
            pass

    return path


def list_records(limit: int = 20, *, user_id: str | None = None) -> list[Path]:
    try:
        from db_store import is_cloud_user, list_analysis_records

        if is_cloud_user(user_id):
            cloud = list_analysis_records(limit=limit, user_id=user_id)
            if cloud:
                paths: list[Path] = []
                d = user_records_dir(user_id)
                for idx, record in enumerate(cloud):
                    local_path = record.get("_local_path")
                    if local_path and Path(local_path).exists():
                        paths.append(Path(local_path))
                        continue
                    ts = (record.get("recorded_at") or f"cloud_{idx}").replace(":", "").replace("-", "")
                    virtual = d / f"record_{ts[:15]}.json"
                    if not virtual.exists():
                        virtual.write_text(
                            json.dumps(record, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    paths.append(virtual)
                return paths
    except Exception:
        pass

    d = user_records_dir(user_id)
    if not d.exists():
        return []
    files = sorted(d.glob("record_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def load_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_previous_record(
    exclude: Path | None = None,
    *,
    user_id: str | None = None,
) -> Path | None:
    for p in list_records(limit=50, user_id=user_id):
        if exclude and p.resolve() == exclude.resolve():
            continue
        return p
    return None


def compare_records(current: dict[str, Any], previous: dict[str, Any]) -> str:
    """두 기록의 Stage 점수 차이 텍스트."""
    cur = current.get("stage_scores") or {}
    prev = previous.get("stage_scores") or {}
    cur_overall = current.get("overall_score")
    prev_overall = previous.get("overall_score")

    lines = [
        "",
        "=" * 50,
        "성장 비교 (이전 기록 vs 오늘)",
        "=" * 50,
        f"이전: {previous.get('recorded_at', '?')}",
        f"오늘: {current.get('recorded_at', '?')}",
        "",
    ]

    if cur_overall is not None and prev_overall is not None:
        diff = float(cur_overall) - float(prev_overall)
        sign = "+" if diff >= 0 else ""
        lines.append(f"종합 점수: {prev_overall} → {cur_overall} ({sign}{diff:.1f})")

    stage_names = {1: "음정", 2: "박자·리듬", 3: "호흡·음색"}
    for stage in (1, 2, 3):
        c = cur.get(stage) or cur.get(str(stage))
        p = prev.get(stage) or prev.get(str(stage))
        if c is None and p is None:
            continue
        c, p = float(c or 0), float(p or 0)
        diff = c - p
        sign = "+" if diff >= 0 else ""
        name = stage_names.get(stage, f"Stage{stage}")
        lines.append(f"  {name}: {p:.1f} → {c:.1f} ({sign}{diff:.1f})")

    lines.append("")
    if cur_overall is not None and prev_overall is not None:
        if float(cur_overall) > float(prev_overall):
            lines.append("잘하고 있어요! 점수가 올랐습니다. 같은 루틴으로 한 주 더 가보세요.")
        elif float(cur_overall) == float(prev_overall):
            lines.append("점수가 같습니다. 리포트의 '집중 구간' 연습량을 늘려 보세요.")
        else:
            lines.append("오늘은 컨디션이나 녹음 환경(MR 포함 등) 영향일 수 있어요. 목소리만 녹음해 비교해 보세요.")
    lines.append("")
    return "\n".join(lines)
