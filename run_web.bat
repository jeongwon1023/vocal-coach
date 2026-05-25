@echo off
cd /d "%~dp0"

echo.
echo ========================================
echo   vocal-coach Web UI + Auth Server
echo ========================================
echo   App:  http://localhost:8501
echo   Auth: http://localhost:8001
echo.
echo   Browser opens in 4 seconds.
echo   Press Ctrl+C to stop both servers.
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: venv\Scripts\python.exe not found.
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ERROR: app.py not found in %CD%
    pause
    exit /b 1
)

if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]>"%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">>"%USERPROFILE%\.streamlit\credentials.toml"
)

set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_SHOW_EMAIL_PROMPT=false

echo Starting OAuth auth server on port 8001...
start "vocal-coach-auth" /MIN cmd /c "venv\Scripts\python.exe -m uvicorn auth_server:app --host 127.0.0.1 --port 8001"

start "" cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8501"
venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless false --server.showEmailPrompt false --browser.gatherUsageStats false
pause
