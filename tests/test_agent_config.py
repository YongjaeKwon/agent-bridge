from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ecc_harness.agent_config import all_agent_ids, get_agent_definition, worker_agent_ids


class AgentConfigTest(unittest.TestCase):
    def test_gemini_is_optional_until_command_is_set(self) -> None:
        with patch.dict(os.environ, {"ECC_GEMINI_COMMAND": ""}, clear=False):
            gemini = get_agent_definition("gemini")
            self.assertIsNotNone(gemini)
            assert gemini is not None
            self.assertTrue(gemini.optional)
            self.assertFalse(gemini.enabled)
            self.assertNotIn("gemini", all_agent_ids())
            self.assertNotIn("gemini", worker_agent_ids())

    def test_gemini_is_enabled_when_command_is_set(self) -> None:
        with patch.dict(os.environ, {"ECC_GEMINI_COMMAND": "gemini -p"}, clear=False):
            gemini = get_agent_definition("gemini")
            self.assertIsNotNone(gemini)
            assert gemini is not None
            self.assertTrue(gemini.enabled)
            self.assertIn("gemini", all_agent_ids())


if __name__ == "__main__":
    unittest.main()
