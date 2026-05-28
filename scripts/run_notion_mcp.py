from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config.settings import load_environment


def main() -> int:
    load_environment(ROOT_DIR / ".env")
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        print("Missing token: set NOTION_TOKEN in .env")
        return 2

    env = os.environ.copy()
    env["OPENAPI_MCP_HEADERS"] = json.dumps(
        {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
        }
    )
    command = ["npx", "-y", "@notionhq/notion-mcp-server"]
    return subprocess.call(command, cwd=ROOT_DIR, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
