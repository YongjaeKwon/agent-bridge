from __future__ import annotations

from typing import Any

from config.settings import get_env

from .descriptions import format_task_description, planner_request_description
from .integrations import create_linear_issue_record
from .store import add_event, create_task, list_tasks, update_task


def should_auto_sync_linear() -> bool:
    value = get_env("ECC_AUTO_SYNC_LINEAR", "true").lower()
    return value not in {"0", "false", "no", "off"}


def create_detailed_task(
    title: str,
    body: str,
    assignee: str = "",
    source: str = "local",
    sync_linear: bool = False,
    parent_task_id: str = "",
) -> dict[str, Any]:
    detailed_body = format_task_description(title, body, assignee, source)
    task = create_task(title, detailed_body, assignee, source)
    parent_linear_issue_id = ""
    if parent_task_id:
        parent = next((item for item in list_tasks() if item["id"] == parent_task_id), None)
        if parent:
            parent_linear_issue_id = parent.get("linear_issue_id", "")
            task = update_task(task["id"], parent_task_id=parent_task_id, parent_linear_issue_id=parent_linear_issue_id)
    if sync_linear:
        try:
            issue = create_linear_issue_record(task["title"], task["body"], parent_id=parent_linear_issue_id)
            task = update_task(
                task["id"],
                linear_id=issue.get("url", ""),
                linear_issue_id=issue.get("id", ""),
                linear_identifier=issue.get("identifier", ""),
            )
            add_event("system", "sync.linear", issue.get("url", "") or issue.get("identifier", ""), task["id"])
        except Exception as exc:
            add_event("system", "sync.linear.failed", str(exc), task["id"])
    return task


def create_planner_request(goal: str, source: str = "user-request", sync_linear: bool = False) -> dict[str, Any]:
    title = f"Planner request: {goal[:80]}"
    return create_detailed_task(title, planner_request_description(goal), "planner", source, sync_linear)
