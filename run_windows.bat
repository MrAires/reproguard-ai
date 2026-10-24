@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ReproGuard has not been installed yet.
  echo Running setup...
  call setup_windows.bat
  exit /b %errorlevel%
)

start "" ".venv\Scripts\pythonw.exe" "%CD%\launcher_windows.py"
exit /b 0
