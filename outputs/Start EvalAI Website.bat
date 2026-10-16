@echo off
setlocal
set "PROJECT=%~dp0.."
cd /d "%PROJECT%"

if not exist "work\.venv\Scripts\python.exe" (
  echo EvalAI has not been set up yet.
  echo Run this command in the VS Code terminal first:
  echo powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Frontend dependencies are missing.
  echo Run this command in the VS Code terminal first:
  echo powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
  pause
  exit /b 1
)

echo Starting EvalAI backend...
start "EvalAI Backend" powershell -NoExit -NoProfile -Command "$env:DATABASE_URL='sqlite:///./evalai.db'; $env:MOCK_MODE='true'; Set-Location '%PROJECT%'; & '.\work\.venv\Scripts\python.exe' -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000"

echo Starting EvalAI frontend...
start "EvalAI Frontend" powershell -NoExit -NoProfile -ExecutionPolicy Bypass -File "%PROJECT%\scripts\start_frontend.ps1"

echo Waiting for the website to start...
timeout /t 6 /nobreak >nul
start "" "http://localhost:5173"

echo EvalAI is opening in your browser.
echo Close the two EvalAI terminal windows when you want to stop it.
timeout /t 5 /nobreak >nul

