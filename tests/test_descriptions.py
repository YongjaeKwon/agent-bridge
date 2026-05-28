from __future__ import annotations

import unittest
from unittest.mock import patch

from ecc_harness.descriptions import format_task_description, planner_request_description


class DescriptionsTest(unittest.TestCase):
    def test_format_task_description_adds_linear_ready_sections(self) -> None:
        body = format_task_description("Fix portfolio copy", "Korean content is corrupted.", "codex", "test")

        self.assertIn("## Goal", body)
        self.assertIn("## Context", body)
        self.assertIn("## Deliverables", body)
        self.assertIn("## Acceptance Criteria", body)
        self.assertIn("codex", body)

    def test_planner_request_description_requires_detailed_downstream_tasks(self) -> None:
        body = planner_request_description("Improve the project")

        self.assertIn("Each delegated task must include", body)
        self.assertIn("Linear", body)

    @patch("ecc_harness.i18n.get_env")
    def test_format_task_description_supports_korean_locale(self, get_env_mock) -> None:
        get_env_mock.return_value = "ko"

        body = format_task_description("테스트", "본문", "planner", "test")

        self.assertIn("## 목표", body)
        self.assertIn("## 배경", body)


if __name__ == "__main__":
    unittest.main()
