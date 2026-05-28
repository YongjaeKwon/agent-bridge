from __future__ import annotations

from collections import defaultdict
from typing import Any

from .agent_config import list_agent_definitions
from .i18n import locale
from .store import EVENTS_FILE, add_meeting, list_tasks, read_jsonl


KO = {
    "title": "\u0045\u0043\u0043 \uc5d0\uc774\uc804\ud2b8 \ud68c\uc758\ub85d",
    "scope": "\ubc94\uc704",
    "task_scope": "\uc791\uc5c5 \ubc94\uc704",
    "all_work": "\uc804\uccb4 \ucd5c\uadfc/\uc9c4\ud589 \uc791\uc5c5",
    "tasks_included": "\ud3ec\ud568\ub41c \uc791\uc5c5 \uc218",
    "progress": "\uc9c4\ud589 \ud604\ud669",
    "contributions": "\uc5d0\uc774\uc804\ud2b8\ubcc4 \uc758\uacac\uacfc \uae30\uc5ec",
    "role": "\uc5ed\ud560",
    "decisions": "\uacb0\uc815 \uc0ac\ud56d\uacfc \uadfc\uac70",
    "no_decisions": "\uba85\uc2dc\uc801\uc73c\ub85c \uae30\ub85d\ub41c \uacb0\uc815\uc740 \uc5c6\uc2b5\ub2c8\ub2e4. \uc5d0\uc774\uc804\ud2b8\ubcc4 \uae30\uc5ec\uc5d0\uc11c \uc554\ubb35\uc801 \uc120\ud0dd\uc744 \ud655\uc778\ud558\uc138\uc694.",
    "blockers": "\u0042\u006c\u006f\u0063\u006b\u0065\u0072\uc640 \uc704\ud5d8 \uc694\uc18c",
    "no_blockers": "\uae30\ub85d\ub41c blocker\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",
    "outcomes": "\uacb0\uacfc",
    "no_done": "\uc774 \ubc94\uc704\uc5d0\uc11c \uc644\ub8cc \ucc98\ub9ac\ub41c \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.",
    "next": "\ub2e4\uc74c \uc561\uc158",
    "no_next": "\uc774 \ubc94\uc704\uc5d0\uc11c \uc5f4\ub9b0 \ud6c4\uc18d \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.",
}


def _bullet(value: str) -> str:
    cleaned = value.strip().replace("\n", " ")
    return f"- {cleaned}" if cleaned else "-"


def _heading(en: str, ko_key: str, korean: bool) -> str:
    return f"## {KO[ko_key]}" if korean else f"## {en}"


def build_agent_digest(task_id: str = "", limit: int = 80) -> str:
    korean = locale() == "ko"
    tasks = list_tasks()
    if task_id:
        tasks = [task for task in tasks if task.get("id") == task_id or task.get("parent_task_id") == task_id]
    task_ids = {task.get("id", "") for task in tasks}
    events = read_jsonl(EVENTS_FILE)
    if task_id:
        events = [event for event in events if event.get("task_id") in task_ids]
    events = events[-limit:]

    agent_roles = {agent.id: agent.role for agent in list_agent_definitions()}
    events_by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        events_by_agent[event.get("agent", "system")].append(event)

    title = KO["title"] if korean else "ECC Agent Meeting Digest"
    scope = task_id or (KO["all_work"] if korean else "all active/recent work")
    lines = [
        f"# {title}",
        "",
        _heading("Scope", "scope", korean),
        _bullet(f"{KO['task_scope'] if korean else 'Task scope'}: {scope}"),
        _bullet(f"{KO['tasks_included'] if korean else 'Tasks included'}: {len(tasks)}"),
        "",
        _heading("Progress Snapshot", "progress", korean),
    ]
    for task in tasks:
        lines.append(_bullet(f"{task.get('id')} [{task.get('status')}] {task.get('assignee') or 'unassigned'} - {task.get('title')}"))

    lines.extend(["", _heading("Agent Contributions", "contributions", korean)])
    for agent, agent_events in sorted(events_by_agent.items()):
        role = agent_roles.get(agent, "system or external event")
        lines.extend(["", f"### {agent}", _bullet(f"{KO['role'] if korean else 'Role'}: {role}")])
        for event in agent_events[-12:]:
            lines.append(_bullet(f"{event.get('action')} {event.get('task_id')}: {event.get('message')}"))

    decisions = [
        event
        for event in events
        if event.get("action") in {"decision", "meeting.decision"} or "decision" in event.get("message", "").lower()
    ]
    blockers = [
        event
        for event in events
        if event.get("action") in {"blocker", "auto.timeout", "auto.command_missing"} or "block" in event.get("message", "").lower()
    ]
    done_tasks = [task for task in tasks if task.get("status") == "done"]
    open_tasks = [task for task in tasks if task.get("status") != "done"]

    lines.extend(["", _heading("Decisions And Rationale", "decisions", korean)])
    if decisions:
        for event in decisions:
            lines.append(_bullet(f"{event.get('agent')}: {event.get('message')}"))
    else:
        lines.append(f"- {KO['no_decisions']}" if korean else "- No explicit decisions were logged. Review agent contributions for implicit choices.")

    lines.extend(["", _heading("Blockers And Risks", "blockers", korean)])
    if blockers:
        for event in blockers:
            lines.append(_bullet(f"{event.get('agent')}: {event.get('message')}"))
    else:
        lines.append(f"- {KO['no_blockers']}" if korean else "- No blockers were logged.")

    lines.extend(["", _heading("Outcomes", "outcomes", korean)])
    if done_tasks:
        for task in done_tasks:
            lines.append(_bullet(f"{task.get('title')}: {task.get('summary') or 'completed'}"))
    else:
        lines.append(f"- {KO['no_done']}" if korean else "- No tasks were marked done in this scope.")

    lines.extend(["", _heading("Next Actions", "next", korean)])
    if open_tasks:
        for task in open_tasks:
            lines.append(_bullet(f"{task.get('assignee') or 'unassigned'}: continue {task.get('id')} - {task.get('title')}"))
    else:
        lines.append(f"- {KO['no_next']}" if korean else "- No open follow-up tasks in this scope.")

    return "\n".join(lines).strip() + "\n"


def add_meeting_digest(title: str = "ECC Agent Meeting Digest", task_id: str = "", agent: str = "system") -> dict[str, Any]:
    notes = build_agent_digest(task_id)
    participants = ", ".join(agent.id for agent in list_agent_definitions() if agent.enabled)
    return add_meeting(title, notes, participants, agent)
