@echo off
echo ========================================
echo   Git setup check for vocal-coach
echo ========================================
echo.

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git is NOT installed.
    echo.
    echo Install with PowerShell ^(Admin^):
    echo   winget install --id Git.Git -e
    echo.
    echo Then RESTART PowerShell.
    echo See: docs folder ^(next-steps guide^)
    pause
    exit /b 1
)

echo Git OK:
git --version
echo.
echo Next ^(replace YOUR_USERNAME^):
echo   cd /d "%~dp0"
echo   git init
echo   git add .
echo   git commit -m "vocal-coach web MVP"
echo   git remote add origin https://github.com/YOUR_USERNAME/vocal-coach.git
echo   git push -u origin main
echo.
echo Deploy: https://share.streamlit.io
pause
