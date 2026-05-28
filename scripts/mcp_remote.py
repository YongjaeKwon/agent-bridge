from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config.settings import load_environment

SERVERS = {
    "github": {
        "url": "https://api.githubcopilot.com/mcp/",
        "token_env": ("GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"),
    },
    "linear": {
        "url": "https://mcp.linear.app/mcp",
        "token_env": ("LINEAR_API_KEY",),
    },
}


def get_token(names: tuple[str, ...]) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def main() -> int:
    load_environment(ROOT_DIR / ".env")
    if len(sys.argv) != 2 or sys.argv[1] not in SERVERS:
        names = ", ".join(sorted(SERVERS))
        print(f"Usage: python scripts/mcp_remote.py <{names}>", file=sys.stderr)
        return 2

    server = SERVERS[sys.argv[1]]
    token = get_token(server["token_env"])
    if not token:
        expected = " or ".join(server["token_env"])
        print(f"Missing token: set {expected} in .env", file=sys.stderr)
        return 2

    command = [
        "npx",
        "-y",
        "mcp-remote",
        server["url"],
        "--header",
        f"Authorization: Bearer {token}",
    ]
    return subprocess.call(command, cwd=ROOT_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
