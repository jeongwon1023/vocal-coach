# 배포 실행 계획 (Vocal Coach AI — 베타)

> **목표:** GitHub `main` push → Streamlit Cloud 자동 재배포 → 베타 URL 공유  
> **저장소:** https://github.com/jeongwon1023/vocal-coach  
> **앱 진입점:** `app.py`

---

## Phase 0 — 사전 점검 (로컬, ~5분)

| # | 작업 | 명령 / 확인 | 완료 기준 |
|---|------|-------------|-----------|
| 0.1 | Smoke test | `.\venv\Scripts\python.exe tests\test_ui_smoke.py` | `All UI smoke tests passed` |
| 0.2 | `.env` 미추적 | `git ls-files .env` → 오류 | GitHub에 키 없음 |
| 0.3 | RAG 교재 포함 | `coach_knowledge/*.md` 4개+ | 커밋 대상 |
| 0.4 | 로컬 1회 분석 | `.\run_web.bat` → 업로드 → DM·리포트 | 화면 깨짐 없음 |

---

## Phase 1 — Git push (자동화, ~2분)

```powershell
cd "C:\Users\chahy\OneDrive\바탕 화면\vocal-coach"
& "C:\Program Files\Git\bin\git.exe" add .
& "C:\Program Files\Git\bin\git.exe" commit -m "feat: RAG coach, feedback calibration, DM UX polish"
& "C:\Program Files\Git\bin\git.exe" push origin main
```

**이번 배포에 포함되는 주요 변경**

- `coach_rag.py` + `coach_knowledge/` — 강사 교재 RAG
- `feedback_trainer.py` — 점수 피드백 보정 (Phase 1)
- DM 채팅 UX (fragment, 타이핑, 교재 근거 표시)
- 분석 UI (sticky 배너, 로딩 분리, 리포트 줄바꿈)

---

## Phase 2 — Streamlit Cloud (~10분)

### 2.1 앱 연결 (최초 1회만)

1. https://share.streamlit.io 로그인 (GitHub 연동)
2. **New app** → `jeongwon1023/vocal-coach` → Branch `main` → Main file **`app.py`**
3. **Advanced settings** → Python 3.10+ (기본값 OK)
4. `packages.txt` 자동 적용 → `ffmpeg`, `libsndfile1`

### 2.2 Secrets (필수 / 선택)

Settings → Secrets:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"

# RAG (기본 켜짐, 교재는 repo에 포함)
COACH_RAG_ENABLED = "1"
COACH_RAG_TOP_K = "4"

# OAuth (선택 — 없으면 체험 로그인만)
# GOOGLE_CLIENT_ID = "..."
# GOOGLE_CLIENT_SECRET = "..."
# KAKAO_REST_API_KEY = "..."
```

GPT 키 없어도 **분석·규칙 코칭**은 동작. DM GPT·RAG 임베딩은 키 있을 때 품질 ↑.

### 2.3 재배포

- `main` push 시 **자동 Reboot app**
- 수동: Cloud 대시보드 → **Reboot app**
- 배포 URL 예: `https://vocal-coach-xxxx.streamlit.app`

### 2.4 배포 후 smoke (5분)

| 체크 | 방법 |
|------|------|
| 홈 로드 | URL 접속, 베타 배너 |
| 분석 | 본인 MP3 1회 업로드 (1~3분) |
| DM | 「10분 루틴」질문 → 📚 교재 근거 표시 |
| 마이 | 기록 1건 표시 |
| 피드백 | 점수 동의/불일치 저장 |

---

## Phase 3 — OAuth (선택, 배포 URL 확정 후)

Google / Kakao 콘솔에 **배포 URL** 리디렉션 추가:

```
https://YOUR-APP.streamlit.app/   (웹)
http://localhost:8501/            (로컬)
```

OAuth는 `auth_server.py` 별도 호스팅 시 완전 연동. 베타는 **체험 로그인**으로도 충분.

---

## Phase 4 — 베타 런칭 (1~2주)

1. 친구 3~5명 URL 공유
2. **피드백** 탭 · 점수 동의/불일치 수집 (보정 5건↑)
3. `coach_knowledge/`에 학원 PDF→MD 추가 → Cloud 재배포
4. 이슈: cold start(첫 로드 30초+) — 베타 안내 문구 이미 있음

---

## Phase 5 — 다음 로드맵 (배포 후)

| 순서 | 항목 | 시기 |
|------|------|------|
| 1 | Supabase 기록 영구 저장 | 2~4주 |
| 2 | `ml_scorer` 정밀 모드 (Phase 2) | 3~6개월 |
| 3 | 이용약관·개인정보 페이지 | 베타→정식 전 |
| 4 | Sentry 에러 모니터링 | 트래픽↑ 시 |

---

## 문제 해결

| 증상 | 조치 |
|------|------|
| 분석 타임아웃 | 짧은 MP3(3분↓), fast mode |
| GPT 없음 | Secrets에 `OPENAI_API_KEY` |
| RAG 안 보임 | `coach_knowledge/` push 확인, 재부팅 |
| ffmpeg 오류 | `packages.txt` 확인 후 Reboot |
| Git push 실패 | GitHub 로그인 / PAT |

---

## 한 줄 타임라인

```
로컬 테스트 → git push → Streamlit 자동 배포 → Secrets 확인 → URL smoke → 베타 공유
```

**예상 소요:** 첫 배포 30분 · 이후 push마다 3~8분 재배포
