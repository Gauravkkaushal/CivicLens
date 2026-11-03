"""Local dev server with auto-reload: `python dev.py [port]`.

uvicorn's own --reload on Windows restarts the worker with CTRL_C_EVENT, which either never
arrives (reload hangs) or hits every process on the console (server dies). watchfiles stops the
worker with TerminateProcess instead, so reloads are quick and reliable. Only app/ is watched.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from watchfiles import PythonFilter, run_process


def serve(port: int) -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)  # "app" and the app.main import resolve from backend/, wherever this is launched
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_process("app", target=serve, args=(port,), watch_filter=PythonFilter(), sigint_timeout=1)
