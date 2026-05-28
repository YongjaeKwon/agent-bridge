from __future__ import annotations

import unittest
from unittest.mock import patch

from ecc_harness.task_ops import create_detailed_task


class TaskOpsTest(unittest.TestCase):
    @patch("ecc_harness.task_ops.add_event")
    @patch("ecc_harness.task_ops.update_task")
    @patch("ecc_harness.task_ops.create_task")
    @patch("ecc_harness.task_ops.list_tasks")
    @patch("ecc_harness.task_ops.create_linear_issue_record")
    def test_create_detailed_task_syncs_linear_sub_issue(
        self,
        create_linear_issue_record_mock,
        list_tasks_mock,
        create_task_mock,
        update_task_mock,
        add_event_mock,
    ) -> None:
        list_tasks_mock.return_value = [{"id": "task-parent", "linear_issue_id": "lin-parent"}]
        create_task_mock.return_value = {"id": "task-child", "title": "Child", "body": "Body"}
        update_task_mock.side_effect = [
            {"id": "task-child", "title": "Child", "body": "Body", "parent_linear_issue_id": "lin-parent"},
            {"id": "task-child", "linear_issue_id": "lin-child"},
        ]
        create_linear_issue_record_mock.return_value = {
            "id": "lin-child",
            "identifier": "YON-20",
            "url": "https://linear.app/test/issue/YON-20/child",
        }

        task = create_detailed_task("Child", "Body", "codex", "test", True, "task-parent")

        self.assertEqual(task["linear_issue_id"], "lin-child")
        _, kwargs = create_linear_issue_record_mock.call_args
        self.assertEqual(kwargs["parent_id"], "lin-parent")
        add_event_mock.assert_called()


if __name__ == "__main__":
    unittest.main()
