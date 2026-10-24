from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "streamlit_app.py"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "reproguard_launcher.log"
HOST = "127.0.0.1"
PORT = 8501
URL = f"http://{HOST}:{PORT}"


def port_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def open_app() -> None:
    webbrowser.open(URL, new=2)


def main() -> int:
    LOG_DIR.mkdir(exist_ok=True)

    # If ReproGuard is already running, do not launch a duplicate server.
    if port_open(HOST, PORT):
        open_app()
        return 0

    python_exe = Path(sys.executable)
    # setup_windows.bat creates the shortcut using pythonw.exe. If this file is
    # launched with normal python.exe, prefer pythonw.exe when it is available.
    if python_exe.name.lower() == "python.exe":
        pythonw = python_exe.with_name("pythonw.exe")
        if pythonw.exists():
            python_exe = pythonw

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write("\n--- ReproGuard launch ---\n")
        log.flush()
        subprocess.Popen(
            [
                str(python_exe),
                "-m",
                "streamlit",
                "run",
                str(APP),
                "--server.address",
                HOST,
                "--server.port",
                str(PORT),
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=str(ROOT),
            stdout=log,
            stderr=log,
            creationflags=creationflags,
            close_fds=os.name != "nt",
        )

    # Give Streamlit time to start, then open the browser.
    for _ in range(60):
        if port_open(HOST, PORT):
            open_app()
            return 0
        time.sleep(0.25)

    # Even if startup is slow, opening the URL is still useful; the browser can
    # refresh when the local service becomes ready. Details are in the log file.
    open_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
