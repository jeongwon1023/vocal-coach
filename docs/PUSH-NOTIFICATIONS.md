# 푸시 알림 (Expo · 장기)

## 목표

- 연습 리마인더 (매일/매주)
- 분석 완료 알림 (백그라운드 job)

## 구현 경로

1. `mobile/` Expo + `expo-notifications`
2. API 서버에 device token 저장 (Supabase `push_tokens` 테이블)
3. Cron (GitHub Actions / Railway) → 미연습 사용자 리마인드

## 베타

현재 Streamlit WebView/PWA만 지원 — 푸시는 **Expo 앱 + API 배포** 이후.

## 참고

- [Expo Notifications](https://docs.expo.dev/push-notifications/overview/)
- `mobile/README.md`
