@echo off
setlocal
set "PORT=8501"

echo Looking for ReproGuard AI on port %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
  echo Stopping process %%a...
  taskkill /PID %%a /F >nul 2>nul
)

echo ReproGuard AI has been stopped if it was running.
pause
