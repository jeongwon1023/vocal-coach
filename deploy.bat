@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo   Vocal Coach AI - Deploy Prep
echo ========================================
echo.

where git >nul 2>&1
if errorlevel 1 goto NO_GIT
echo [OK] Git installed
git --version
echo.
goto AFTER_GIT

:NO_GIT
echo [X] Git not found
echo     Install: winget install --id Git.Git -e
echo     Then open a NEW PowerShell window.
echo.

:AFTER_GIT
echo --- Smoke test ---
if not exist "venv\Scripts\python.exe" goto NO_VENV
venv\Scripts\python.exe tests\test_ui_smoke.py
if errorlevel 1 goto END
echo.
goto AFTER_TEST

:NO_VENV
echo [!] venv not found. Run: python -m venv venv
echo.

:AFTER_TEST
echo --- Secret file check ---
if exist ".env" (
    echo [OK] .env exists locally - it must NOT be pushed to GitHub
) else (
    echo [!] .env not found - OK for deploy, set secrets on Streamlit Cloud
)
findstr /i /c:".env" .gitignore >nul 2>&1
if errorlevel 1 (
    echo [X] .env is NOT in .gitignore - fix before push
) else (
    echo [OK] .env is listed in .gitignore
)
echo.

if not exist ".git" goto NO_REPO
echo [OK] Git repo exists
git status -sb
echo.
goto CLOUD

:NO_REPO
echo [!] No git repo yet. Run these commands:
echo     git init
echo     git add .
echo     git commit -m "vocal-coach beta"
echo     git branch -M main
echo     git remote add origin https://github.com/YOUR_USERNAME/vocal-coach.git
echo     git push -u origin main
echo.

:CLOUD
echo --- Streamlit Cloud ---
echo 1. Open https://share.streamlit.io
echo 2. New app - pick repo - Main file: app.py
echo 3. Secrets - see .streamlit\secrets.toml.example
echo    OPENAI_API_KEY = your-key
echo    OPENAI_MODEL = gpt-4o-mini
echo 4. Click Deploy
echo.
echo packages.txt includes ffmpeg for audio analysis.
echo Full checklist: docs\BETA-LAUNCH.md
echo.
echo Tip: On PowerShell, prefer:  .\deploy.ps1
echo.

:END
pause
