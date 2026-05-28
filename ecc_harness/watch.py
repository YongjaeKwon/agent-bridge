from __future__ import annotations

import os
import shutil
import time
from collections import defaultdict
from textwrap import shorten

from .agent_config import list_agent_definitions
from .store import EVENTS_FILE, list_tasks, read_jsonl


def _clear_screen() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def _fit(value: str, width: int) -> str:
    if width <= 3:
        return value[:width]
    return shorten(value.replace("\n", " "), width=width, placeholder="...")


def _agent_ids(requested: str) -> list[str]:
    configured = [agent.id for agent in list_agent_definitions() if agent.enabled]
    if requested:
        return [item.strip() for item in requested.split(",") if item.strip()]
    return configured


def render_dashboard(agents: list[str], limit: int = 8) -> str:
    width = shutil.get_terminal_size((120, 30)).columns
    events = read_jsonl(EVENTS_FILE)
    tasks = list_tasks()
    tasks_by_agent: dict[str, list[dict[str, str]]] = defaultdict(list)
    events_by_agent: dict[str, list[dict[str, str]]] = defaultdict(list)

    for task in tasks:
        assignee = task.get("assignee") or "unassigned"
        tasks_by_agent[assignee].append(task)
    for event in events:
        events_by_agent[event.get("agent", "system")].append(event)

    panel_width = max(32, min(54, (width - 4) // max(1, min(3, len(agents)))))
    lines = [
        "ECC multi-agent view",
        "Press Ctrl+C to stop. Run auto loop in another terminal/cmd window.",
        "",
    ]

    for agent in agents:
        lines.append("=" * panel_width)
        lines.append(_fit(f"{agent}", panel_width))
        lines.append("- tasks")
        agent_tasks = tasks_by_agent.get(agent, [])
        if not agent_tasks:
            lines.append("  (no assigned tasks)")
        for task in agent_tasks[-limit:]:
            lines.append(
                "  "
                + _fit(
                    f"{task.get('status', '')} {task.get('id', '')} {task.get('title', '')}",
                    panel_width - 2,
                )
            )
        lines.append("- events")
        agent_events = events_by_agent.get(agent, [])
        if not agent_events:
            lines.append("  (no events)")
        for event in agent_events[-limit:]:
            lines.append(
                "  "
                + _fit(
                    f"{event.get('action', '')} {event.get('task_id', '')} {event.get('message', '')}",
                    panel_width - 2,
                )
            )
        lines.append("")

    unassigned = tasks_by_agent.get("unassigned", [])
    if unassigned:
        lines.append("=" * panel_width)
        lines.append("unassigned")
        for task in unassigned[-limit:]:
            lines.append("  " + _fit(f"{task.get('status', '')} {task.get('id', '')} {task.get('title', '')}", panel_width - 2))

    return "\n".join(lines)


def watch_dashboard(agents: str = "", interval: float = 2.0, limit: int = 8, once: bool = False) -> None:
    selected_agents = _agent_ids(agents)
    while True:
        _clear_screen()
        print(render_dashboard(selected_agents, limit=limit), flush=True)
        if once:
            return
        time.sleep(interval)
