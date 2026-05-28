from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ECC_DIR = ROOT_DIR / ".ecc"
TASKS_FILE = ECC_DIR / "tasks.jsonl"
EVENTS_FILE = ECC_DIR / "events.jsonl"
MEETINGS_FILE = ECC_DIR / "meetings.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def ensure_store() -> None:
    ECC_DIR.mkdir(exist_ok=True)
    for path in (TASKS_FILE, EVENTS_FILE, MEETINGS_FILE):
        path.touch(exist_ok=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    ensure_store()
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    ensure_store()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_store()
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def add_event(agent: str, action: str, message: str, task_id: str = "") -> dict[str, Any]:
    return append_jsonl(
        EVENTS_FILE,
        {
            "id": short_id("evt"),
            "created_at": now(),
            "agent": agent,
            "action": action,
            "task_id": task_id,
            "message": message,
        },
    )


def create_task(title: str, body: str, assignee: str = "", source: str = "local") -> dict[str, Any]:
    task = {
        "id": short_id("task"),
        "created_at": now(),
        "updated_at": now(),
        "title": title,
        "body": body,
        "status": "open",
        "assignee": assignee,
        "source": source,
        "linear_id": "",
        "github_issue": "",
        "notion_page": "",
        "summary": "",
    }
    append_jsonl(TASKS_FILE, task)
    add_event(assignee or "system", "task.create", title, task["id"])
    return task


def list_tasks(status: str = "") -> list[dict[str, Any]]:
    tasks = read_jsonl(TASKS_FILE)
    if status:
        tasks = [task for task in tasks if task.get("status") == status]
    return tasks


def update_task(task_id: str, **changes: Any) -> dict[str, Any]:
    tasks = read_jsonl(TASKS_FILE)
    for task in tasks:
        if task["id"] == task_id:
            task.update(changes)
            task["updated_at"] = now()
            write_jsonl(TASKS_FILE, tasks)
            return task
    raise KeyError(f"Unknown task id: {task_id}")


def add_meeting(title: str, notes: str, participants: str = "", agent: str = "system") -> dict[str, Any]:
    meeting = {
        "id": short_id("mtg"),
        "created_at": now(),
        "title": title,
        "participants": participants,
        "notes": notes,
        "notion_page": "",
    }
    append_jsonl(MEETINGS_FILE, meeting)
    add_event(agent, "meeting.add", title)
    return meeting


def list_meetings() -> list[dict[str, Any]]:
    return read_jsonl(MEETINGS_FILE)


def update_meeting(meeting_id: str, **changes: Any) -> dict[str, Any]:
    meetings = read_jsonl(MEETINGS_FILE)
    for meeting in meetings:
        if meeting["id"] == meeting_id:
            meeting.update(changes)
            write_jsonl(MEETINGS_FILE, meetings)
            return meeting
    raise KeyError(f"Unknown meeting id: {meeting_id}")
