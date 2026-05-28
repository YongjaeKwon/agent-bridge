from __future__ import annotations

import argparse
import json
import sys
import time

from config.settings import load_environment

from .agents import run_auto_once
from .integrations import create_github_issue, create_linear_issue, create_notion_meeting_page, post_slack_message
from .store import (
    add_event,
    add_meeting,
    create_task,
    ensure_store,
    list_meetings,
    list_tasks,
    update_meeting,
    update_task,
)


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecc", description="ECC collaboration harness CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create the local .ecc queue files")

    status = sub.add_parser("status", help="Show open work and recent activity")
    status.add_argument("--task-status", default="", help="Filter tasks by status")

    task = sub.add_parser("task", help="Create, list, claim, or complete tasks")
    task_sub = task.add_subparsers(dest="task_command", required=True)

    task_create = task_sub.add_parser("create")
    task_create.add_argument("--title", required=True)
    task_create.add_argument("--body", default="")
    task_create.add_argument("--assignee", default="")
    task_create.add_argument("--source", default="local")

    task_list = task_sub.add_parser("list")
    task_list.add_argument("--status", default="")

    task_claim = task_sub.add_parser("claim")
    task_claim.add_argument("task_id")
    task_claim.add_argument("--agent", required=True)

    task_done = task_sub.add_parser("done")
    task_done.add_argument("task_id")
    task_done.add_argument("--agent", required=True)
    task_done.add_argument("--summary", required=True)

    log = sub.add_parser("log", help="Append an agent work log")
    log.add_argument("--agent", required=True)
    log.add_argument("--message", required=True)
    log.add_argument("--task", default="")
    log.add_argument("--action", default="work.log")

    dispatch = sub.add_parser("dispatch", help="Assign open local tasks across agents")
    dispatch.add_argument("--agents", default="claude,codex")

    auto = sub.add_parser("auto", help="Run assigned tasks through local Claude/Codex CLI commands")
    auto.add_argument("--agents", default="claude,codex")
    auto.add_argument("--timeout", type=int, default=1800)
    auto.add_argument("--dry-run", action="store_true")
    auto.add_argument("--dispatch", action="store_true", help="Assign unassigned open tasks before each cycle")
    auto.add_argument("--loop", action="store_true", help="Keep polling for new assigned tasks")
    auto.add_argument("--interval", type=int, default=30)
    auto.add_argument("--max-cycles", type=int, default=1)

    meeting = sub.add_parser("meeting", help="Record meeting notes for Notion sync")
    meeting_sub = meeting.add_subparsers(dest="meeting_command", required=True)
    meeting_add = meeting_sub.add_parser("add")
    meeting_add.add_argument("--title", required=True)
    meeting_add.add_argument("--notes", required=True)
    meeting_add.add_argument("--participants", default="")
    meeting_add.add_argument("--agent", default="system")

    sync = sub.add_parser("sync", help="Write queued work to external tools")
    sync_sub = sync.add_subparsers(dest="sync_command", required=True)

    linear = sync_sub.add_parser("linear")
    linear.add_argument("--task", required=True)

    github = sync_sub.add_parser("github")
    github.add_argument("--task", required=True)

    notion = sync_sub.add_parser("notion")
    notion.add_argument("--meeting", required=True)

    slack = sync_sub.add_parser("slack")
    slack.add_argument("--message", required=True)
    slack.add_argument("--channel", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    load_environment()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        ensure_store()
        print_json({"ok": True, "message": "Initialized .ecc collaboration store"})
        return 0

    if args.command == "status":
        print_json({"tasks": list_tasks(args.task_status)})
        return 0

    if args.command == "task":
        if args.task_command == "create":
            print_json(create_task(args.title, args.body, args.assignee, args.source))
            return 0
        if args.task_command == "list":
            print_json(list_tasks(args.status))
            return 0
        if args.task_command == "claim":
            task = update_task(args.task_id, status="in_progress", assignee=args.agent)
            add_event(args.agent, "task.claim", f"Claimed {task['title']}", args.task_id)
            print_json(task)
            return 0
        if args.task_command == "done":
            task = update_task(args.task_id, status="done", assignee=args.agent, summary=args.summary)
            add_event(args.agent, "task.done", args.summary, args.task_id)
            print_json(task)
            return 0

    if args.command == "log":
        print_json(add_event(args.agent, args.action, args.message, args.task))
        return 0

    if args.command == "dispatch":
        agents = [agent.strip() for agent in args.agents.split(",") if agent.strip()]
        if not agents:
            raise ValueError("At least one agent is required")
        assigned = []
        for index, task in enumerate(task for task in list_tasks("open") if not task.get("assignee")):
            agent = agents[index % len(agents)]
            updated = update_task(task["id"], assignee=agent)
            add_event("system", "task.dispatch", f"Assigned to {agent}", task["id"])
            assigned.append(updated)
        print_json({"assigned": assigned})
        return 0

    if args.command == "auto":
        agents = [agent.strip() for agent in args.agents.split(",") if agent.strip()]
        cycles = 0
        all_results = []
        while True:
            cycles += 1
            if args.dispatch:
                for index, task in enumerate(task for task in list_tasks("open") if not task.get("assignee")):
                    agent = agents[index % len(agents)]
                    update_task(task["id"], assignee=agent)
                    add_event("system", "task.dispatch", f"Assigned to {agent}", task["id"])
            all_results.extend(run_auto_once(agents, dry_run=args.dry_run, timeout=args.timeout))
            if not args.loop or cycles >= args.max_cycles:
                break
            time.sleep(args.interval)
        print_json({"cycles": cycles, "results": all_results})
        return 0

    if args.command == "meeting" and args.meeting_command == "add":
        print_json(add_meeting(args.title, args.notes, args.participants, args.agent))
        return 0

    if args.command == "sync":
        if args.sync_command in {"linear", "github"}:
            task = next((item for item in list_tasks() if item["id"] == args.task), None)
            if not task:
                raise KeyError(f"Unknown task id: {args.task}")
            if args.sync_command == "linear":
                url = create_linear_issue(task["title"], task["body"])
                task = update_task(task["id"], linear_id=url)
                add_event("system", "sync.linear", url, task["id"])
                print_json(task)
                return 0
            url = create_github_issue(task["title"], task["body"])
            task = update_task(task["id"], github_issue=url)
            add_event("system", "sync.github", url, task["id"])
            print_json(task)
            return 0

        if args.sync_command == "notion":
            meeting = next((item for item in list_meetings() if item["id"] == args.meeting), None)
            if not meeting:
                raise KeyError(f"Unknown meeting id: {args.meeting}")
            url = create_notion_meeting_page(meeting["title"], meeting["notes"], meeting["participants"])
            meeting = update_meeting(meeting["id"], notion_page=url)
            add_event("system", "sync.notion", url)
            print_json(meeting)
            return 0

        if args.sync_command == "slack":
            ts = post_slack_message(args.message, args.channel)
            event = add_event("system", "sync.slack", f"posted:{ts}")
            print_json(event)
            return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
