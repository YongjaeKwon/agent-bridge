from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from .agent_config import all_agent_ids, get_agent_definition, list_agent_definitions, main_agent_id, worker_agent_ids
from .store import ROOT_DIR, add_event, list_tasks, update_task


@dataclass(frozen=True)
class AgentCommand:
    agent: str
    command: list[str]


DEFAULT_COMMANDS = {
    "claude": "claude -p",
    "codex": "codex exec",
}

WINDOWS_DEFAULT_COMMANDS = {
    "claude": "cmd /c claude.cmd -p",
    "codex": "cmd /c codex.cmd exec",
}


def command_for(agent: str) -> AgentCommand | None:
    agent_definition = get_agent_definition(agent)
    if agent_definition:
        if not agent_definition.command:
            return None
        return AgentCommand(agent=agent, command=agent_definition.command)

    env_name = f"ECC_{agent.upper().replace('-', '_')}_COMMAND"
    value = os.getenv(env_name, "").strip()
    if not value:
        return None
    import shlex

    return AgentCommand(agent=agent, command=shlex.split(value, posix=os.name != "nt"))


def build_prompt(task: dict[str, Any], agent: str) -> str:
    agent_definition = get_agent_definition(agent)
    role = agent_definition.role if agent_definition else f"{agent} agent"
    roster = "\n".join(f"- {item.id}: {item.role}" for item in list_agent_definitions())
    planner_rules = ""
    if agent == main_agent_id():
        planner_rules = f"""
Planner responsibilities:
- You are the only agent that receives the user's top-level request.
- Turn the request into concrete tasks.
- Assign subagent work to: {", ".join(worker_agent_ids())}.
- Use `python ecc.py task create --title "..." --body "..." --assignee <agent-id>` for each delegated task.
- Use Linear/Notion/GitHub sync commands when useful and safe.
"""
    return f"""You are {agent} working inside this repository through the ECC harness.

Agent role:
{role}

Available agents:
{roster}
{planner_rules}

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
- Use agent ids, not tool names, for assignees.
- If you hit auth, token, quota, rate limit, context limit, or budget issues, log the blocker and stop instead of looping.
"""


def runnable_tasks(agents: list[str], task_id: str = "") -> list[dict[str, Any]]:
    allowed = set(agents)
    return [
        task
        for task in list_tasks()
        if task.get("status") in {"open", "in_progress"}
        and task.get("assignee") in allowed
        and (not task_id or task.get("id") == task_id)
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
    command = [*agent_command.command, prompt]
    print(f"\n[ecc] starting {agent} on {task['id']}: {task['title']}", flush=True)
    print(f"[ecc] command: {agent_command.command[0]} ...\n", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT_DIR,
            text=True,
            timeout=timeout,
            check=False,
        )
        message = f"exit={completed.returncode}"
        add_event(agent, "auto.finish", message, task["id"])
        print(f"\n[ecc] finished {agent} on {task['id']} with exit={completed.returncode}\n", flush=True)
        if completed.returncode != 0:
            update_task(
                task["id"],
                status="blocked",
                summary=f"{agent} CLI exited with {completed.returncode}. Check terminal output for auth, token, quota, or runtime errors.",
            )
    except subprocess.TimeoutExpired:
        message = f"timeout={timeout}"
        add_event(agent, "auto.timeout", message, task["id"])
        update_task(task["id"], status="blocked", summary=f"{agent} CLI timed out after {timeout}s.")
        print(f"\n[ecc] timed out {agent} on {task['id']} after {timeout}s\n", file=sys.stderr, flush=True)
        return {
            "agent": agent,
            "task_id": task["id"],
            "timeout": timeout,
        }
    except FileNotFoundError as exc:
        message = f"missing_command={exc}"
        add_event(agent, "auto.command_missing", message, task["id"])
        update_task(task["id"], status="blocked", summary=f"{agent} CLI command was not found. Check ECC_{agent.upper()}_COMMAND.")
        print(f"\n[ecc] command missing for {agent}: {exc}\n", file=sys.stderr, flush=True)
        return {
            "agent": agent,
            "task_id": task["id"],
            "missing_command": str(exc),
        }
    return {
        "agent": agent,
        "task_id": task["id"],
        "returncode": completed.returncode,
    }


def run_auto_once(agents: list[str], dry_run: bool = False, timeout: int = 1800, task_id: str = "") -> list[dict[str, Any]]:
    results = []
    for task in runnable_tasks(agents, task_id):
        results.append(run_agent_task(task, task["assignee"], dry_run=dry_run, timeout=timeout))
    return results
