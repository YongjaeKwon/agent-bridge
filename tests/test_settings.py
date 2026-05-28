from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from config.settings import get_token, mask_secret, missing_required_env


class SettingsTest(unittest.TestCase):
    def test_get_token_prefers_first_present_value(self) -> None:
        with patch.dict(os.environ, {"PRIMARY": "", "SECONDARY": "value"}, clear=True):
            self.assertEqual(get_token("PRIMARY", "SECONDARY"), "value")

    def test_missing_required_env_groups_by_integration(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            missing = missing_required_env()

        self.assertEqual(missing["github"], ["GITHUB_TOKEN"])
        self.assertEqual(missing["linear"], ["LINEAR_API_KEY"])
        self.assertEqual(missing["slack"], ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"])
        self.assertEqual(missing["notion"], ["NOTION_TOKEN"])

    def test_mask_secret_never_exposes_token_fragments(self) -> None:
        self.assertEqual(mask_secret("abcdefghijk"), "set")
        self.assertEqual(mask_secret("short"), "set")
        self.assertEqual(mask_secret(""), "")


if __name__ == "__main__":
    unittest.main()
