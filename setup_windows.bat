@echo off
setlocal
cd /d "%~dp0"

echo ======================================================
echo        ReproGuard AI - Windows Setup
echo ======================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PY_CMD=python"
  ) else (
    echo Python was not found.
    echo Install Python 3.10 or newer from https://www.python.org/downloads/
    echo During installation, select "Add Python to PATH".
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment...
  if "%PY_CMD%"=="py" (
    py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :failed
) else (
  echo [1/4] Virtual environment already exists.
)

echo [2/4] Installing ReproGuard dependencies...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :failed
pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [3/4] Running a quick self-test...
set "PYTHONPATH=%CD%\src"
python -c "from reproguard.parser import parse_pdf; print('ReproGuard core import: OK')"
if errorlevel 1 goto :failed

echo [4/4] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\create_desktop_shortcut.ps1"
if errorlevel 1 (
  echo Shortcut creation failed, but ReproGuard is installed.
  echo You can still run it using run_windows.bat.
)

echo.
echo ======================================================
echo Setup complete.
echo Double-click the "ReproGuard AI" icon on your Desktop.
echo You can also double-click run_windows.bat in this folder.
echo ======================================================
echo.
pause
exit /b 0

:failed
echo.
echo Setup failed. Please copy the error message above and send it to ChatGPT.
pause
exit /b 1
