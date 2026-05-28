# Vocal Coach — 보완 백로그

> 2026-05 전체 순차 진행 반영

---

## ✅ 완료

- [x] Plotly 인터랙티브 히트맵 (클릭 선택)
- [x] 인기곡 picker 페이지네이션
- [x] 베타 초대 카드 + 공유 URL
- [x] `docs/로드맵.md` 갱신
- [x] 분석 ETA (MR · 유튜브 보정)
- [x] Supabase 미러 강화 + 클라우드 카운트
- [x] MIDI 업로드 UI
- [x] Demucs/CREPE 문서 (`docs/PRECISION-LOCAL.md`)
- [x] WebView + PWA (`webview/`, `docs/WEBVIEW.md`)
- [x] API Docker (`Dockerfile.api`, `docs/API-DEPLOY.md`)
- [x] 월간 분석 한도 (`usage_limits.py`, 기본 30회)
- [x] 푸시/CNN 로드맵 문서

---

## ⬜ 수동 / 외부

| 항목 | 담당 |
|------|------|
| 베타 사용자 3~5명 피드백 | 사용자 |
| Supabase 프로젝트 Secrets 등록 | 사용자 |
| Railway/Render API 배포 | 사용자 |
| 앱스토어 WebView/Capacitor 빌드 | 사용자 |

---

## 🔜 코드 후속 (선택)

1. Plotly 히트맵 → 드릴 패널 오디오 자동 재생
2. Supabase Auth 네이티브 연동 (RLS)
3. Expo `mobile/` API URL 환경변수
4. 구독 tier (Stripe) + `VC_MONTHLY_ANALYSIS_LIMIT` tier별

---

## 환경 변수

| 변수 | 기본 | 설명 |
|------|------|------|
| `VC_MONTHLY_ANALYSIS_LIMIT` | 30 | 월 분석 한도 (0=무제한) |
| `SUPABASE_URL` / `SUPABASE_KEY` | — | 클라우드 미러 |
| `USE_CREPE` / `VOCAL_SEP` | — | 로컬 정밀 |

---

## 제약

- Streamlit Cloud: pYIN + HPSS, plotly OK, demucs NO
- 노트 클립: `audio_path` 필요 (캐시 복원 시 제한)
