@echo off
setlocal
set "PROJECT=%~dp0.."

where code >nul 2>nul
if errorlevel 1 (
  echo VS Code's command-line launcher was not found.
  echo Open VS Code manually and select this folder:
  echo %PROJECT%
  pause
  exit /b 1
)

code "%PROJECT%"
echo.
echo EvalAI is open in VS Code.
echo Press Ctrl+Shift+B and choose "EvalAI: Start Website".
echo Then open http://localhost:5173
timeout /t 6 >nul

