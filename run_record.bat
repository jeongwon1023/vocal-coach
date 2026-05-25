@echo off
cd /d "%~dp0"
echo [vocal-coach] Full pipeline: record + clips + chart...
venv\Scripts\python.exe analysis.py sample.mp3 --save-record --compare --export-clips --growth-chart --json-out analysis_report.json
echo.
echo Done: pitch_result.png , records/ , clips/ , charts/
start "" "%~dp0pitch_result.png"
if exist charts\growth_chart.png start "" "%~dp0charts\growth_chart.png"
pause
