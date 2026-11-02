from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from interview_simulator import (
    answer_session,
    create_session,
    finish_session,
    skip_question,
    start_response,
)
from test_interview_research import researched_with_experiences


class SimulatorTests(unittest.TestCase):
    def test_start_shows_one_question_and_hides_answer_outline(self):
        state = create_session(researched_with_experiences(), scene="auto", difficulty="auto")
        response = start_response(state)
        self.assertEqual(response["status"], "in_progress")
        self.assertIn("question", response)
        self.assertNotIn("answer_outline", response["question"])
        self.assertNotIn("answer_structure", response["question"])
        self.assertEqual(response["progress"]["answered"], 0)

    def test_scene_selection_rejects_inapplicable_scene(self):
        data = copy.deepcopy(researched_with_experiences())
        for question in data["interview_prep"]["questions"]:
            question["category"] = "professional_knowledge"
        with self.assertRaisesRegex(ValueError, "不适用于场景"):
            create_session(data, scene="technical")

    def test_weak_answer_triggers_relevant_follow_up(self):
        state = create_session(researched_with_experiences(), scene="technical")
        _, response = answer_session(state, "我会认真处理。")
        self.assertEqual(response["kind"], "follow_up")
        self.assertIn("具体场景", response["question"]["question"])
        self.assertEqual(len(state["turns"]), 1)

    def test_concrete_answer_advances_without_repeating_question(self):
        state = create_session(researched_with_experiences(), scene="technical")
        first = state["current_question_id"]
        _, response = answer_session(
            state,
            "我负责设计缓存服务，将延迟从 120 毫秒降至 45 毫秒，命中率提升 18%，并完成故障回滚和压力测试。",
        )
        self.assertIn("question", response)
        self.assertNotEqual(response["question"]["id"], first)
        self.assertEqual(len({turn["question_id"] for turn in state["turns"]}), 1)
        self.assertEqual(len(state["question_bank"]), 10)

    def test_difficulty_can_change_after_answer(self):
        state = create_session(
            researched_with_experiences(),
            scene="technical",
            difficulty="junior",
        )
        before = state["current_difficulty"]
        answer_session(
            state,
            "我负责设计系统并把延迟降低 30%，同时用压测验证容量，记录了失败模式和回滚方案。",
        )
        self.assertEqual(before, "junior")
        self.assertIn(state["current_difficulty"], {"intermediate", "senior"})

    def test_finish_returns_specific_feedback_without_probability(self):
        state = create_session(researched_with_experiences(), scene="professional")
        answer_session(state, "我之前负责一个服务优化项目。")
        state, response = finish_session(state)
        self.assertEqual(state["status"], "completed")
        feedback = response["feedback"]
        self.assertIn("answered", feedback)
        self.assertIn("gaps", feedback)
        self.assertIn("improved_answer_outlines", feedback)
        self.assertIn("不推断真实录用概率", feedback["disclaimer"])
        self.assertNotIn("录用概率为", str(feedback))

    def test_finish_without_answers_is_honest(self):
        state = create_session(researched_with_experiences())
        _, response = finish_session(state)
        self.assertEqual(response["feedback"]["answered"], 0)
        self.assertIn("无法评估", response["feedback"]["logic_organization"])

    def test_end_to_end_follow_up_then_finish(self):
        state = create_session(researched_with_experiences(), scene="technical")
        state, first = answer_session(state, "我会认真处理。")
        self.assertEqual(first["kind"], "follow_up")
        state, second = answer_session(
            state,
            "我在支付服务故障中负责定位问题，把错误率从 8% 降到 0.5%，"
            "同时记录回滚边界并完成压测复盘。",
        )
        self.assertIn("question", second)
        self.assertNotEqual(second["question"].get("id"), state["turns"][0]["question_id"])
        state, finished = finish_session(state)
        self.assertEqual(finished["status"], "completed")
        self.assertEqual(finished["feedback"]["answered"], 1)
        self.assertTrue(finished["feedback"]["improved_answer_outlines"])

    def test_conversational_finish_command_stops_questions(self):
        state = create_session(researched_with_experiences())
        state, response = answer_session(state, "结束面试")
        self.assertEqual(response["status"], "completed")
        self.assertNotIn("question", response)
        self.assertEqual(state["feedback"]["answered"], 0)

    def test_skip_advances_without_counting_an_answer(self):
        state = create_session(researched_with_experiences(), scene="technical")
        first = state["current_question_id"]
        state, response = skip_question(state)
        self.assertEqual(response["kind"], "skipped")
        self.assertNotEqual(response["question"]["id"], first)
        self.assertEqual(response["progress"]["answered"], 0)
        self.assertEqual(state["turns"], [])

    def test_session_has_ten_unique_questions(self):
        state = create_session(researched_with_experiences())
        ids = [item["id"] for item in state["question_bank"]]
        texts = [item["question"] for item in state["question_bank"]]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertEqual(len(set(texts)), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
