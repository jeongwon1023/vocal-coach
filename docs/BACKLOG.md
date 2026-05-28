# Vocal Coach — 보완 백로그

에이전트·개발 중 수집한 개선 항목. 완료 시 `[x]` 표시.

---

## 완료 (최근)

- [x] 곡 DB JSON 외부화 + mtime 자동 갱신
- [x] 곡 DB 110곡 + 검색·장르 필터
- [x] 히트맵 번호 버튼 → 구간 재생 (드릴다운)
- [x] MR 감지 캐시 — 파일 변경 시 무효화
- [x] 주간 요약 (마이 + 결과 인라인)
- [x] PDF 리포트 · 연습 히스토리 자동 갱신

---

## P1 — 단기 (리스크 낮음)

| # | 항목 | 메모 |
|---|------|------|
| 1 | 히트맵 이미지 좌표 클릭 | Streamlit 한계 → plotly 또는 커스텀 컴포넌트 검토 |
| 2 | 인기곡 picker 페이지네이션 | 48곡 초과 시 더보기 |
| 3 | 베타 사용자 피드백 3~5명 | 수동 — 링크 공유 |
| 4 | `docs/로드맵.md` 갱신 | 배포·기능 반영 |
| 5 | 분석 ETA 정밀 모드 보정 | MR+유튜브 시 시간 늘림 |

---

## P2 — 중기 (인프라·정확도)

| # | 항목 | 메모 |
|---|------|------|
| 6 | Supabase 프로덕션 연동 | `db_store.py` · schema 이미 있음 |
| 7 | Demucs 로컬 옵션 문서화 | `VOCAL_SEP=demucs` |
| 8 | MIDI 원곡 레퍼런스 | 저작권·데이터 확보 필요 |
| 9 | WebView 앱 | Streamlit URL 래핑 |
| 10 | API 서버 배포 | `api_server.py` → Railway/Render |

---

## P3 — 장기

- 구독/월 N회 분석 한도
- 푸시 알림 (연습 리마인더)
- CNN 등 고급 음색 분석

---

## 알려진 제약

- **Streamlit Cloud**: CREPE/Demucs 미설치 → pYIN + HPSS
- **유튜브 가이드**: yt-dlp·네트워크 의존, 실패 시 HPSS 폴백
- **노트 클립**: 정밀 분석 + `audio_path` 필요 (캐시 복원 시 제한)

---

## 곡 DB 추가

`data/song_hints.json` 편집 또는 `scripts/expand_song_db.py` 참고.  
앱 재시작 없이 mtime 감지로 자동 반영.
