from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config.settings import load_environment


def main() -> int:
    load_environment(ROOT_DIR / ".env")
    missing = [name for name in ("SLACK_BOT_TOKEN", "SLACK_TEAM_ID") if not os.getenv(name, "").strip()]
    if missing:
        print(f"Missing token: set {', '.join(missing)} in .env")
        return 2

    command = ["npx", "-y", "@modelcontextprotocol/server-slack"]
    return subprocess.call(command, cwd=ROOT_DIR, env=os.environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
