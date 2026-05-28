from __future__ import annotations

import unittest
from unittest.mock import patch

from ecc_harness.meetings import build_agent_digest


class MeetingsTest(unittest.TestCase):
    @patch("ecc_harness.meetings.list_agent_definitions")
    @patch("ecc_harness.meetings.read_jsonl")
    @patch("ecc_harness.meetings.list_tasks")
    def test_build_agent_digest_includes_agent_views_and_next_actions(
        self,
        list_tasks_mock,
        read_jsonl_mock,
        list_agents_mock,
    ) -> None:
        class Agent:
            def __init__(self, id: str, role: str) -> None:
                self.id = id
                self.role = role
                self.enabled = True

        list_agents_mock.return_value = [Agent("planner", "PM"), Agent("codex", "Implementation")]
        list_tasks_mock.return_value = [
            {"id": "task-1", "status": "in_progress", "assignee": "planner", "title": "Plan", "summary": ""},
            {"id": "task-2", "status": "done", "assignee": "codex", "title": "Build", "summary": "Built it"},
        ]
        read_jsonl_mock.return_value = [
            {"agent": "planner", "action": "decision", "task_id": "task-1", "message": "Use Linear sub-issues."},
            {"agent": "codex", "action": "work.log", "task_id": "task-2", "message": "Implemented sync."},
        ]

        digest = build_agent_digest()

        self.assertIn("## Agent Contributions", digest)
        self.assertIn("### planner", digest)
        self.assertIn("Use Linear sub-issues", digest)
        self.assertIn("## Decisions And Rationale", digest)
        self.assertIn("## Next Actions", digest)

    @patch("ecc_harness.meetings.locale")
    @patch("ecc_harness.meetings.list_agent_definitions")
    @patch("ecc_harness.meetings.read_jsonl")
    @patch("ecc_harness.meetings.list_tasks")
    def test_build_agent_digest_supports_korean_locale(
        self,
        list_tasks_mock,
        read_jsonl_mock,
        list_agents_mock,
        locale_mock,
    ) -> None:
        locale_mock.return_value = "ko"
        list_tasks_mock.return_value = []
        read_jsonl_mock.return_value = []
        list_agents_mock.return_value = []

        digest = build_agent_digest()

        self.assertIn("회의록", digest)
        self.assertIn("범위", digest)


if __name__ == "__main__":
    unittest.main()
