"""Distribution manifest and source integrity checks (no network required)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DistributionTests(unittest.TestCase):
    def test_manifests_are_valid(self):
        for path in ["gemini-extension.json", "plugin.json",
                     ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                     ".cursor-plugin/marketplace.json"]:
            with self.subTest(path=path):
                data = json.loads((ROOT / path).read_text(encoding="utf-8"))
                self.assertTrue(data.get("name"))
                if path.endswith("marketplace.json"):
                    self.assertEqual(len(data["plugins"]), 1)
                    self.assertEqual(data["plugins"][0]["source"], "./")
                else:
                    self.assertEqual(data["name"], "interview-intel")
    def test_portable_skill_references_canonical_skill(self):
        wrapper = ROOT / "skills" / "interview-intel" / "SKILL.md"
        content = wrapper.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\nname: interview-intel\n"))
        self.assertIn("../../SKILL.md", content)
        for relative in ["../../SKILL.md","../../scripts/interview_intel.py",
                         "../../scripts/interview_simulator.py",
                         "../../references/interview-practice.md"]:
            self.assertTrue((wrapper.parent / relative).exists(), relative)
        self.assertIn("at least two", content)
        self.assertIn("no individual interviewer profiling", content)
    def test_distribution_docs_reference_original_repo(self):
        text = (ROOT / "PUBLISHING.md").read_text(encoding="utf-8")
        self.assertIn("gaochenyang666-droid/interview-intel", text)
        self.assertIn("gemini-cli-extension", text)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("interview-practice.md", readme)
        self.assertIn("0.2.0-beta.1", readme)


if __name__ == "__main__":
    unittest.main()
