@echo off
cd /d "%~dp0"
echo [vocal-coach] Analyze + GPT + save record...
venv\Scripts\python.exe analysis.py sample.mp3 --gpt --save-record --compare
pause
