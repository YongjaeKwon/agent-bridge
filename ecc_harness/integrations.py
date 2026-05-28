from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any

from config.settings import get_env, get_token


def request_json(url: str, headers: dict[str, str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if payload is None else "POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned HTTP {exc.code}: {body}") from exc


def infer_github_repository() -> str:
    configured = get_env("GITHUB_REPOSITORY")
    if configured:
        return configured

    try:
        remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

    if remote.startswith("git@github.com:"):
        return remote.removeprefix("git@github.com:").removesuffix(".git")
    if "github.com/" in remote:
        return remote.split("github.com/", 1)[1].removesuffix(".git")
    return ""


def create_github_issue(title: str, body: str) -> str:
    token = get_token("GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN")
    repo = infer_github_repository()
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    if not repo:
        raise RuntimeError("Missing GITHUB_REPOSITORY and no GitHub origin remote was found")

    response = request_json(
        f"https://api.github.com/repos/{repo}/issues",
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ecc-harness",
        },
        {"title": title, "body": body},
    )
    return response.get("html_url", "")


def linear_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    token = get_env("LINEAR_API_KEY")
    if not token:
        raise RuntimeError("Missing LINEAR_API_KEY")
    response = request_json(
        "https://api.linear.app/graphql",
        {"Authorization": token, "Content-Type": "application/json"},
        {"query": query, "variables": variables},
    )
    if response.get("errors"):
        raise RuntimeError(json.dumps(response["errors"], ensure_ascii=False))
    return response["data"]


def get_linear_team_id() -> str:
    configured = get_env("LINEAR_TEAM_ID")
    if configured:
        return configured
    data = linear_graphql("query { teams { nodes { id name key } } }", {})
    teams = data["teams"]["nodes"]
    if len(teams) != 1:
        names = ", ".join(f"{team['key']}:{team['name']}" for team in teams)
        raise RuntimeError(f"Set LINEAR_TEAM_ID. Available teams: {names}")
    return teams[0]["id"]


def create_linear_issue(title: str, description: str) -> str:
    data = linear_graphql(
        """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            issue { identifier url }
          }
        }
        """,
        {"input": {"teamId": get_linear_team_id(), "title": title, "description": description}},
    )
    issue = data["issueCreate"]["issue"]
    return issue.get("url") or issue.get("identifier", "")


def create_notion_meeting_page(title: str, notes: str, participants: str = "") -> str:
    token = get_env("NOTION_TOKEN")
    parent_page_id = get_env("NOTION_PARENT_PAGE_ID")
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    if not parent_page_id:
        raise RuntimeError("Missing NOTION_PARENT_PAGE_ID")

    response = request_json(
        "https://api.notion.com/v1/pages",
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        {
            "parent": {"page_id": parent_page_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": participants}}]},
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": notes[:1900]}}]},
                },
            ],
        },
    )
    return response.get("url", "")


def post_slack_message(text: str, channel: str = "") -> str:
    token = get_env("SLACK_BOT_TOKEN")
    channel_id = channel or get_env("SLACK_DEFAULT_CHANNEL_ID")
    if not token:
        raise RuntimeError("Missing SLACK_BOT_TOKEN")
    if not channel_id:
        raise RuntimeError("Missing SLACK_DEFAULT_CHANNEL_ID")

    response = request_json(
        "https://slack.com/api/chat.postMessage",
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        {"channel": channel_id, "text": text},
    )
    if not response.get("ok"):
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    return response.get("ts", "")
