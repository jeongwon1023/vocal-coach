# Vocal Coach AI 🎤

**녹음 한 번으로 음정·박자·호흡을 분석하고, AI 보컬 코치가 맞춤 연습법을 알려드려요.**  
레슨비 0원 · 1분 안에 결과 · [체험 계정](https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/)으로 바로 시작.

> 🎵 혼자 연습할 때 「나 잘 부르는 것 같은데…」가 답답하다면, 지금 녹음만 올려보세요.

## 빠른 시작

```powershell
cd "C:\Users\chahy\OneDrive\바탕 화면\vocal-coach"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

| 실행 | 설명 |
|------|------|
| **`run_web.bat`** | 웹 MVP — 분석 대시보드 + 마이 페이지 |
| **`run_api.bat`** | 모바일 연동 REST API (포트 8000) |
| **`run_analysis.bat`** | CLI — sample.mp3 분석 + 그래프 |
| **`run_record.bat`** | CLI — 기록 + 클립 + 성장그래프 |
| **`run_gpt.bat`** | CLI — GPT 코칭 포함 |
| **`run_check.bat`** | 환경 점검 |

> **`vocal-coach` 폴더**에서 실행하세요. `.\run_web.bat` 처럼 `.\` 를 붙이세요.

## 웹 MVP (1단계 — 지금)

| 탭 | 기능 |
|----|------|
| **분석 대시보드** | MP3 업로드 → 4단계 분석 → 레이더 차트 · GPT · 클립 |
| **마이 페이지** | 날짜별 JSON 이력 · 성장 곡선 · 기록 비교 |

```powershell
.\run_web.bat
```

## 모바일 (3단계 준비)

- `mobile/` — Expo + React Native 골격 (녹음 → API 전송 → 마이 페이지)
- `api_server.py` — FastAPI (`POST /analyze`, `GET /records`)

```powershell
.\run_api.bat          # PC에서 API 서버
cd mobile && npm install && npx expo start
```

## 로드맵 · 배포

| 문서 | 내용 |
|------|------|
| [docs/BETA-LAUNCH.md](docs/BETA-LAUNCH.md) | **베타 런칭 체크리스트** · 배포 · 피드백 |
| [docs/다음-스텝.md](docs/다음-스텝.md) | **지금 할 일** · 배포 · Supabase |
| [docs/로드맵.md](docs/로드맵.md) | 4단계 실행 계획 |
| [docs/배포-비용-가이드.md](docs/배포-비용-가이드.md) | Streamlit Cloud · API · 비용 |
| [docs/기능과-사용법.md](docs/기능과-사용법.md) | CLI · 웹 · 연습 루틴 |
| [docs/폴더-구조.md](docs/폴더-구조.md) | 파일·폴더 설명 |

## 이 프로젝트로 할 수 있는 것

- **Stage 1~4 분석** · **GPT 코칭** · **성장 기록/그래프** · **구간 클립** · **MR 감지**
- **웹 대시보드** (Streamlit) · **모바일 API** (FastAPI) · **Expo 앱 골격**

## 다음 스텝 (웹 열린 후)

1. **오늘** — 본인 녹음 MP3 업로드 → 분석 → 마이 페이지 확인
2. **이번 주** — Git 설치 → GitHub → [Streamlit Cloud](https://share.streamlit.io) 배포
3. **1~2개월** — Supabase 로그인 + 클라우드 기록

상세: [docs/다음-스텝.md](docs/다음-스텝.md) · Git 점검: `setup_git.bat`

## 환경

- Python 3.10+ · `.env`에 `OPENAI_API_KEY` (GPT 선택)
- Node.js 18+ (모바일 개발 시)
