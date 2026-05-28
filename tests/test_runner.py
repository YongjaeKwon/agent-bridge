from __future__ import annotations

import unittest
from unittest.mock import mock_open, patch

from ecc_harness.runner import start_auto_process


class RunnerTest(unittest.TestCase):
    @patch("ecc_harness.runner.add_event")
    @patch("ecc_harness.runner.subprocess.Popen")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_start_auto_process_runs_task_with_assigned_agent(self, open_mock, popen_mock, add_event_mock) -> None:
        popen_mock.return_value.pid = 123

        result = start_auto_process("task-123", "planner")

        command = popen_mock.call_args.args[0]
        self.assertIn("ecc.py", command)
        self.assertIn("--task", command)
        self.assertIn("task-123", command)
        self.assertIn("--agents", command)
        self.assertIn("planner", command)
        self.assertEqual(result["pid"], "123")
        add_event_mock.assert_called()

    @patch("ecc_harness.runner.get_env")
    @patch("ecc_harness.runner.add_event")
    @patch("ecc_harness.runner.subprocess.Popen")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_start_auto_process_uses_loop_env_limits(
        self,
        open_mock,
        popen_mock,
        add_event_mock,
        get_env_mock,
    ) -> None:
        get_env_mock.side_effect = lambda name, default="": {"ECC_AUTO_LOOP_CYCLES": "3", "ECC_AUTO_LOOP_INTERVAL": "7"}.get(name, default)
        popen_mock.return_value.pid = 123

        start_auto_process(dispatch=True, loop=True)

        command = popen_mock.call_args.args[0]
        self.assertIn("--max-cycles", command)
        self.assertIn("3", command)
        self.assertIn("--interval", command)
        self.assertIn("7", command)


if __name__ == "__main__":
    unittest.main()
