"""
코칭 매니저 — 우선순위별 실행 플랜 (유튜브·학원식 표현).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from coaching_vocab import STAGE_LABELS_SHORT, cent_to_words, rhythm_cv_to_words, time_range

if TYPE_CHECKING:
    from analysis import CurriculumReport

RHYTHM_CV_TARGET = 0.28
METRONOME_BPM = 70


@dataclass
class ActionItem:
    priority: int
    title: str
    prescription: str
    practice: str
    reason: str
    stage: int


def build_action_plan(report: "CurriculumReport") -> list[ActionItem]:
    stages = {s.stage: s for s in report.stages[:3]}
    s1 = stages.get(1)
    s2 = stages.get(2)
    s3 = stages.get(3)

    rhythm_cv = (s2.details.get("rhythm_cv") if s2 else None) or 0.69
    timbre_count = len(report.timbre_issue_segments)
    pitch_seg = report.pitch_deviation_segments[0] if report.pitch_deviation_segments else None

    items: list[ActionItem] = []
    s2_score = s2.score if s2 else 0

    items.append(
        ActionItem(
            priority=1,
            title="박자·리듬 — 메트로놈 2마디 끊어치기",
            prescription=f"메트로놈 {METRONOME_BPM}BPM · 손뼉과 가사 동시에.",
            practice=(
                "곡 전체 X → AI가 지목한 구간 **2마디만** 선택.\n"
                "  1세트: 손뼉 1번 + 첫 음절 (5회)\n"
                "  2세트: 손뼉 + 두 음절 (5회)\n"
                "  맞으면 BPM 75 → 80으로 올리기"
            ),
            reason=(
                f"{rhythm_cv_to_words(rhythm_cv)} (지수 {rhythm_cv:.2f}, 목표 {RHYTHM_CV_TARGET} 이하). "
                f"현재 박자 {s2_score:.0f}점 — 박만 잡아도 체감 점수가 크게 오릅니다."
            ),
            stage=2,
        )
    )

    s3_score = s3.score if s3 else 0
    timbre_example = ""
    if report.timbre_issue_segments:
        t0 = report.timbre_issue_segments[0]
        timbre_example = f" (예: {time_range(t0.start_sec, t0.end_sec)})"

    items.append(
        ActionItem(
            priority=2,
            title="호흡·음색 — 씨(S) 훈련 + 성대 닫힘",
            prescription="소리 '새는' 느낌 = 공기 반·소리 반 → 음색 탁해짐.",
            practice=(
                "① 복식호흡 후 '씨—' 10초 × 5세트 (마지막 3초 힘 유지)\n"
                "② 피아노 한 음 '아—' 롱톤 10분 (입술 살짝 모음)\n"
                f"③ 음색 흐려진 구간{timbre_example} 가사만 0.75배속 5번"
            ),
            reason=(
                f"음색 흐려진 구간 {timbre_count}곳{timbre_example}. "
                f"호흡·음색 {s3_score:.0f}점."
            ),
            stage=3,
        )
    )

    focus = ""
    if pitch_seg:
        focus = (
            f"오늘 루프: {time_range(pitch_seg.start_sec, pitch_seg.end_sec)} "
            f"({pitch_seg.note_hint}) — {cent_to_words(pitch_seg.max_deviation_cents)} · 10회"
        )
    else:
        focus = "오늘: 박자 틀린 2마디만 듣고 손뼉+가사 10회"

    items.append(
        ActionItem(
            priority=3,
            title="기록 비교 — 같은 곡 1주 후 재분석",
            prescription="웹에서 '성장 기록 저장' 켜고 분석 → 마이 페이지 확인.",
            practice=(
                f"{focus}\n"
                "  1주 후 같은 곡 다시 녹음 → 마이 페이지에서 점수 비교"
            ),
            reason=(
                "곡 전체 100번보다 AI가 찍어준 구간 10번이 훨씬 효과적입니다. "
                "숫자로 변화를 보면 동기부여도 됩니다."
            ),
            stage=0,
        )
    )

    return items


def format_action_plan(items: list[ActionItem]) -> str:
    lines = [
        "",
        "=" * 50,
        "오늘 이렇게 연습하세요 (우선순위 3가지)",
        "=" * 50,
    ]
    for item in items:
        lines.extend(
            [
                f"\n{item.priority}. {item.title}",
                f"   한 줄 요약: {item.prescription}",
                f"   구체적 연습:",
                *[f"   {ln}" for ln in item.practice.split("\n")],
                f"   왜 이걸 먼저? {item.reason}",
            ]
        )
    lines.extend(
        [
            "",
            "-" * 50,
            "코치 한마디",
            "-" * 50,
            "노래 전체를 무작정 반복하지 마세요.",
            "리포트에 나온 **초(秒) 구간**만 루프 연습하는 게 유튜브 레슨에서도 가장 많이 쓰는 방법입니다.",
            f"오늘: (1) 문제 구간 듣기 → (2) 메트로놈 {METRONOME_BPM} 2마디×5세트 → (3) 마이 페이지에 저장",
            "",
        ]
    )
    return "\n".join(lines)
