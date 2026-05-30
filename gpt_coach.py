"""
GPT 코칭 멘트 생성 모듈 — 분석 JSON → OpenAI API.

환경 변수:
    OPENAI_API_KEY=sk-...
    OPENAI_MODEL=gpt-4o-mini  (선택, 기본 gpt-4o-mini)
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any

COACH_SYSTEM_PROMPT = (
    "당신은 10년 차 한국 보컬 학원 선생님입니다. "
    "유튜브·학원에서 학생에게 말하듯 따뜻하고 구체적으로 코칭하세요.\n"
    "JSON 데이터만 보고 코칭하세요. 추측 금지.\n\n"
    "선생님 말투 규칙:\n"
    "- 반드시 **잘한 점을 먼저** 2~3가지 (teacher.strengths, stage_scores 높은 항목 인용)\n"
    "- 약점 지적 전 **강점 칭찬 → 약점 → 해결책** 샌드위치 피드백 구조 필수\n"
    "- '~해요', '~해보세요' 존댓말. 기계적·냉정한 말투 금지\n"
    "- 숫자는 '음정 74점', '박자 68점'처럼 학생이 이해하게\n"
    "- Cent, DTW, HPSS, LUFS, Superflux, onset, CV 지수 등 분석·논문 용어 금지 → "
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


COACH_CHAT_FOCUS_SYSTEM_PROMPT = (
    "당신은 한국 보컬 학원 선생님입니다. "
    "제공된 [약점 JSON]의 **단 하나의 약점**만 분석하세요.\n"
    "JSON에 없는 내용은 추측·환각 금지. "
    "Cent, DTW, HPSS, Superflux, CV 지수, 논문명 등 기술 용어 금지 → '음정', '박', '호흡', '목소리'로.\n"
    "반드시 **학생이 지금 당장 따라 할 수 있는 물리적 훈련법 1개**만 구체적으로 제시하세요 "
    "(예: 롱톤 5초×5회, 메트로놈 60BPM, 'ng' 허밍, 0.5배속 구간 루프).\n"
    "'~해요', '~해보세요' 존댓말. 답변 5~8문장."
)


COACH_CHAT_SYSTEM_PROMPT = (
    "당신은 15년 차 한국 보컬 학원 원장 선생님입니다. "
    "유튜브 강의·보컬 pedagogy 논문·현장 레슨 경험을 바탕으로 "
    "카카오톡·인스타 DM처럼 **1:1로 대화**하듯 코칭합니다.\n\n"
    "말투: '~해요', '~해보세요' 존댓말. 학생 이름을 부르며 격려하되 구체적으로.\n"
    "피드백은 반드시 **칭찬 → 약점 → 연습법** 순서(샌드위치 피드백).\n"
    "한 줄 요약·끝맺음만 하는 답변 금지. 추상적 격려('조금씩 발전', '화이팅'만) 금지.\n"
    "분석 JSON·이전 대화를 근거로 답하세요. 추측·허위 금지.\n"
    "Cent, DTW, HPSS, Superflux, CV 지수, 논문명 등 기술 용어 대신 '음정', '박', '호흡', '목소리 톤'으로.\n"
    "실무 용어 OK: 롱톤, 메트로놈, 복식호흡, 믹스보이스, 0.5배속, 구간 루프.\n\n"
    "첫 DM은 **짧게 3~5문장**만: 인사 + 종합 점수 + 오늘 함께 잡을 1가지 + 아래 버튼/질문 유도.\n"
    "진단서·차트·3분할 카드는 이미 화면 위 탭에 있으므로 **첫 DM에서 긴 리포트·점수표·10분 루틴 반복 금지**.\n"
    "후속 답변(유저가 버튼·질문을 눌렀을 때)은 **5~10문장**. **굵게**로 핵심 강조.\n"
    "JSON 점수·초 구간·BPM·반복 횟수를 구체적으로 인용하세요. HTML 태그 금지.\n"
    "취소선(~~), 구분선(---) 사용 금지. 목록은 빈 줄 뒤 · 또는 번호로 작성.\n"
    "연습 단계는 ① ② ③ 처럼 각각 새 줄에 작성."
)

RAG_SYSTEM_SUFFIX = (
    "\n\n[강사 교재·레슨 자료]\n"
    "아래 교재 발췌를 **우선 참고**하되, 분석 JSON·대화와 모순되면 JSON을 따르세요.\n"
    "교재에 없는 내용은 지어내지 마세요."
)


def _with_rag(system_prompt: str, rag_block: str | None) -> str:
    block = (rag_block or "").strip()
    if not block:
        return system_prompt
    return system_prompt + RAG_SYSTEM_SUFFIX + "\n\n" + block

COACH_OPENING_USER_PROMPT = (
    "학생이 방금 녹음 분석을 마쳤어요. 카카오톡·인스타 DM **첫 메시지**를 작성하세요.\n\n"
    "위 탭에 진단서·차트가 이미 있으므로 **짧은 인사만** (최대 280자, 3~5문장):\n"
    "1) 🎤 이름 부르며 인사 + '분석을 마쳤어요' **1문장**\n"
    "2) 종합 점수 + 오늘 함께 잡을 **1가지 영역** **1~2문장** (JSON 점수 인용)\n"
    "3) 아래 버튼을 누르거나 질문하라는 유도 + 😊 **1문장**\n\n"
    "🌟 잘한 점·📋 10분 루틴·📊 영역별 점수표는 **첫 DM에 쓰지 마세요** — 유저가 질문할 때만 답하세요.\n"
    "선생님이 옆에 앉아 **한마디 건네는** 느낌으로 따뜻하게."
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
    rag_block: str | None = None,
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
            {"role": "system", "content": _with_rag(COACH_SYSTEM_PROMPT, rag_block)},
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
    rag_block: str | None = None,
) -> str:
    """분석 직후 DM 첫 메시지."""
    client, key = _openai_client(api_key)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    user_content = (
        COACH_OPENING_USER_PROMPT + "\n\n"
        f"```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": _with_rag(COACH_CHAT_SYSTEM_PROMPT, rag_block)},
            {"role": "user", "content": user_content},
        ],
        temperature=0.76,
        max_tokens=450,
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


def _build_coach_chat_messages(
    analysis_json: dict[str, Any],
    chat_history: list[dict[str, str]],
    user_message: str,
    *,
    rag_block: str | None = None,
    focus_mode: bool = False,
) -> list[dict[str, str]]:
    context = (
        f"[약점 JSON]\n```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )
    system_base = COACH_CHAT_FOCUS_SYSTEM_PROMPT if focus_mode else COACH_CHAT_SYSTEM_PROMPT
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": _with_rag(system_base, rag_block)
            + "\n\n"
            + context
            + (
                "\n\n지시: 제공된 약점 1가지만 분석하고 물리적 훈련법 1개를 제시하세요."
                if focus_mode
                else ""
            ),
        },
    ]
    for turn in chat_history[-12:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def _build_coach_opening_messages(
    analysis_json: dict[str, Any],
    *,
    rag_block: str | None = None,
    focus_mode: bool = False,
) -> list[dict[str, str]]:
    label = "약점 JSON" if focus_mode else "분석 JSON"
    user_content = (
        (COACH_OPENING_USER_PROMPT if not focus_mode else (
            "학생이 방금 녹음 분석을 마쳤어요. 아래 [약점 JSON]의 **가장 취약한 1가지**만 짚어 "
            "따뜻하게 인사한 뒤, **물리적 훈련법 1개**를 구체적으로 제시하는 DM 첫 메시지를 작성하세요. "
            "JSON에 없는 내용 추측 금지. **3~5문장**, 최대 280자."
        ))
        + "\n\n"
        f"```json\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n```"
    )
    system_base = COACH_CHAT_FOCUS_SYSTEM_PROMPT if focus_mode else COACH_CHAT_SYSTEM_PROMPT
    return [
        {"role": "system", "content": _with_rag(system_base, rag_block)},
        {"role": "user", "content": user_content.replace("[약점 JSON]", label)},
    ]


def _stream_chat_completion(
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = 0.74,
    max_tokens: int = 950,
) -> Iterator[str]:
    """OpenAI Chat Completions 스트리밍 — 토큰 단위 yield."""
    client, _ = _openai_client(api_key)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def stream_coach_chat_reply(
    analysis_json: dict[str, Any],
    chat_history: list[dict[str, str]],
    user_message: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    rag_block: str | None = None,
    focus_mode: bool = True,
) -> Iterator[str]:
    """DM 후속 대화 — 스트리밍."""
    messages = _build_coach_chat_messages(
        analysis_json,
        chat_history,
        user_message,
        rag_block=rag_block,
        focus_mode=focus_mode,
    )
    yield from _stream_chat_completion(
        messages, api_key=api_key, model=model, temperature=0.74, max_tokens=950
    )


def stream_coach_opening(
    analysis_json: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
    rag_block: str | None = None,
    focus_mode: bool = True,
) -> Iterator[str]:
    """분석 직후 DM 첫 메시지 — 스트리밍."""
    messages = _build_coach_opening_messages(
        analysis_json, rag_block=rag_block, focus_mode=focus_mode
    )
    yield from _stream_chat_completion(
        messages, api_key=api_key, model=model, temperature=0.76, max_tokens=450
    )


def generate_coach_chat_reply(
    analysis_json: dict[str, Any],
    chat_history: list[dict[str, str]],
    user_message: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    rag_block: str | None = None,
    focus_mode: bool = True,
) -> str:
    """DM 후속 대화 (일괄 — 테스트·폴백용)."""
    return "".join(
        stream_coach_chat_reply(
            analysis_json,
            chat_history,
            user_message,
            api_key=api_key,
            model=model,
            rag_block=rag_block,
            focus_mode=focus_mode,
        )
    )


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
