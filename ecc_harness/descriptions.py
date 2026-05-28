from __future__ import annotations

from .i18n import section_labels

DETAIL_HEADINGS = ("## Goal", "## Context", "## Deliverables", "## Acceptance Criteria", "## 목표", "## 배경", "## 산출물", "## 완료 기준")


def is_detailed_description(body: str) -> bool:
    return any(heading in body for heading in DETAIL_HEADINGS)


def format_task_description(title: str, body: str, assignee: str = "", source: str = "") -> str:
    cleaned = body.strip()
    if is_detailed_description(cleaned):
        return cleaned

    labels = section_labels()
    assignee_text = assignee or "unassigned"
    source_text = source or "local"
    context = cleaned or "No extra context was provided. Clarify scope before implementation if needed."
    return f"""## {labels["goal"]}
{title}

## {labels["context"]}
{context}

## {labels["owner"]}
{assignee_text}

## {labels["source"]}
{source_text}

## {labels["deliverables"]}
- Concrete implementation or planning output needed to satisfy the goal.
- Work log entries that explain important decisions and blockers.
- Follow-up tasks for any work that should be delegated.

## {labels["acceptance"]}
- Scope is clear enough for the assigned agent to start without guessing.
- Relevant files, commands, tickets, or verification steps are recorded in the work log.
- The task is marked done with a useful summary, or blocked with a specific reason.
"""


def planner_request_description(goal: str) -> str:
    labels = section_labels()
    return f"""## {labels["goal"]}
{goal}

## {labels["context"]}
This is a top-level user request. The Claude planner owns clarification, planning, and task decomposition.

## {labels["planner_instructions"]}
- Break the request into concrete subagent tasks.
- Assign each task to a configured agent id.
- Each delegated task must include Goal, Context, Deliverables, Acceptance Criteria, and Suggested Verification.
- Sync meaningful tasks to Linear so they do not remain title-only backlog items.

## {labels["acceptance"]}
- The planner creates detailed downstream work items.
- Each work item has enough description for another agent or human to understand why it exists.
- Blockers, assumptions, and handoffs are logged.
"""
