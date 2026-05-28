from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except ModuleNotFoundError:
    _load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"


@dataclass(frozen=True)
class Integration:
    name: str
    required_env: tuple[str, ...]
    optional_env: tuple[str, ...] = ()


INTEGRATIONS = (
    Integration("github", ("GITHUB_TOKEN",), ("GITHUB_PERSONAL_ACCESS_TOKEN",)),
    Integration("linear", ("LINEAR_API_KEY",)),
    Integration("slack", ("SLACK_BOT_TOKEN", "SLACK_TEAM_ID"), ("SLACK_CHANNEL_IDS",)),
    Integration("notion", ("NOTION_TOKEN",)),
)


def load_environment(env_file: Path = ENV_FILE) -> None:
    if _load_dotenv:
        _load_dotenv(env_file)
        return

    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_token(*names: str) -> str:
    for name in names:
        value = get_env(name)
        if value:
            return value
    return ""


def missing_required_env() -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for integration in INTEGRATIONS:
        absent = [name for name in integration.required_env if not get_env(name)]
        if absent:
            missing[integration.name] = absent
    return missing


def mask_secret(value: str) -> str:
    if not value:
        return ""
    return "set"


def integration_status() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for integration in INTEGRATIONS:
        values = [get_env(name) for name in integration.required_env]
        ready = all(values)
        rows.append(
            {
                "name": integration.name,
                "status": "ready" if ready else "missing",
                "required": ", ".join(integration.required_env),
                "tokens": ", ".join(mask_secret(value) for value in values if value),
            }
        )
    return rows
