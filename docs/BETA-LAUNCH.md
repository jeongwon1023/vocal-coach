# 베타 런칭 체크리스트

## ✅ 완료 (코드)

- [x] 웹 UI · 로그인(체험/Google/Kakao) · 분석 · DM 코치
- [x] 마이 페이지 · 기록 저장
- [x] 베타 배너 · 이용 안내
- [x] UI smoke test (`tests/test_ui_smoke.py`)

## Security before push

- [ ] `.env` is in `.gitignore` (already set)
- [ ] Run `.\deploy.ps1` — confirms `.env` is NOT tracked by git
- [ ] API keys only in Streamlit Cloud **Secrets**, never in code
- [ ] OAuth keys (Google/Kakao) in Secrets or `.env` locally only
- [ ] Do not commit `records/`, user uploads, or analysis JSON with personal data

## Copyright / legal (beta)

- **Your code**: you own it; dependencies (Streamlit, librosa, etc.) are open-source — keep their licenses in mind.
- **User uploads**: users should upload **their own vocal recordings**. Add beta notice that they must have rights to the audio.
- **YouTube guide** (optional feature): downloading MR/guides via yt-dlp may conflict with platform ToS and copyright in some regions — disclose in beta, use at user's choice.
- **sample.mp3**: if included in repo, use only royalty-free or your own recording.
- **Privacy**: add a short notice (already in app beta footer) that recordings are processed for analysis only.

## 🔲 배포 전 (당신이 할 일)

1. **`.\deploy.ps1`** 실행 (PowerShell 권장) 또는 `.\deploy.bat`
2. **본인 녹음 1회** — 상세 리포트 · 그래프 · 점수 카드 확인
3. **GitHub push** — `.env`는 제외됨 (`.gitignore`)
4. **Streamlit Cloud** — [share.streamlit.io](https://share.streamlit.io)
   - Main file: `app.py`
   - `packages.txt` — ffmpeg (오디오 분석)
   - Secrets: `OPENAI_API_KEY`, OAuth 키(선택)
5. **OAuth 리디렉션 URL** — 배포 URL에 맞게 Google/Kakao 콘솔 수정
6. **친구 3~5명** — 링크 공유 + 피드백

## 🔲 배포 후 (1~2주)

- [ ] Supabase 연동 (`docs/supabase-setup.md`)
- [ ] 이용약관·개인정보처리방침 페이지 (법무 검토)
- [ ] 에러 모니터링 (Sentry 등)
- [ ] Streamlit Cloud sleep 대응 — cold start 안내 문구

## 명령어

```powershell
cd "C:\Users\chahy\OneDrive\바탕 화면\vocal-coach"
.\venv\Scripts\python.exe tests\test_ui_smoke.py
.\run_web.bat
```
