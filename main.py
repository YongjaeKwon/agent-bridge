from __future__ import annotations

import json
import sys

from config.settings import integration_status, load_environment, missing_required_env


def main() -> int:
    load_environment()
    missing = missing_required_env()
    payload = {
        "ok": not missing,
        "missing": missing,
        "integrations": integration_status(),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
