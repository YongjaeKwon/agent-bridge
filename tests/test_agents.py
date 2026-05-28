from __future__ import annotations

import unittest

from ecc_harness.agents import build_prompt


class AgentsTest(unittest.TestCase):
    def test_build_prompt_includes_required_handoff_commands(self) -> None:
        task = {"id": "task-123", "title": "Fix sync", "body": "Make auto loop reliable"}

        prompt = build_prompt(task, "codex")

        self.assertIn("python ecc.py task claim task-123 --agent codex", prompt)
        self.assertIn("python ecc.py log --agent codex --task task-123", prompt)
        self.assertIn("python ecc.py task done task-123 --agent codex", prompt)


if __name__ == "__main__":
    unittest.main()
