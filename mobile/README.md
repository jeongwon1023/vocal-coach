# 보컬 코치 모바일 (Expo MVP)

React Native + Expo 기반 모바일 앱 **골격**입니다.  
3단계 로드맵에서 본격 개발할 예정이며, 지금은 API 연동 구조만 준비되어 있습니다.

## 사전 요구

- Node.js 18+
- Expo Go 앱 (스마트폰)
- PC에서 `run_api.bat` 실행 (같은 Wi-Fi)

## 설치

```bash
cd mobile
npm install
npx expo start
```

## API 연결

`src/api/client.ts`의 `API_BASE_URL` 수정:

| 환경 | URL 예시 |
|------|----------|
| Android 에뮬레이터 | `http://10.0.2.2:8000` |
| 실제 기기 (같은 Wi-Fi) | `http://192.168.x.x:8000` (PC IP) |
| 배포 후 | `https://your-api.railway.app` |

## 화면 구성

| 탭 | 기능 |
|----|------|
| **분석** | 마이크 녹음 → POST /analyze → 점수 표시 |
| **마이** | GET /records → 날짜별 이력 |

## WebView 대안 (더 빠른 출시)

네이티브 개발 전에 Streamlit 웹을 WebView로 감싸면 앱스토어 출시 가능:

```tsx
import { WebView } from "react-native-webview";
// <WebView source={{ uri: "https://your-app.streamlit.app" }} />
```

자세한 내용: [docs/로드맵.md](../docs/로드맵.md)

## 에셋

`app.json`에서 icon/splash를 참조합니다.  
실제 빌드 전 `assets/` 폴더에 PNG를 추가하거나 `npx create-expo-app`으로 생성한 기본 에셋을 복사하세요.

```bash
mkdir assets
# placeholder — expo start 시 경고 나올 수 있음
```
