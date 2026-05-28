from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from ecc_harness.agents import build_prompt, run_agent_task


class AgentsTest(unittest.TestCase):
    def test_build_prompt_includes_required_handoff_commands(self) -> None:
        task = {"id": "task-123", "title": "Fix sync", "body": "Make auto loop reliable"}

        with patch.dict(os.environ, {"ECC_COMPACT_PROMPTS": "false"}):
            prompt = build_prompt(task, "codex")

        self.assertIn("python ecc.py task claim task-123 --agent codex", prompt)
        self.assertIn("python ecc.py log --agent codex --task task-123", prompt)
        self.assertIn("python ecc.py task done task-123 --agent codex", prompt)

    def test_planner_prompt_requires_detailed_synced_tasks(self) -> None:
        task = {"id": "task-123", "title": "Plan work", "body": "Split the work"}

        with patch.dict(os.environ, {"ECC_COMPACT_PROMPTS": "false"}):
            prompt = build_prompt(task, "planner")

        self.assertIn("--sync-linear", prompt)
        self.assertIn("--parent-task task-123", prompt)
        self.assertIn("Acceptance Criteria", prompt)
        self.assertIn("Suggested Verification", prompt)
        self.assertIn("docs/ecc/plan.md", prompt)
        self.assertIn("Model policy", prompt)

    def test_compact_prompt_uses_context_file_instead_of_full_body(self) -> None:
        task = {"id": "task-123", "title": "Plan work", "body": "x" * 5000}

        with patch.dict(os.environ, {"ECC_COMPACT_PROMPTS": "true"}):
            prompt = build_prompt(task, "planner")

        self.assertIn("Context file:", prompt)
        self.assertIn("docs/ecc/plan.md", prompt)
        self.assertNotIn("x" * 100, prompt)
        self.assertLess(len(prompt), 1200)

    @patch("ecc_harness.agents.add_event")
    @patch("ecc_harness.agents.update_task")
    @patch("ecc_harness.agents.command_for")
    @patch("ecc_harness.agents.run_streaming_command")
    def test_run_agent_task_streams_output_instead_of_capturing(
        self,
        run_command_mock,
        command_for_mock,
        update_task_mock,
        add_event_mock,
    ) -> None:
        command_for_mock.return_value.command = ["codex", "exec"]
        run_command_mock.return_value = (0, "")
        task = {"id": "task-123", "title": "Fix sync", "body": ""}

        with redirect_stdout(io.StringIO()):
            result = run_agent_task(task, "codex")

        self.assertEqual(result["returncode"], 0)
        command = run_command_mock.call_args.args[0]
        self.assertIn(".ecc", command[-1])
        self.assertIn("Read the full UTF-8 task prompt", command[-1])

    @patch("ecc_harness.agents.add_event")
    @patch("ecc_harness.agents.update_task")
    @patch("ecc_harness.agents.command_for")
    @patch("ecc_harness.agents.run_streaming_command")
    def test_run_agent_task_marks_quota_failures_as_blocked(
        self,
        run_command_mock,
        command_for_mock,
        update_task_mock,
        add_event_mock,
    ) -> None:
        command_for_mock.return_value.command = ["codex", "exec"]
        run_command_mock.return_value = (1, "Error: insufficient_quota. You exceeded your current quota.")
        task = {"id": "task-123", "title": "Fix sync", "body": ""}

        with redirect_stdout(io.StringIO()):
            result = run_agent_task(task, "codex")

        self.assertEqual(result["returncode"], 1)
        update_task_mock.assert_any_call(
            "task-123",
            status="blocked",
            blocker_type="quota_exhausted",
            summary="Agent quota or paid usage limit is exhausted. Refill/upgrade/wait for reset, then rerun this task.",
        )
        add_event_mock.assert_any_call(
            "codex",
            "blocker.quota_exhausted",
            "Agent quota or paid usage limit is exhausted. Refill/upgrade/wait for reset, then rerun this task.",
            "task-123",
        )


if __name__ == "__main__":
    unittest.main()
