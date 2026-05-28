# API 서버 배포 (Railway / Render)

`api_server.py` — FastAPI · 모바일 Expo 연동용

## 로컬 실행

```powershell
.\run_api.bat
# 또는
.\venv\Scripts\uvicorn.exe api_server:app --host 0.0.0.0 --port 8000
```

헬스체크: `GET http://localhost:8000/health`

## Docker

```powershell
docker build -f Dockerfile.api -t vocal-coach-api .
docker run -p 8000:8000 vocal-coach-api
```

## Railway

1. GitHub `vocal-coach` 연결
2. **New Service** → Dockerfile path: `Dockerfile.api`
3. Port: `8000`
4. Variables: `OPENAI_API_KEY` (GPT 사용 시)

## Render

1. **New Web Service** → Docker
2. Dockerfile: `Dockerfile.api`
3. Health Check Path: `/health`

## CORS

기본 `allow_origins=["*"]` — 프로덕션에서는 모바일 앱 도메인으로 제한 권장.

## 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 상태 |
| POST | `/analyze` | 동기 분석 |
| POST | `/analyze/async` | 비동기 job |
| GET | `/jobs/{id}` | job 결과 |
| GET | `/records` | 기록 목록 |
