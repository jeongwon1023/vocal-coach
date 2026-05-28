# 로컬 정밀 분석 (CREPE · Demucs)

Streamlit Cloud는 메모리 제한으로 **pYIN + HPSS**만 사용합니다.  
로컬 PC에서 아래 패키지를 설치하면 정밀도를 높일 수 있습니다.

## 설치

```powershell
cd vocal-coach
.\venv\Scripts\python.exe -m pip install -r requirements-precision.txt
```

## 환경 변수

| 변수 | 값 | 설명 |
|------|-----|------|
| `USE_CREPE=1` | 기본(로컬) | CREPE F0 앙상블 |
| `USE_CREPE=0` | Cloud 기본 | pYIN만 |
| `VOCAL_SEP=enhanced` | 기본 | 강화 HPSS |
| `VOCAL_SEP=demucs` | 선택 | Demucs AI 보컬 분리 (느림, GPU 권장) |

## Windows 예시

```powershell
$env:USE_CREPE="1"
$env:VOCAL_SEP="demucs"
.\run_web.bat
```

## 주의

- Demucs + torch는 **수 GB** 디스크·RAM 사용
- 첫 실행 시 모델 다운로드로 시간 소요
- MR/반주 녹음에 효과가 큼
