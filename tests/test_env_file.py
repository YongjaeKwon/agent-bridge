from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ecc_harness.env_file import read_env_file, write_env_values
from ecc_harness.store import read_jsonl


class EnvFileTest(unittest.TestCase):
    def test_write_env_values_preserves_comments_and_updates_existing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("# comment\nGITHUB_TOKEN=old\nLINEAR_API_KEY=lin\n", encoding="utf-8")

            write_env_values({"GITHUB_TOKEN": "new", "NOTION_TOKEN": "ntn"}, path)

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "# comment\nGITHUB_TOKEN=new\nLINEAR_API_KEY=lin\nNOTION_TOKEN=ntn\n",
            )
            self.assertEqual(read_env_file(path)["GITHUB_TOKEN"], "new")

    def test_read_jsonl_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_bytes(b"\xef\xbb\xbf" + '{"ok": true}\n'.encode("utf-8"))

            self.assertEqual(read_jsonl(path), [{"ok": True}])


if __name__ == "__main__":
    unittest.main()
