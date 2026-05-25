@echo off
cd /d "%~dp0"
echo [vocal-coach] API server http://localhost:8000
venv\Scripts\python.exe -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
pause
