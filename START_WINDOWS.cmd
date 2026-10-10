@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto setup
if not exist "web\node_modules" goto setup
if not exist ".env" goto setup
goto start
:setup
py -3.12 scripts\bootstrap.py
if errorlevel 1 (
 echo Setup failed. Install Python 3.12 and Node.js 22 or 24, then retry.
 pause
 exit /b 1
)
:start
.venv\Scripts\python.exe scripts\credentials.py
.venv\Scripts\python.exe scripts\start.py --preview
pause
