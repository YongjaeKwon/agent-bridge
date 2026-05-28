from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from ecc_harness.agents import build_prompt, run_agent_task


class AgentsTest(unittest.TestCase):
    def test_build_prompt_includes_required_handoff_commands(self) -> None:
        task = {"id": "task-123", "title": "Fix sync", "body": "Make auto loop reliable"}

        prompt = build_prompt(task, "codex")

        self.assertIn("python ecc.py task claim task-123 --agent codex", prompt)
        self.assertIn("python ecc.py log --agent codex --task task-123", prompt)
        self.assertIn("python ecc.py task done task-123 --agent codex", prompt)

    @patch("ecc_harness.agents.add_event")
    @patch("ecc_harness.agents.update_task")
    @patch("ecc_harness.agents.command_for")
    @patch("ecc_harness.agents.subprocess.run")
    def test_run_agent_task_streams_output_instead_of_capturing(
        self,
        run_mock,
        command_for_mock,
        update_task_mock,
        add_event_mock,
    ) -> None:
        command_for_mock.return_value.command = ["codex", "exec"]
        run_mock.return_value.returncode = 0
        task = {"id": "task-123", "title": "Fix sync", "body": ""}

        with redirect_stdout(io.StringIO()):
            result = run_agent_task(task, "codex")

        self.assertEqual(result["returncode"], 0)
        _, kwargs = run_mock.call_args
        self.assertNotIn("capture_output", kwargs)
        self.assertNotIn("stdout", kwargs)
        self.assertNotIn("stderr", kwargs)


if __name__ == "__main__":
    unittest.main()
