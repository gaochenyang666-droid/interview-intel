from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from intel_core import IntelValidationError, build_plan, render_report, validate_research
from interview_questions import generate_question_bank
from test_interview_intel import complete_research


def researched_with_experiences() -> dict:
    data = copy.deepcopy(complete_research())
    data["evidence"].extend(
        [
            {
                "id": "E010",
                "title": "Example Corp Software Engineer interview account",
                "url": "https://interviews.example.org/example-corp/se",
                "platform": "Interview Forum",
                "source_type": "interview_report",
                "published_at": "2026-09-20",
                "published_at_precision": "day",
                "retrieved_at": "2026-11-02",
                "language": "en",
                "excerpt": "The candidate described a coding task and a service-design discussion.",
                "access_status": "verified",
                "independence_group": "example-se-interview-1",
                "supports": [],
                "limitations": "Single anonymous public account.",
            },
            {
                "id": "E011",
                "title": "Example Corp reliability engineer interview",
                "url": "https://interviews.example.org/example-corp/sre",
                "platform": "Interview Forum",
                "source_type": "interview_report",
                "published_at": "2026-08-15",
                "published_at_precision": "day",
                "retrieved_at": "2026-11-02",
                "language": "en",
                "excerpt": "The candidate discussed incident response and system tradeoffs.",
                "access_status": "verified",
                "independence_group": "example-sre-interview-1",
                "supports": [],
                "limitations": "Related role rather than exact role.",
            },
            {
                "id": "E012",
                "title": "Peer Corp software engineer interview",
                "url": "https://interviews.example.org/peer-corp/se",
                "platform": "Interview Forum",
                "source_type": "interview_report",
                "published_at": "2026-07-10",
                "published_at_precision": "day",
                "retrieved_at": "2026-11-02",
                "language": "en",
                "excerpt": "The interview included API design, caching, and failure recovery questions.",
                "access_status": "verified",
                "independence_group": "peer-se-interview-1",
                "supports": [],
                "limitations": "A different company with a related business and role.",
            },
            {
                "id": "E013",
                "title": "Peer Corp engineering overview",
                "url": "https://peer.example.com/engineering",
                "platform": "Peer Corp",
                "source_type": "official",
                "published_at": "2026-06-01",
                "published_at_precision": "day",
                "retrieved_at": "2026-11-02",
                "language": "en",
                "excerpt": "Peer Corp builds enterprise cloud software with a large backend engineering organization.",
                "access_status": "verified",
                "independence_group": "peer-company-overview",
                "supports": [],
                "limitations": "Used only to justify comparability.",
            },
        ]
    )
    data["similar_companies"] = [
        {
            "name": "Peer Corp",
            "match_rationale": "Both companies sell enterprise cloud software and hire backend platform engineers.",
            "evidence_ids": ["E013"],
        }
    ]
    data["interview_experiences"] = [
        {
            "id": "I001",
            "source_level": 1,
            "company": "Example Corp",
            "role": "Software Engineer",
            "country": "US",
            "city": "Test City",
            "level": "Mid-level",
            "published_at": "2026-09-20",
            "interview_date": "2026-09",
            "rounds": ["coding", "design"],
            "format": "video",
            "questions": [
                "Implement a cache with bounded memory and concurrency safety.",
                "How would you debug a service that intermittently returns stale data?",
            ],
            "difficulty": "moderate",
            "author_impression": "The coding interview was practical and test-focused.",
            "evidence_ids": ["E010"],
            "limitations": "One anonymous candidate account.",
        },
        {
            "id": "I002",
            "source_level": 2,
            "company": "Example Corp",
            "role": "Site Reliability Engineer",
            "role_relation": "The role shares backend reliability responsibilities with the target team.",
            "country": "US",
            "published_at": "2026-08-15",
            "interview_date": "2026-08",
            "format": "video",
            "questions": ["How do you respond when a dependency is slow during a production incident?"],
            "difficulty": "moderate",
            "author_impression": "The interviewer focused on incident tradeoffs.",
            "evidence_ids": ["E011"],
            "limitations": "Related role rather than the exact job.",
        },
        {
            "id": "I003",
            "source_level": 3,
            "company": "Peer Corp",
            "similar_company": "Peer Corp",
            "role": "Software Engineer",
            "match_rationale": "Both companies have enterprise cloud products and similar backend engineering scope.",
            "country": "US",
            "published_at": "2026-07-10",
            "interview_date": "2026-07",
            "format": "video",
            "questions": ["Design an API with idempotent retries and bounded latency."],
            "difficulty": "moderate",
            "evidence_ids": ["E012"],
            "limitations": "Company context differs; use as transferable practice only.",
        },
    ]
    data["summary"]["experience_note"] = (
        "找到一条本公司同岗位、一条相近岗位和一条相似公司面经；历史原题与迁移题已分别标注。"
    )
    data["interview_prep"]["questions"] = generate_question_bank(data)
    data["interview_prep"].pop("mock_questions", None)
    return data


class InterviewResearchTests(unittest.TestCase):
    def test_plan_contains_interview_tiers_and_dynamic_mix(self):
        plan = build_plan(
            {
                "company": {"name": "ByteDance", "industry": "Consumer internet"},
                "role": {"title": "Product Manager"},
                "location": {"country": "CN"},
            }
        )
        categories = {query["category"] for query in plan["queries"]}
        self.assertIn("interview_exact", categories)
        self.assertIn("interview_similar_role", categories)
        self.assertIn("interview_peer_discovery", categories)
        self.assertIn("interview_role_general", categories)
        self.assertEqual(
            plan["interview_strategy"]["selection_order"][0],
            "1_same_company_same_role_recent",
        )
        self.assertIn("product_sense", plan["interview_strategy"]["question_mix"])

    def test_interview_sources_are_present_in_catalog_routing(self):
        plan = build_plan(
            {
                "company": {"name": "Example Corp"},
                "role": {"title": "Software Engineer"},
                "location": {"country": "US"},
            }
        )
        source_ids = {item["id"] for item in plan["sources"]}
        self.assertIn("leetcode", source_ids)
        interview_query_platforms = {
            platform_id
            for query in plan["queries"]
            if query["category"].startswith("interview_")
            for platform_id in query.get("platform_ids", [])
        }
        self.assertIn("leetcode", interview_query_platforms)

    def test_exact_company_experience_is_used_first(self):
        data = researched_with_experiences()
        questions = data["interview_prep"]["questions"]
        self.assertEqual(len(questions), 10)
        self.assertEqual(questions[0]["source_level"], 1)
        self.assertEqual(questions[0]["origin_type"], "historical_exact")
        self.assertIn("cache", questions[0]["question"].casefold())

    def test_similar_company_is_labelled_and_requires_rationale(self):
        data = researched_with_experiences()
        similar = [
            item for item in data["interview_prep"]["questions"]
            if item["origin_type"] == "similar_company"
        ]
        self.assertTrue(similar)
        self.assertEqual(similar[0]["source_company"], "Peer Corp")
        self.assertIn("enterprise cloud", similar[0]["migration_rationale"])
        report = render_report(data)
        self.assertIn("相似公司参考题", report)
        self.assertIn("迁移限制", report)

    def test_similar_company_cannot_be_relabelled_as_exact(self):
        data = researched_with_experiences()
        data["interview_prep"]["questions"][0]["source_level"] = 4
        data["interview_prep"]["questions"][0]["origin_type"] = "historical_exact"
        with self.assertRaisesRegex(IntelValidationError, "source_level 与 origin_type 不一致"):
            validate_research(data)

    def test_related_role_requires_relation_rationale(self):
        data = researched_with_experiences()
        data["interview_experiences"][1].pop("role_relation")
        with self.assertRaisesRegex(IntelValidationError, "角色相关性"):
            validate_research(data)

    def test_historical_question_must_exist_in_linked_experience(self):
        data = researched_with_experiences()
        data["interview_prep"]["questions"][0]["question"] = (
            "This question was never present in the linked public interview report."
        )
        with self.assertRaisesRegex(IntelValidationError, "未在对应级别"):
            validate_research(data)

    def test_duplicate_questions_are_rejected(self):
        data = researched_with_experiences()
        data["interview_prep"]["questions"][1]["question"] = (
            data["interview_prep"]["questions"][0]["question"] + " "
        )
        with self.assertRaisesRegex(IntelValidationError, "重复"):
            validate_research(data)

    def test_question_categories_are_diverse(self):
        data = researched_with_experiences()
        categories = {
            item["category"] for item in data["interview_prep"]["questions"]
        }
        self.assertGreaterEqual(len(categories), 3)
        validate_research(data)

    def test_no_historical_questions_falls_back_to_predictions(self):
        data = copy.deepcopy(complete_research())
        data["interview_experiences"] = []
        data["interview_prep"]["questions"] = generate_question_bank(data)
        data["interview_prep"].pop("mock_questions", None)
        normalized = validate_research(data)
        self.assertTrue(all(item["source_level"] == 4 for item in normalized["interview_prep"]["questions"]))
        self.assertTrue(
            all(item["origin_type"] == "prediction" for item in normalized["interview_prep"]["questions"])
        )

    def test_process_only_experience_keeps_evidence_and_uses_predictions(self):
        data = researched_with_experiences()
        for experience in data["interview_experiences"]:
            experience["questions"] = []
        data["interview_prep"]["questions"] = generate_question_bank(data)
        data["interview_prep"].pop("mock_questions", None)
        normalized = validate_research(data)
        self.assertEqual(len(normalized["interview_experiences"]), 3)
        self.assertTrue(
            all(
                item["origin_type"] == "prediction"
                for item in normalized["interview_prep"]["questions"]
            )
        )

    def test_software_prediction_bank_uses_role_specific_categories(self):
        data = copy.deepcopy(complete_research())
        data["interview_experiences"] = []
        data["interview_prep"]["questions"] = generate_question_bank(data)
        data["interview_prep"].pop("mock_questions", None)
        categories = {
            item["category"] for item in data["interview_prep"]["questions"]
        }
        self.assertIn("coding", categories)
        self.assertIn("system_design", categories)
        self.assertIn("technical", categories)

    def test_non_technical_roles_do_not_reuse_software_bank(self):
        data = copy.deepcopy(complete_research())
        data["request"]["role"] = {
            "title": "Product Operations",
            "family": "operations",
            "level": "Mid-level",
            "url": None,
            "description": None,
        }
        data["interview_experiences"] = []
        questions = generate_question_bank(data)
        categories = {item["category"] for item in questions}
        self.assertIn("business_scenario", categories)
        self.assertIn("product_sense", categories)
        self.assertNotIn("technical", categories)
        self.assertNotIn("system_design", categories)
        self.assertNotIn("coding", categories)

    def test_product_designer_uses_design_specific_categories(self):
        data = copy.deepcopy(complete_research())
        data["request"]["role"] = {
            "title": "Product Designer",
            "family": "product_design",
            "level": "Mid-level",
            "url": None,
            "description": None,
        }
        data["interview_experiences"] = []
        questions = generate_question_bank(data)
        categories = {item["category"] for item in questions}
        self.assertIn("portfolio_review", categories)
        self.assertIn("design_exercise", categories)
        self.assertIn("user_research", categories)
        self.assertNotIn("coding", categories)
        self.assertNotIn("system_design", categories)

    def test_report_never_calls_every_question_a_prediction(self):
        report = render_report(researched_with_experiences())
        self.assertIn("历史原题", report)
        self.assertIn("相似公司参考题", report)
        self.assertNotIn("十个模拟问题（均为预测）", report)
        self.assertIn("## 6. 来源与可信度", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
