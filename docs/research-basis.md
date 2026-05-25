# 분석 엔진 — 논문·연구 근거

`vocal_research.py` + `analysis.py`가 사용하는 학술·음성학 기반.

## 음정 (F0)

| 항목 | 방법 | 출처 |
|------|------|------|
| F0 추출 | **pYIN** + voiced probability | Mauch & Dixon, ICASSP 2014 |
| 유성 프레임 | voiced_prob ≥ 0.5 | pYIN HMM 디코딩 |
| 멜로디 일치 | 가중 평균 ±25 cent | PMC11026466: 훈련 가수 ~22 cent |
| 등급 | pro ≤22 / good ≤35 / fair ≤50 cent | 지각 mistuning 경계 |

## 비브라토

| 항목 | 기준 | 출처 |
|------|------|------|
| Rate | 4.5–6.5 Hz 정상 | Nix et al.; Voice Science |
| Wobble | < 4 Hz | 너무 느린 떨림 |
| Bleat | > 7 Hz | 너무 빠른 떨림 |
| Extent | F0 contour FFT peak-to-trough | Timbre & Orchestration Resource |

## 박자

| 항목 | 방법 | 출처 |
|------|------|------|
| Onset | **Superflux** (lag=1, max_size=1) | Böck & Widmer, DAFx 2013 |
| IOI CV | onset 간격 변동계수, 목표 0.28 | 자체 + 에너지 envelope 보조 |

## 호흡·음색

| 항목 | 방법 | 출처 |
|------|------|------|
| Jitter | local period perturbation % | Praat manual |
| Shimmer | amplitude perturbation % | Praat manual |
| HNR | autocorrelation peak/valley | PMC11026466 (hoarseness) |
| Singer's formant | 2–4 kHz / 0–1 kHz energy | Sundberg |

## 파일

- `vocal_research.py` — 논문 지표 계산
- `analysis.py` — Stage 1~4 점수·코칭에 통합
