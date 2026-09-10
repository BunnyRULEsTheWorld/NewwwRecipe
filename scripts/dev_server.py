#!/usr/bin/env python3
"""One-window dev launcher for the NewwwRecipe backend + frontend.

Usage (from repo root):

    python scripts\dev_server.py

or, on Windows CMD:

    .venv\Scripts\python.exe scripts\dev_server.py

The launcher starts the FastAPI backend on 127.0.0.1:8000 and the Vite dev
frontend on 127.0.0.1:5173.  Press Ctrl+C to stop both.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    root = repo_root()
    web = root / "web"
    venv_python = root / ".venv" / "Scripts" / "python.exe"
    npm = "npm.cmd" if sys.platform == "win32" else "npm"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["NR_BACKEND_HOST"] = env.get("NR_BACKEND_HOST", "127.0.0.1")
    env["NR_BACKEND_PORT"] = env.get("NR_BACKEND_PORT", "8000")

    if not venv_python.exists():
        print(f"Missing virtual-env Python: {venv_python}", file=sys.stderr)
        print("Create it first: python -m venv .venv", file=sys.stderr)
        return 1

    backend_cmd = [
        str(venv_python),
        "-m",
        "uvicorn",
        "creative_recipe.web.app:app",
        "--host",
        env["NR_BACKEND_HOST"],
        "--port",
        env["NR_BACKEND_PORT"],
        "--log-level",
        "warning",
    ]

    frontend_cmd = [npm, "run", "dev"]

    print("Starting NewwwRecipe dev servers...")
    print(f"  Backend:  http://{env['NR_BACKEND_HOST']}:{env['NR_BACKEND_PORT']}/")
    print("  Frontend: http://127.0.0.1:5173/")
    print("  Press Ctrl+C to stop both.\n")

    kwargs: dict = {}
    if sys.platform == "win32":
        # On Windows, create a new process group so terminate can reach children.
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    backend = subprocess.Popen(
        backend_cmd,
        cwd=str(root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        **kwargs,
    )
    time.sleep(0.5)  # give backend a moment to bind

    frontend = subprocess.Popen(
        frontend_cmd,
        cwd=str(web),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        **kwargs,
    )

    def shutdown(_signum=None, _frame=None) -> None:
        print("\nShutting down servers...")
        for proc in (backend, frontend):
            try:
                if sys.platform == "win32":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGINT)
            except Exception:
                pass
        for proc in (backend, frontend):
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    def pump(proc: subprocess.Popen, label: str) -> None:
        if proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            sys.stdout.write(f"[{label}] {line}")
            sys.stdout.flush()

    import threading

    threading.Thread(target=pump, args=(backend, "backend"), daemon=True).start()
    threading.Thread(target=pump, args=(frontend, "frontend"), daemon=True).start()

    # Keep main thread alive until a process exits.
    while True:
        if backend.poll() is not None or frontend.poll() is not None:
            shutdown()
        time.sleep(0.5)


if __name__ == "__main__":
    raise SystemExit(main())
