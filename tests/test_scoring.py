from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from intel_core import IntelValidationError, build_plan, render_report, validate_research
from scoring import evaluate_assessment
from test_interview_intel import complete_research


def metric(key: str, rating: int, *finding_ids: str) -> dict:
    return {"key": key, "rating": rating,
            "reason": "根据核验过的来源和相关岗位要求评估该维度，有局限。", "finding_ids": list(finding_ids)}


class OpportunityScoringTests(unittest.TestCase):
    def test_legacy_report_without_assessment_is_compatible(self):
        data = complete_research()
        normalized = validate_research(data)
        result = evaluate_assessment(normalized)
        self.assertIsNone(result["overall"])
        self.assertEqual(result["coverage_pct"], 0)
        self.assertIn("暂未评分", render_report(data))

    def test_scaffold_has_empty_optional_assessment(self):
        data = build_plan({"company": {"name": "Example Corp"}, "role": {"title": "Engineer"}})
        self.assertEqual(data["scaffold"]["assessment"], {"metrics": []})

    def test_partially_scored_and_missing_metrics_not_zero(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("stability", 4, "F001"),
                                          metric("clarity", 4, "F004"),
                                          metric("skills", 4, "F004")]}
        scores = evaluate_assessment(validate_research(data))
        self.assertEqual(scores["status"], "insufficient_evidence")
        self.assertIsNone(scores["overall"])
        self.assertEqual(scores["coverage_pct"], 45.0)
        self.assertIsNone(scores["dimensions"]["company"]["score"])
        self.assertEqual(scores["dimensions"]["fit"]["score"], 75.0)
        self.assertIn("面试机会评分", render_report(data))
        self.assertIn("[F001](#f001)", render_report(data))

    def test_culture_requires_independent_review_origins(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("culture", 4, "F003")]}
        with self.assertRaisesRegex(IntelValidationError, "两个独立来源"):
            validate_research(data)

    def test_compensation_requires_comparison_sources(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("compensation", 4, "F004")]}
        with self.assertRaisesRegex(IntelValidationError, "薪酬竞争力需要"):
            validate_research(data)

    def test_prediction_cannot_support_score(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("growth", 4, "F006")]}
        with self.assertRaisesRegex(IntelValidationError, "预测"):
            validate_research(data)

    def test_invalid_rating_and_duplicate_metric_rejected(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("stability", True, "F001"),
                                          metric("stability", 5, "F001")]}
        with self.assertRaisesRegex(IntelValidationError, "1 至 5"):
            validate_research(data)

    def test_personal_preferences_require_user_disclosure(self):
        data = complete_research()
        data["assessment"] = {"metrics": [metric("preferences", 4, "F004")]}
        with self.assertRaisesRegex(IntelValidationError, "个人偏好"):
            validate_research(data)

    def test_unconfirmed_company_cannot_receive_score(self):
        data = complete_research()
        data["research"]["entity"]["status"] = "probable"
        data["assessment"] = {"metrics": [metric("stability", 4, "F001")]}
        with self.assertRaisesRegex(IntelValidationError, "公司实体未确认"):
            validate_research(data)

    def test_no_network_cannot_be_scored(self):
        data = complete_research()
        data["research"]["network_status"] = "unavailable"
        data["assessment"] = {"metrics": [metric("stability", 4, "F001")]}
        with self.assertRaisesRegex(IntelValidationError, "网络不可用"):
            validate_research(data)

    def test_complete_evidenced_assessment(self):
        data = complete_research()
        data["request"]["candidate"]["preferences"] = ["remote work"]
        data["evidence"].extend([
            {
                "id": "E009", "title": "Official workplace statement",
                "url": "https://example.com/workplace", "platform": "Example Corp",
                "source_type": "official", "published_at": "2026-09-01",
                "retrieved_at": "2026-11-02", "language": "en",
                "excerpt": "Published team working arrangements.",
                "access_status": "verified", "independence_group": "company-culture",
                "supports": ["F009"], "limitations": "Company-authored."
            },
            {
                "id": "E010", "title": "Regional salary study",
                "url": "https://salary.example.org/benchmark", "platform": "Salary survey",
                "source_type": "aggregator", "published_at": "2026-09-01",
                "retrieved_at": "2026-11-02", "language": "en",
                "excerpt": "Regional role pay benchmarks.",
                "access_status": "verified", "independence_group": "independent-pay",
                "supports": ["F010"], "limitations": "Salary estimates."
            },
        ])
        data["findings"].extend([
            {"id": "F009", "section": "reviews", "kind": "fact",
             "statement": "官网公布工作方式。", "evidence_ids": ["E009"], "confidence": "high"},
            {"id": "F010", "section": "role", "kind": "fact",
             "statement": "存在地区薪资比较数据。", "evidence_ids": ["E002", "E010"], "confidence": "medium"},
        ])
        data["assessment"] = {"metrics": [
            metric("stability", 4, "F001"),
            metric("culture", 4, "F003", "F009"),
            metric("clarity", 4, "F004"),
            metric("growth", 4, "F002"),
            metric("compensation", 3, "F010"),
            metric("skills", 4, "F004"),
            metric("preferences", 4, "F004"),
        ]}
        normalized = validate_research(data)
        score = evaluate_assessment(normalized)
        self.assertEqual(score["status"], "scored")
        self.assertEqual(score["overall"], 72.5)
        self.assertEqual(score["coverage_pct"], 100)
        self.assertEqual(score["dimensions"]["company"]["score"], 75.0)
        self.assertIn("72.5/100", render_report(data))


if __name__ == "__main__":
    unittest.main()
