"""
GPT 코칭 멘트 생성 모듈 — 분석 JSON → OpenAI API.

환경 변수:
    OPENAI_API_KEY=sk-...
    OPENAI_MODEL=gpt-4o-mini  (선택, 기본 gpt-4o-mini)
"""

from __future__ import annotations

import json
import os
from typing import Any

COACH_SYSTEM_PROMPT = (
    "당신은 10년 차 한국 보컬 학원 선생님입니다. "
    "유튜브·학원에서 학생에게 말하듯 따뜻하고 구체적으로 코칭하세요.\n"
    "JSON 데이터만 보고 코칭하세요. 추측 금지.\n\n"
    "선생님 말투 규칙:\n"
    "- 반드시 **잘한 점을 먼저** 2~3가지 (teacher.strengths, stage_scores 높은 항목 인용)\n"
    "- '~해요', '~해보세요' 존댓말. 기계적·냉정한 말투 금지\n"
    "- 숫자는 '음정 74점', '박자 68점'처럼 학생이 이해하게\n"
    "- Cent, DTW, HPSS, LUFS 등 분석 용어 금지 → "
    "'음정이 반쯤 틀림', '박이 밀림', '호흡이 끊김', '목소리가 탁해짐'\n"
    "- 업계 실무 용어 OK: 롱톤, 메트로놈, 복식호흡, 호흡 지지, 루바토, "
    "0.5배속, 믹스보이스, 두성, 씨(S) 훈련, 구간 루프\n\n"
    "출력 순서:\n"
    "1. 🌟 오늘 잘한 점 (teacher.strengths + JSON 숫자)\n"
    "2. 🎯 가장 먼저 함께 잡을 1가지 (몇 초~몇 초, BPM, 반복 횟수)\n"
    "3. 📋 오늘 10~15분 연습 루틴 (①②③)\n"
    "4. 📅 1주 후 재녹음 체크리스트\n"
    "5. 마지막 한 줄 격려 (선생님이 응원하는 말)"
)


def build_analysis_json(
    *,
    song_title: str | None,
    user_file: str,
    report_summary: dict[str, Any],
    dtw_result: dict[str, Any] | None,
    reference_source: str,
) -> dict[str, Any]:
    """GPT에 전달할 분석 JSON (사용자 데이터만, 외부 가사 없음)."""
    payload: dict[str, Any] = {
        "song_title": song_title or "미지정",
        "user_recording": user_file,
        "reference_source": reference_source,
        "overall_score": report_summary.get("overall_score"),
        "stage_scores": report_summary.get("stage_scores", {}),
        "pitch": {
            "melody_match_ratio_percent": report_summary.get("melody_match_percent"),
            "deviation_segments": report_summary.get("pitch_deviations", []),
        },
        "breath_issues": report_summary.get("breath_issues", []),
        "timbre_issues": report_summary.get("timbre_issues", []),
    }
    if dtw_result:
        payload["dtw_alignment"] = dtw_result
    return payload


COACH_CHAT_SYSTEM_PROMPT = (
    "당신은 15년 차 한국 보컬 학원 원장 선생님입니다. "
    "유튜브 강의·보컬 pedagogy 논문·현장 레슨 경험을 바탕으로 "
    "차분하고 따뜻하게 코칭합니다.\n\n"
    "말투: '~해요', '~해보세요' 존댓말. 학생을 격려하되 구체적으로.\n"
    "분석 JSON·이전 대화를 근거로 답하세요. 추측·허위 금지.\n"
    "Cent, DTW, HPSS 등 기술 용어 대신 '음정', '박', '호흡', '목소리 톤'으로.\n"
    "실무 용어 OK: 롱톤, 메트로놈, 복식호흡, 믹스보이스, 0.5배속, 구간 루프.\n"
    "답변은 DM처럼 3~8문장, 너무 길면 나눠 말하세요."
)


def _openai_client(api_key: str | None = None):
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지 필요: pip install openai") from exc
    return OpenAI(api_key=key), key


def generate_gpt_coaching(
    analysis_json: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """
    OpenAI Chat Completions API로 코칭 멘트 생성.

    Raises
    ------
    RuntimeError
        API 키 없음 또는 API 호출 실패
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되지 않았습니다.\n"
            "  PowerShell: $env:OPENAI_API_KEY='your-key'\n"
            "  또는 .env 파일 사용"
        )

    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지 필요: pip install openai") from exc

    client = OpenAI(api_key=key)
    user_content = (
        "아래 데이터[JSON]를 보고 코칭해 주세요.\n\n"
        f"```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=1200,
    )
    return response.choices[0].message.content or ""


def generate_coach_opening(
    analysis_json: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """분석 직후 DM 첫 메시지."""
    client, key = _openai_client(api_key)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    user_content = (
        "학생이 방금 녹음 분석을 마쳤어요. 인스타 DM처럼 첫 메시지를 보내세요.\n"
        "순서: ①인사 ②잘한 점 2가지 ③가장 먼저 손볼 1가지 ④오늘 10분 루틴 한 줄 ⑤격려.\n\n"
        f"```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": COACH_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.75,
        max_tokens=900,
    )
    return response.choices[0].message.content or ""


def generate_suggested_questions_gpt(
    analysis_json: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> list[str]:
    """궁금해할 만한 질문 3개."""
    client, _ = _openai_client(api_key)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "보컬 코치. JSON 분석 결과를 보고 학생이 DM으로 물어볼 법한 "
                "짧은 질문 3개만 JSON 배열로 출력. 예: [\"질문1\", \"질문2\", \"질문3\"]",
            },
            {
                "role": "user",
                "content": json.dumps(analysis_json, ensure_ascii=False),
            },
        ],
        temperature=0.6,
        max_tokens=300,
    )
    raw = response.choices[0].message.content or "[]"
    try:
        start, end = raw.find("["), raw.rfind("]") + 1
        items = json.loads(raw[start:end]) if start >= 0 else []
        return [str(x) for x in items[:3]]
    except json.JSONDecodeError:
        return []


def generate_coach_chat_reply(
    analysis_json: dict[str, Any],
    chat_history: list[dict[str, str]],
    user_message: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """DM 후속 대화."""
    client, _ = _openai_client(api_key)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    context = (
        f"[분석 데이터]\n```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": COACH_CHAT_SYSTEM_PROMPT + "\n\n" + context},
    ]
    for turn in chat_history[-12:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.72,
        max_tokens=700,
    )
    return response.choices[0].message.content or ""


def load_dotenv_if_present(project_dir) -> None:
    """.env 파일이 있으면 KEY 로드 (선택). Streamlit Cloud secrets도 지원."""
    env_path = project_dir / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

    try:
        import streamlit as st

        for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "SUPABASE_URL", "SUPABASE_KEY"):
            if key in st.secrets and key not in os.environ:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass
