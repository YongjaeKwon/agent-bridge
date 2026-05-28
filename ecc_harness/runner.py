from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config.settings import get_env

from .store import ECC_DIR, ROOT_DIR, add_event


def _log_path(name: str) -> Path:
    ECC_DIR.mkdir(exist_ok=True)
    return ECC_DIR / f"{name}.log"


def _int_env(name: str, default: int) -> int:
    try:
        return int(get_env(name, str(default)))
    except ValueError:
        return default


def start_auto_process(task_id: str = "", agents: str = "", dispatch: bool = False, loop: bool = False) -> dict[str, str]:
    command = [sys.executable, "ecc.py", "auto"]
    if task_id:
        command.extend(["--task", task_id])
    if agents:
        command.extend(["--agents", agents])
    if dispatch:
        command.append("--dispatch")
    if loop:
        command.extend(
            [
                "--loop",
                "--max-cycles",
                str(_int_env("ECC_AUTO_LOOP_CYCLES", 20)),
                "--interval",
                str(_int_env("ECC_AUTO_LOOP_INTERVAL", 30)),
            ]
        )
    else:
        command.extend(["--max-cycles", "1"])

    name = f"run-{task_id or 'loop'}"
    stdout_path = _log_path(name)
    stdout = stdout_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=ROOT_DIR,
        stdout=stdout,
        stderr=subprocess.STDOUT,
        text=True,
    )
    add_event("system", "runner.start", f"pid={process.pid} log={stdout_path}", task_id)
    return {"pid": str(process.pid), "log": str(stdout_path), "command": " ".join(command)}
