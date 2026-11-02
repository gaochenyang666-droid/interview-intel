from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from intel_core import IntelValidationError, build_plan, render_report, validate_research
from test_interview_intel import complete_research


class CommunityResearchTests(unittest.TestCase):
    def test_cn_plan_has_explicit_local_platform_queries(self):
        plan = build_plan({
            "company": {"name": "示例公司"},
            "role": {"title": "产品运营"},
            "location": {"country": "CN"},
        })
        queries = [q for q in plan["queries"] if q["category"] == "community_platform"]
        self.assertGreaterEqual(len(queries), 2)
        self.assertGreaterEqual(len({q["platform_ids"][0] for q in queries}), 2)
        self.assertTrue(any(q["language"] == "zh-Hans" for q in queries))
        self.assertTrue(all("site:" in q["query"] for q in queries))
        self.assertTrue(plan["scaffold"]["research"]["coverage"]["community_required"])

    def test_us_community_platform_queries(self):
        plan = build_plan({"company": {"name": "Microsoft"},
                           "role": {"title": "Engineer"},
                           "location": {"country": "US"}})
        self.assertGreaterEqual(len([
            q for q in plan["queries"] if q["category"] == "community_platform"
        ]), 2)
        self.assertIn("reddit", [x["platform_id"] for x in plan["community_targets"]])

    def test_low_query_budget_preserves_local_search(self):
        plan = build_plan({"company": {"name": "测试公司"},
                           "role": {"title": "客服"},
                           "location": {"country": "CN"},
                           "research": {"max_queries": 4}})
        self.assertLessEqual(len(plan["queries"]), 4)
        self.assertIn("zh-Hans", plan["languages_planned"])

    def test_live_company_research_requires_two_platform_attempts(self):
        data = complete_research()
        data["research"]["coverage"].update({"community_required": True, "community_attempts": []})
        with self.assertRaisesRegex(IntelValidationError, "两个独立平台"):
            validate_research(data)

    def test_explicit_access_failures_are_acceptable_not_employee_claims(self):
        data = complete_research()
        data["research"]["coverage"].update({
            "community_required": True,
            "community_attempts": [
                {"platform_id": "reddit", "query": 'site:reddit.com "Example Corp" experience',
                 "result": "no_results", "evidence_ids": []},
                {"platform_id": "glassdoor", "query": 'site:glassdoor.com "Example Corp" reviews',
                 "result": "login_required", "evidence_ids": []},
            ],
        })
        validate_research(data)
        report = render_report(data)
        self.assertIn("社交平台与职场社区检索情况", report)
        self.assertIn("需要登录", report)
        self.assertIn("未找到结果", report)

    def test_found_requires_opened_original_community_source(self):
        data = complete_research()
        data["research"]["coverage"].update({
            "community_required": True,
            "community_attempts": [
                {"platform_id": "reddit", "query": "reddit review",
                 "result": "found", "evidence_ids": ["E001"]},
                {"platform_id": "glassdoor", "query": "glassdoor review",
                 "result": "blocked", "evidence_ids": []},
            ],
        })
        with self.assertRaisesRegex(IntelValidationError, "原帖或员工评价证据"):
            validate_research(data)

    def test_found_community_source_is_linked_in_report(self):
        data = complete_research()
        data["research"]["coverage"].update({
            "community_required": True,
            "community_attempts": [
                {"platform_id": "reddit", "query": "reddit review",
                 "result": "found", "evidence_ids": ["E003"]},
                {"platform_id": "glassdoor", "query": "glassdoor review",
                 "result": "blocked", "evidence_ids": []},
            ],
        })
        validate_research(data)
        report = render_report(data)
        self.assertIn("[E003](#e003)", report)
        self.assertIn("| reddit | 已核实原帖 |", report)

    def test_one_platform_twice_is_not_independent(self):
        data = complete_research()
        data["research"]["coverage"].update({
            "community_required": True,
            "community_attempts": [
                {"platform_id": "reddit", "query": "review 1",
                 "result": "found", "evidence_ids": ["E003"]},
                {"platform_id": "reddit", "query": "review 2",
                 "result": "no_results", "evidence_ids": []},
            ],
        })
        with self.assertRaisesRegex(IntelValidationError, "两个不同的平台"):
            validate_research(data)

    def test_legacy_report_still_valid_no_attempts(self):
        data = complete_research()
        self.assertNotIn("community_required", data["research"]["coverage"])
        validate_research(data)
        report = render_report(data)
        self.assertIn("2. 员工及社交媒体评价", report)
        self.assertNotIn("面试机会评分", report)

    def test_company_missing_does_not_require_community(self):
        plan = build_plan({"company": {"name": None}, "role": {"title": "Engineer"}})
        self.assertFalse(plan["scaffold"]["research"]["coverage"]["community_required"])
        self.assertFalse(plan["community_targets"])


if __name__ == "__main__":
    unittest.main()
