@echo off
cd /d "%~dp0"
echo [vocal-coach] Analyze sample.mp3...
venv\Scripts\python.exe analysis.py sample.mp3 --json-out analysis_report.json
echo.
echo Done: pitch_result.png , analysis_report.json
start "" "%~dp0pitch_result.png"
pause
