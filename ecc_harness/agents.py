from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any

from .store import ROOT_DIR, add_event, list_tasks, update_task


@dataclass(frozen=True)
class AgentCommand:
    agent: str
    command: list[str]


DEFAULT_COMMANDS = {
    "claude": "claude -p",
    "codex": "codex exec",
}


def command_for(agent: str) -> AgentCommand | None:
    env_name = f"ECC_{agent.upper()}_COMMAND"
    value = os.getenv(env_name, DEFAULT_COMMANDS.get(agent, "")).strip()
    if not value:
        return None
    return AgentCommand(agent=agent, command=shlex.split(value, posix=os.name != "nt"))


def build_prompt(task: dict[str, Any], agent: str) -> str:
    return f"""You are {agent} working inside this repository through the ECC harness.

Task id: {task["id"]}
Title: {task["title"]}
Body:
{task.get("body", "")}

Rules:
- Start by running: python ecc.py task claim {task["id"]} --agent {agent}
- Log meaningful progress with: python ecc.py log --agent {agent} --task {task["id"]} --message "..."
- Make the smallest safe code/doc changes required for the task.
- Run relevant verification before finishing.
- Finish with: python ecc.py task done {task["id"]} --agent {agent} --summary "..."
- If the task should be handed to another agent, create a follow-up task with a clear title/body/assignee.
"""


def runnable_tasks(agents: list[str]) -> list[dict[str, Any]]:
    allowed = set(agents)
    return [
        task
        for task in list_tasks()
        if task.get("status") in {"open", "in_progress"} and task.get("assignee") in allowed
    ]


def run_agent_task(task: dict[str, Any], agent: str, dry_run: bool = False, timeout: int = 1800) -> dict[str, Any]:
    agent_command = command_for(agent)
    prompt = build_prompt(task, agent)
    if dry_run:
        return {"agent": agent, "task_id": task["id"], "dry_run": True, "prompt": prompt}
    if agent_command is None:
        add_event("system", "auto.skip", f"No command configured for {agent}", task["id"])
        return {"agent": agent, "task_id": task["id"], "skipped": "missing_command"}

    update_task(task["id"], status="in_progress", assignee=agent)
    add_event("system", "auto.start", "Starting agent CLI", task["id"])
    completed = subprocess.run(
        [*agent_command.command, prompt],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    message = f"exit={completed.returncode}\nstdout={completed.stdout[-4000:]}\nstderr={completed.stderr[-4000:]}"
    add_event(agent, "auto.finish", message, task["id"])
    return {
        "agent": agent,
        "task_id": task["id"],
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1000:],
        "stderr_tail": completed.stderr[-1000:],
    }


def run_auto_once(agents: list[str], dry_run: bool = False, timeout: int = 1800) -> list[dict[str, Any]]:
    results = []
    for task in runnable_tasks(agents):
        results.append(run_agent_task(task, task["assignee"], dry_run=dry_run, timeout=timeout))
    return results
