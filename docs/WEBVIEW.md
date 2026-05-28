# WebView 앱 (가장 빠른 앱화)

Streamlit 배포 URL을 네이티브 WebView로 감싸 앱스토어 출시 전 테스트합니다.

## URL

```
https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app/
```

## Android (Capacitor / Cordova)

1. `npx @capacitor/cli create vocal-coach-app`
2. `webview/` 의 `index.html` 을 시작 페이지로 설정하거나 InAppBrowser로 URL 로드
3. 마이크 권한: `AndroidManifest.xml` 에 `RECORD_AUDIO`

## iOS

- `WKWebView` + `NSMicrophoneUsageDescription`
- Safari WebRTC/마이크 정책 확인

## PWA (대안)

`webview/manifest.json` + 홈 화면 추가 — 스토어 없이 설치형 UX

## 포함 파일

- `webview/index.html` — 전체화면 iframe 래퍼
- `webview/manifest.json` — PWA 메타

## Expo 본격 앱

`mobile/` 폴더 — API 서버(`api_server.py`) 배포 후 `RecordScreen` 연동
