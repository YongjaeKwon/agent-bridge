from __future__ import annotations

import json
import sys
from typing import Any

from .agent_config import list_agent_definitions, main_agent_id
from .store import add_event, add_meeting, create_task, list_tasks, update_task


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        line = line.decode("utf-8").strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length).decode("utf-8")
    return json.loads(body)


def write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def tool_schema() -> list[dict[str, Any]]:
    return [
        {
            "name": "ecc_create_task",
            "description": "Create a local ECC task for Claude/Codex coordination.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "assignee": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["title"],
            },
        },
        {
            "name": "ecc_request",
            "description": "Send a top-level user request to the main planner agent.",
            "inputSchema": {
                "type": "object",
                "properties": {"goal": {"type": "string"}},
                "required": ["goal"],
            },
        },
        {
            "name": "ecc_list_agents",
            "description": "List configured ECC agents and their roles.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "ecc_list_tasks",
            "description": "List local ECC tasks, optionally filtered by status.",
            "inputSchema": {
                "type": "object",
                "properties": {"status": {"type": "string"}},
            },
        },
        {
            "name": "ecc_claim_task",
            "description": "Claim a task for an agent and mark it in progress.",
            "inputSchema": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}, "agent": {"type": "string"}},
                "required": ["task_id", "agent"],
            },
        },
        {
            "name": "ecc_complete_task",
            "description": "Mark a task done with a short completion summary.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "agent": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["task_id", "agent", "summary"],
            },
        },
        {
            "name": "ecc_log",
            "description": "Append an agent work log entry.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "message": {"type": "string"},
                    "task_id": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["agent", "message"],
            },
        },
        {
            "name": "ecc_add_meeting",
            "description": "Store meeting notes for later Notion sync.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "notes": {"type": "string"},
                    "participants": {"type": "string"},
                    "agent": {"type": "string"},
                },
                "required": ["title", "notes"],
            },
        },
    ]


def as_text(payload: object) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}]}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "ecc_create_task":
        return as_text(
            create_task(
                arguments["title"],
                arguments.get("body", ""),
                arguments.get("assignee", ""),
                arguments.get("source", "mcp"),
            )
        )
    if name == "ecc_request":
        return as_text(create_task(f"Planner request: {arguments['goal'][:80]}", arguments["goal"], main_agent_id(), "mcp-request"))
    if name == "ecc_list_agents":
        return as_text(
            [
                {
                    "id": agent.id,
                    "runner": agent.runner,
                    "role": agent.role,
                    "command_env": agent.command_env,
                    "main": agent.id == main_agent_id(),
                }
                for agent in list_agent_definitions()
            ]
        )
    if name == "ecc_list_tasks":
        return as_text(list_tasks(arguments.get("status", "")))
    if name == "ecc_claim_task":
        task = update_task(arguments["task_id"], status="in_progress", assignee=arguments["agent"])
        add_event(arguments["agent"], "task.claim", f"Claimed {task['title']}", arguments["task_id"])
        return as_text(task)
    if name == "ecc_complete_task":
        task = update_task(
            arguments["task_id"],
            status="done",
            assignee=arguments["agent"],
            summary=arguments["summary"],
        )
        add_event(arguments["agent"], "task.done", arguments["summary"], arguments["task_id"])
        return as_text(task)
    if name == "ecc_log":
        return as_text(
            add_event(
                arguments["agent"],
                arguments.get("action", "work.log"),
                arguments["message"],
                arguments.get("task_id", ""),
            )
        )
    if name == "ecc_add_meeting":
        return as_text(
            add_meeting(
                arguments["title"],
                arguments["notes"],
                arguments.get("participants", ""),
                arguments.get("agent", "mcp"),
            )
        )
    raise ValueError(f"Unknown tool: {name}")


def handle(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ecc-harness", "version": "0.1.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tool_schema()}}
    if method == "tools/call":
        params = request.get("params", {})
        try:
            result = call_tool(params["name"], params.get("arguments", {}))
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    while True:
        message = read_message()
        if message is None:
            return 0
        response = handle(message)
        if response is not None:
            write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
