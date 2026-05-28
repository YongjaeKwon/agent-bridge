from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from ecc_harness.ui import app


class UiTest(unittest.TestCase):
    @patch("ecc_harness.ui.start_auto_process")
    @patch("ecc_harness.ui.create_planner_request")
    def test_launch_creates_request_and_starts_planner_and_workers(self, create_request_mock, start_auto_mock) -> None:
        create_request_mock.return_value = {"id": "task-123", "title": "Planner request"}
        start_auto_mock.side_effect = [
            {"pid": "1", "log": "planner.log", "command": "planner"},
            {"pid": "2", "log": "loop.log", "command": "loop"},
        ]

        response = TestClient(app).post("/api/launch", json={"goal": "Build the product"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task"]["id"], "task-123")
        self.assertEqual(start_auto_mock.call_count, 2)
        start_auto_mock.assert_any_call("task-123", "planner", False, False)
        start_auto_mock.assert_any_call("", "", True, True)

    def test_launch_requires_goal(self) -> None:
        response = TestClient(app).post("/api/launch", json={"goal": "   "})

        self.assertEqual(response.status_code, 400)

    @patch("ecc_harness.ui.add_meeting_digest")
    def test_meeting_digest_endpoint(self, digest_mock) -> None:
        digest_mock.return_value = {"id": "mtg-1", "title": "Digest"}

        response = TestClient(app).post("/api/meeting/digest", json={"title": "Digest", "task_id": "task-1"})

        self.assertEqual(response.status_code, 200)
        digest_mock.assert_called_once_with("Digest", "task-1", "ui")

    def test_state_exposes_locale_messages(self) -> None:
        response = TestClient(app).get("/api/state")

        self.assertEqual(response.status_code, 200)
        self.assertIn("locale", response.json())
        self.assertIn("messages", response.json())


if __name__ == "__main__":
    unittest.main()
