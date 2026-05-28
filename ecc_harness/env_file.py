from __future__ import annotations

from pathlib import Path

from config.settings import ENV_FILE


def read_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_env_values(updates: dict[str, str], path: Path = ENV_FILE) -> None:
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    next_lines: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            next_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            next_lines.append(f"{key}={updates[key].strip()}")
            seen.add(key)
        else:
            next_lines.append(line)

    for key, value in updates.items():
        if key not in seen:
            next_lines.append(f"{key}={value.strip()}")

    path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
