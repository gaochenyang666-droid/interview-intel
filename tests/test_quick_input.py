from __future__ import annotations

import argparse
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from intel_core import IntelValidationError, build_plan, validate_research, render_report
from interview_intel import _quick_request
from test_interview_intel import complete_research


def args(value=None, **fields):
    defaults = {"input": value, "country": "0", "company": "0",
                "role": "0", "interviewer": "0"}
    defaults.update(fields)
    return argparse.Namespace(**defaults)


class QuickInputTests(unittest.TestCase):
    def test_slash_four_fields(self):
        req = _quick_request(args("中国/字节跳动/产品运营/0"))
        self.assertTrue(req["quick_mode"])
        self.assertEqual(req["company"]["name"], "字节跳动")
        self.assertEqual(req["role"]["title"], "产品运营")
        self.assertEqual(req["interviewers"], [])
        plan = build_plan(req)
        self.assertEqual(plan["country_code"], "CN")
        self.assertIn("zh", plan["languages_planned"])
        self.assertEqual(plan["request"]["interviewers"], [])

    def test_named_lines_and_missing_country(self):
        req = _quick_request(args("国家：0\n公司：Microsoft\n岗位：Software Engineer\n面试官：0"))
        plan = build_plan(req)
        self.assertIsNone(plan["country_code"])
        self.assertEqual(plan["request"]["company"]["name"], "Microsoft")
        self.assertFalse(any(q["category"].startswith("local") for q in plan["queries"]))

    def test_all_unknown_rejected(self):
        with self.assertRaisesRegex(IntelValidationError, "至少需要"):
            build_plan(_quick_request(args("0/0/0/0")))

    def test_country_only_rejected(self):
        with self.assertRaises(IntelValidationError):
            build_plan(_quick_request(args("中国/0/0/0")))

    def test_role_only(self):
        plan = build_plan(_quick_request(args("中国/0/产品运营/0")))
        self.assertIsNone(plan["request"]["company"]["name"])
        self.assertEqual(plan["entity_resolution"]["status"], "not_applicable")
        categories = [q["category"] for q in plan["queries"]]
        self.assertIn("role_jobs", categories)
        self.assertNotIn("company_official", categories)
        self.assertIn("zh", plan["languages_planned"])

    def test_company_only(self):
        plan = build_plan(_quick_request(args("中国/字节跳动/0/0")))
        self.assertIsNone(plan["request"]["role"]["title"])
        categories = [q["category"] for q in plan["queries"]]
        self.assertIn("company_official", categories)
        self.assertNotIn("role_interview", categories)
        self.assertNotIn("role_market", categories)

    def test_interviewer_only(self):
        plan = build_plan(_quick_request(args("0/0/0/张三")))
        self.assertEqual(plan["entity_resolution"]["status"], "not_applicable")
        self.assertEqual(plan["request"]["interviewers"][0]["name"], "张三")
        categories = [q["category"] for q in plan["queries"]]
        self.assertIn("interviewer_identity", categories)
        self.assertNotIn("company_official", categories)

    def test_flag_arguments(self):
        plan = build_plan(_quick_request(args(country="JP", company="Toyota", role="0", interviewer="0")))
        self.assertEqual(plan["country_code"], "JP")
        self.assertIsNone(plan["request"]["role"]["title"])

    def test_quick_report_skips_interviewer_section(self):
        data = complete_research()
        data["request"]["quick_mode"] = True
        data["request"]["interviewers"] = []
        report = render_report(data)
        self.assertIn("1. 公司概况与综合评价", report)
        self.assertIn("3. 岗位评价", report)
        self.assertNotIn("## 4. HR / 面试官公开情报", report)

    def test_quick_report_skips_absent_role(self):
        data = complete_research()
        data["request"]["quick_mode"] = True
        data["request"]["role"]["title"] = None
        data["request"]["interviewers"] = []
        data["interview_prep"]["mock_questions"] = []
        result = validate_research(data)
        self.assertEqual(result["request"]["role"]["title"], None)
        report = render_report(data)
        self.assertIn("1. 公司概况与综合评价", report)
        self.assertNotIn("## 3. 岗位评价", report)
        self.assertNotIn("## 5. 面试预测与准备", report)

    def test_quick_report_skips_absent_company(self):
        data = complete_research()
        data["request"]["quick_mode"] = True
        data["request"]["company"]["name"] = None
        data["request"]["interviewers"] = []
        data["research"]["entity"] = {"status": "not_applicable", "name": None, "basis": ""}
        report = render_report(data)
        self.assertNotIn("## 1. 公司概况与综合评价", report)
        self.assertNotIn("## 2. 员工及社交媒体评价", report)
        self.assertIn("## 3. 岗位评价", report)

    def test_legacy_report_keeps_structure(self):
        report = render_report(complete_research())
        for title in ["## 1. 公司概况与综合评价", "## 3. 岗位评价",
                      "## 4. HR / 面试官公开情报", "## 5. 面试预测与准备"]:
            self.assertIn(title, report)

    def test_bad_slash_format_rejected(self):
        with self.assertRaisesRegex(ValueError, "四段"):
            _quick_request(args("中国/字节跳动/产品运营"))


if __name__ == "__main__":
    unittest.main()
