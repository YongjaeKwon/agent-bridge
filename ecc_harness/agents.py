from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_config import all_agent_ids, get_agent_definition, list_agent_definitions, main_agent_id, worker_agent_ids
from .i18n import language_name
from .limits import classify_blocker
from .store import ECC_DIR, ROOT_DIR, add_event, list_tasks, update_task


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

COMPACT_LIMIT = 1200
OUTPUT_TAIL_LINES = 80


def compact_prompts_enabled() -> bool:
    return os.getenv("ECC_COMPACT_PROMPTS", "true").lower() not in {"0", "false", "no", "off"}


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
    if compact_prompts_enabled():
        return build_compact_prompt(task, agent)

    agent_definition = get_agent_definition(agent)
    role = agent_definition.role if agent_definition else f"{agent} agent"
    model_policy = agent_definition.model_policy if agent_definition else ""
    roster = "\n".join(f"- {item.id}: {item.role}" for item in list_agent_definitions())
    planner_rules = ""
    if agent == main_agent_id():
        planner_rules = f"""
Planner responsibilities:
- Write planning docs, design docs, tickets, decisions, and meeting notes in {language_name()} unless the user asks otherwise.
- You are the only agent that receives the user's top-level request.
- Turn the request into concrete tasks with useful Linear-style descriptions, not title-only backlog items.
- Create or update PM docs before delegating when the request changes project direction:
  - docs/ecc/plan.md for goals, scope, milestones, and task breakdown
  - docs/ecc/design.md for architecture, UI/UX, data flow, integration choices, and tradeoffs
  - docs/ecc/decisions.md for decisions, alternatives considered, owners, and dates
- Assign subagent work to: {", ".join(worker_agent_ids())}.
- Use `python ecc.py task create --title "..." --body "..." --assignee <agent-id> --parent-task {task["id"]} --sync-linear` for each delegated task when Linear is configured.
- `--parent-task {task["id"]}` makes delegated Linear issues sub-issues of the current planner issue when the parent has a Linear issue id.
- Each delegated task body must include:
  - Goal
  - Context/background
  - Deliverables
  - Acceptance Criteria
  - Suggested Verification
  - Dependencies or blockers, if any
- Use Linear/Notion/GitHub sync commands when useful and safe.
"""
    return f"""You are {agent} working inside this repository through the ECC harness.

Agent role:
{role}

Model policy:
{model_policy}

Available agents:
{roster}
{planner_rules}

Task id: {task["id"]}
Title: {task["title"]}
Body:
{task.get("body", "")}

Rules:
- Use {language_name()} for user-facing planning docs, task descriptions, meeting notes, and summaries unless the task explicitly says otherwise.
- Start by running: python ecc.py task claim {task["id"]} --agent {agent}
- Log meaningful progress with: python ecc.py log --agent {agent} --task {task["id"]} --message "..."
- Make the smallest safe code/doc changes required for the task.
- Run relevant verification before finishing.
- Finish with: python ecc.py task done {task["id"]} --agent {agent} --summary "..."
- If the task should be handed to another agent, create a follow-up task with a clear title/body/assignee.
- Use agent ids, not tool names, for assignees.
- If you hit auth, token, quota, rate limit, context limit, or budget issues, log the blocker and stop instead of looping.
"""


def write_task_context(task: dict[str, Any], agent: str) -> Path:
    context_dir = ECC_DIR / "contexts"
    context_dir.mkdir(exist_ok=True)
    context_file = context_dir / f"{task['id']}-{agent}.md"
    context_file.write_text(
        f"""# ECC Task Context

Task id: {task["id"]}
Title: {task["title"]}
Assignee: {task.get("assignee", "")}
Status: {task.get("status", "")}
Source: {task.get("source", "")}
Linear: {task.get("linear_id", "")}

## Body
{task.get("body", "")}
""",
        encoding="utf-8",
    )
    return context_file


def build_compact_prompt(task: dict[str, Any], agent: str) -> str:
    agent_definition = get_agent_definition(agent)
    role = agent_definition.role if agent_definition else f"{agent} agent"
    model_policy = agent_definition.model_policy if agent_definition else ""
    context_file = write_task_context(task, agent)
    common = f"""ECC {task["id"]}: {task["title"]}
Agent: {agent}
Role: {role}
Model: {model_policy}
Lang: {language_name()}
Context file: {context_file}

Commands:
- python ecc.py task claim {task["id"]} --agent {agent}
- python ecc.py log --agent {agent} --task {task["id"]} --message "..."
- python ecc.py task done {task["id"]} --agent {agent} --summary "..."

Read context. Do needed work only. Log blockers. Stop on auth/quota/context errors.
"""
    if agent != main_agent_id():
        return common

    workers = ", ".join(worker_agent_ids())
    return common + f"""
PM:
- Use {language_name()} for docs, tickets, meeting notes, and summaries unless the user asks otherwise.
- Update docs/ecc/plan.md, docs/ecc/design.md, docs/ecc/decisions.md when direction changes.
- Split work for: {workers}.
- Create sub-issues:
  python ecc.py task create --title "..." --body "Goal/Context/Deliverables/Acceptance Criteria/Suggested Verification" --assignee <agent-id> --parent-task {task["id"]} --sync-linear
- Keep task bodies concise.
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


def run_streaming_command(command: list[str], timeout: int) -> tuple[int, str]:
    process = subprocess.Popen(
        command,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    deadline = time.monotonic() + timeout
    tail: list[str] = []
    assert process.stdout is not None
    while True:
        if time.monotonic() > deadline:
            process.kill()
            raise subprocess.TimeoutExpired(command, timeout)
        line = process.stdout.readline()
        if line:
            print(line, end="", flush=True)
            tail.append(line)
            if len(tail) > OUTPUT_TAIL_LINES:
                tail.pop(0)
            continue
        if process.poll() is not None:
            break
        time.sleep(0.1)
    return process.wait(), "".join(tail)


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
    prompt_dir = ECC_DIR / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    prompt_file = prompt_dir / f"{task['id']}-{agent}.md"
    prompt_file.write_text(prompt[:COMPACT_LIMIT] if compact_prompts_enabled() else prompt, encoding="utf-8")
    prompt_arg = (
        "Read the full UTF-8 task prompt from this local file and follow it exactly: "
        f"{prompt_file}"
    )
    command = [*agent_command.command, prompt_arg]
    print(f"\n[ecc] starting {agent} on {task['id']}: {task['title']}", flush=True)
    print(f"[ecc] command: {agent_command.command[0]} ...\n", flush=True)
    try:
        returncode, output_tail = run_streaming_command(command, timeout)
        message = f"exit={returncode}"
        add_event(agent, "auto.finish", message, task["id"])
        print(f"\n[ecc] finished {agent} on {task['id']} with exit={returncode}\n", flush=True)
        if returncode != 0:
            blocker = classify_blocker(output_tail, returncode)
            add_event(agent, f"blocker.{blocker.kind}", blocker.summary, task["id"])
            update_task(
                task["id"],
                status="blocked",
                blocker_type=blocker.kind,
                summary=blocker.summary,
            )
    except subprocess.TimeoutExpired:
        message = f"timeout={timeout}"
        add_event(agent, "auto.timeout", message, task["id"])
        update_task(task["id"], status="blocked", blocker_type="timeout", summary=f"{agent} CLI timed out after {timeout}s.")
        print(f"\n[ecc] timed out {agent} on {task['id']} after {timeout}s\n", file=sys.stderr, flush=True)
        return {
            "agent": agent,
            "task_id": task["id"],
            "timeout": timeout,
        }
    except FileNotFoundError as exc:
        message = f"missing_command={exc}"
        add_event(agent, "auto.command_missing", message, task["id"])
        update_task(
            task["id"],
            status="blocked",
            blocker_type="missing_command",
            summary=f"{agent} CLI command was not found. Check ECC_{agent.upper()}_COMMAND.",
        )
        print(f"\n[ecc] command missing for {agent}: {exc}\n", file=sys.stderr, flush=True)
        return {
            "agent": agent,
            "task_id": task["id"],
            "missing_command": str(exc),
        }
    return {
        "agent": agent,
        "task_id": task["id"],
        "returncode": returncode,
    }


def run_auto_once(agents: list[str], dry_run: bool = False, timeout: int = 1800, task_id: str = "") -> list[dict[str, Any]]:
    results = []
    for task in runnable_tasks(agents, task_id):
        results.append(run_agent_task(task, task["assignee"], dry_run=dry_run, timeout=timeout))
    return results
