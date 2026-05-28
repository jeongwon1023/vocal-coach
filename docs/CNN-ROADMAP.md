# CNN / 고급 음색 분석 (장기)

## 현재

- librosa: jitter, HNR, MFCC, HPSS
- 정밀 모드: 노트 단위 F0, CREPE(로컬)

## 후보

| 방향 | 용도 |
|------|------|
| 학습된 보컬 분리 | MR 환경 SNR 개선 |
| 음색 embedding | 강사/원곡 유사도 |
| 발성 이상 탐지 | 기침·쉰 목소리 |

## 제약

- 학습 데이터·GPU·배포 크기
- Streamlit Cloud 비적합 → API 서버 GPU tier

## 단계

1. 데이터: 사용자 opt-in 녹음 (익명)
2. 프로토타입: 오프라인 노트북
3. API optional endpoint `/analyze/deep`

베타에서는 **규칙+librosa** 유지.
