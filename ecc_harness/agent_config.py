from __future__ import annotations

import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .store import ROOT_DIR


CONFIG_FILE = ROOT_DIR / "ecc_agents.json"


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    runner: str
    role: str
    model_policy: str
    command_env: str
    command: list[str]
    enabled: bool
    optional: bool


DEFAULT_CONFIG: dict[str, Any] = {
    "mainAgent": "planner",
    "agents": [
        {
            "id": "planner",
            "runner": "claude",
            "commandEnv": "ECC_PLANNER_COMMAND",
            "role": "Main PM agent. Plan, write planning/design docs, split work, assign subagents, and coordinate external sync.",
            "modelPolicy": "Use the strongest available model only for ambiguous planning, architecture, and final decisions. Keep routine ticketing concise.",
            "defaultWindowsCommand": "cmd /c claude.cmd -p",
            "defaultCommand": "claude -p",
        },
        {
            "id": "codex",
            "runner": "codex",
            "commandEnv": "ECC_CODEX_COMMAND",
            "role": "Implementation, backend/integration work, verification, and code review.",
            "modelPolicy": "Prefer the fastest cost-efficient coding model. Escalate only for architecture review, hard debugging, or security-sensitive changes.",
            "defaultWindowsCommand": "cmd /c codex.cmd exec",
            "defaultCommand": "codex exec",
        },
        {
            "id": "gemini",
            "runner": "gemini",
            "commandEnv": "ECC_GEMINI_COMMAND",
            "role": "Alternative analysis/research agent for broad review and ideation.",
            "modelPolicy": "Optional broad review slot. Use only when additional perspective is worth the extra token spend.",
            "optional": True,
            "enabledByDefault": False,
            "defaultWindowsCommand": "cmd /c gemini.cmd -p",
            "defaultCommand": "gemini -p",
        },
        {
            "id": "claude-code",
            "runner": "claude",
            "commandEnv": "ECC_CLAUDE_CODE_COMMAND",
            "role": "Claude Code worker for focused UI/UX, frontend, and writing tasks.",
            "modelPolicy": "Prefer a fast frontend/writing model for focused execution. Escalate only for complex UX strategy.",
            "defaultWindowsCommand": "cmd /c claude.cmd -p",
            "defaultCommand": "claude -p",
        },
    ],
}


def load_agent_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG


def _split_command(command: str) -> list[str]:
    return shlex.split(command, posix=os.name != "nt")


def list_agent_definitions() -> list[AgentDefinition]:
    config = load_agent_config()
    agents = []
    for raw in config.get("agents", []):
        default_key = "defaultWindowsCommand" if os.name == "nt" else "defaultCommand"
        env_command = os.getenv(raw.get("commandEnv", ""), "").strip()
        optional = bool(raw.get("optional", False))
        enabled_by_default = raw.get("enabledByDefault", True)
        enabled = bool(env_command or enabled_by_default)
        command_text = env_command or (raw.get(default_key, "") if enabled else "")
        agents.append(
            AgentDefinition(
                id=raw["id"],
                runner=raw.get("runner", raw["id"]),
                role=raw.get("role", ""),
                model_policy=raw.get("modelPolicy", ""),
                command_env=raw.get("commandEnv", ""),
                command=_split_command(command_text) if command_text else [],
                enabled=enabled,
                optional=optional,
            )
        )
    return agents


def get_agent_definition(agent_id: str) -> AgentDefinition | None:
    for agent in list_agent_definitions():
        if agent.id == agent_id:
            return agent
    return None


def main_agent_id() -> str:
    return load_agent_config().get("mainAgent", "planner")


def worker_agent_ids() -> list[str]:
    main = main_agent_id()
    return [agent.id for agent in list_agent_definitions() if agent.enabled and agent.id != main]


def all_agent_ids() -> list[str]:
    return [agent.id for agent in list_agent_definitions() if agent.enabled]
