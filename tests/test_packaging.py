"""Test exact ZIP root layout accepted by different Qwen skill uploaders."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from package_skill import package


class PackagingTests(unittest.TestCase):
    def test_qwen_ai_root_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "interview-intel-qwen.zip"
            count, size = package(dest, "qwen-ai")
            self.assertGreater(count, 5)
            self.assertLess(size, 10 * 1024 * 1024)
            with ZipFile(dest) as zipfile:
                paths = zipfile.namelist()
                self.assertIn("SKILL.md", paths)
                self.assertIn("scripts/interview_intel.py", paths)
                self.assertFalse(any(p.startswith("interview-intel/") for p in paths))
                self.assertFalse(any("__pycache__" in p for p in paths))

    def test_qwenwork_wrapper_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "interview-intel-qwenwork.zip"
            package(dest, "qwenwork")
            with ZipFile(dest) as zipfile:
                paths = zipfile.namelist()
                self.assertIn("interview-intel/SKILL.md", paths)
                self.assertNotIn("SKILL.md", paths)
                self.assertTrue(all(x.startswith("interview-intel/") for x in paths))


if __name__ == "__main__":
    unittest.main()
