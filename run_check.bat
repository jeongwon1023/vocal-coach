@echo off
cd /d "%~dp0"
echo [vocal-coach] Environment check...
venv\Scripts\python.exe check_setup.py
pause
