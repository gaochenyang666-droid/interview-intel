#!/usr/bin/env python3
"""Stateful, evidence-grounded mock interview sessions without a server."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from intel_core import (
    DIFFICULTIES,
    EXPERIENCE_LEVEL_LABELS,
    QUESTION_CATEGORY_LABELS,
    QUESTION_ORIGIN_LABELS,
    SCENES,
    _default_difficulty,
    _question_fingerprint,
    validate_research,
)
from interview_questions import generate_question_bank


SCENE_CATEGORIES = {
    "hr_screen": {"hr_motivation", "behavioral", "communication_collaboration"},
    "professional": {"professional_knowledge", "project_experience", "technical", "data_analysis", "product_sense"},
    "technical": {"technical", "coding", "system_design"},
    "business_case": {"business_scenario", "case_analysis", "product_sense", "data_analysis"},
    "final": {"hr_motivation", "behavioral", "situational_judgment", "communication_collaboration", "business_scenario"},
}
DIFFICULTY_ORDER = {"junior": 0, "intermediate": 1, "senior": 2, "stress": 3}
ACTION_WORDS = {
    "负责", "设计", "推动", "实现", "协调", "分析", "排查", "优化", "lead",
    "owned", "built", "designed", "implemented", "led", "analyzed",
}
RESULT_WORDS = {
    "结果", "提升", "降低", "减少", "增长", "上线", "交付", "impact", "result",
    "reduced", "increased", "improved", "launched",
}
TRADEOFF_WORDS = {
    "取舍", "权衡", "tradeoff", "constraint", "边界", "风险", "失败", "回滚",
    "性能", "成本", "安全", "可靠性",
}
STAR_WORDS = {"情境", "任务", "行动", "结果", "situation", "task", "action", "result"}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _public_question(question: dict[str, Any]) -> dict[str, Any]:
    """Hide answer outlines until the interview has ended."""
    return {
        "id": question["id"],
        "question": question["question"],
        "category": question.get("category"),
        "category_label": QUESTION_CATEGORY_LABELS.get(
            question.get("category"), question.get("category")
        ),
        "source_level": question.get("source_level"),
        "source_level_label": EXPERIENCE_LEVEL_LABELS.get(question.get("source_level")),
        "origin_type": question.get("origin_type"),
        "origin_label": QUESTION_ORIGIN_LABELS.get(question.get("origin_type")),
        "competencies": question.get("competencies", []),
        "difficulty": question.get("difficulty", "intermediate"),
    }


def available_scenes(questions: list[dict[str, Any]]) -> list[str]:
    result = []
    for scene, categories in SCENE_CATEGORIES.items():
        if any(question.get("category") in categories for question in questions):
            result.append(scene)
    return result


def choose_scene(
    questions: list[dict[str, Any]],
    requested: str,
    role_title: str | None,
) -> str:
    available = available_scenes(questions)
    if requested != "auto":
        if requested not in SCENES:
            raise ValueError(f"未知面试场景：{requested}")
        if requested not in available:
            raise ValueError(f"该岗位和题库不适用于场景：{requested}")
        return requested
    text = (role_title or "").casefold()
    if any(term in text for term in ["software", "engineer", "developer", "开发", "工程师"]):
        preferred = ["technical", "professional", "final", "business_case"]
    elif any(term in text for term in ["product", "operation", "business", "产品", "运营", "业务"]):
        preferred = ["business_case", "professional", "final", "hr_screen"]
    else:
        preferred = ["professional", "final", "hr_screen", "business_case"]
    for scene in preferred:
        if scene in available:
            return scene
    return available[0] if available else "professional"


def _question_priority(question: dict[str, Any], scene: str, difficulty: str) -> tuple[int, int, str]:
    category_match = 0 if question.get("category") in SCENE_CATEGORIES[scene] else 1
    source_level = int(question.get("source_level", 4))
    level_distance = abs(
        DIFFICULTY_ORDER.get(question.get("difficulty"), 1)
        - DIFFICULTY_ORDER.get(difficulty, 1)
    )
    return (category_match, source_level + level_distance, question.get("question", ""))


def _select_next(
    state: dict[str, Any],
    all_questions: dict[str, dict[str, Any]],
) -> str | None:
    remaining = state.get("remaining_question_ids", [])
    if not remaining:
        return None
    scene = state["scene"]
    difficulty = state["current_difficulty"]
    return min(
        remaining,
        key=lambda question_id: _question_priority(
            all_questions[question_id], scene, difficulty
        ),
    )


def _answer_analysis(answer: str, category: str) -> dict[str, Any]:
    normalized = " ".join(answer.split())
    lowered = normalized.casefold()
    numbers = re.findall(r"\d+(?:\.\d+)?%?", normalized)
    has_action = any(word in lowered for word in ACTION_WORDS)
    has_result = any(word in lowered for word in RESULT_WORDS)
    has_tradeoff = any(word in lowered for word in TRADEOFF_WORDS)
    star_hits = sum(word in lowered for word in STAR_WORDS)
    length_score = 2 if len(normalized) >= 180 else 1 if len(normalized) >= 80 else 0
    score = length_score + bool(numbers) + has_action + has_result + has_tradeoff
    completeness = "strong" if score >= 4 else "moderate" if score >= 2 else "weak"
    missing: list[str] = []
    if not has_action:
        missing.append("具体行动")
    if not numbers:
        missing.append("量化结果")
    if not has_result:
        missing.append("结果或影响")
    if category in {"technical", "system_design", "coding"} and not has_tradeoff:
        missing.append("技术权衡与边界")
    return {
        "length": len(normalized),
        "numbers": numbers,
        "has_action": has_action,
        "has_result": has_result,
        "has_tradeoff": has_tradeoff,
        "star_hits": star_hits,
        "score": score,
        "completeness": completeness,
        "missing": missing,
    }


def _follow_up(question: dict[str, Any], analysis: dict[str, Any]) -> str | None:
    missing = analysis["missing"]
    if "具体行动" in missing:
        return "请补充一个具体场景，说明你本人承担了什么责任、采取了哪些行动。"
    if "量化结果" in missing:
        return "请补充至少一个指标或前后对比，说明你的行动带来了什么可验证变化。"
    if "技术权衡与边界" in missing:
        return "请进一步说明方案的边界条件、失败模式，以及性能、安全或成本之间的关键权衡。"
    if analysis["completeness"] == "weak":
        return "请按“情境、任务、行动、结果、复盘”补充完整，尤其说明你的个人贡献。"
    return None


def _adjust_difficulty(current: str, completeness: str) -> str:
    current_index = DIFFICULTY_ORDER[current]
    if completeness == "strong" and current_index < DIFFICULTY_ORDER["stress"]:
        return list(DIFFICULTY_ORDER)[current_index + 1]
    if completeness == "weak" and current_index > 0:
        return list(DIFFICULTY_ORDER)[current_index - 1]
    return current


def _feedback(state: dict[str, Any]) -> dict[str, Any]:
    turns = state.get("turns", [])
    if not turns:
        return {
            "answered": 0,
            "effective_information": [],
            "logic_organization": "尚未获得回答，无法评估。",
            "domain_coverage": [],
            "evidence_specificity": "尚未获得回答，无法评估。",
            "gaps": ["至少完成一道题后才能评价本次表现。"],
            "practice_questions": [],
            "improved_answer_outlines": [],
            "disclaimer": "本反馈只评价本次模拟对话，不推断真实录用概率。",
        }
    question_map = {item["id"]: item for item in state["question_bank"]}
    answered = len(turns)
    analyses = [turn["analysis"] for turn in turns]
    avg_score = sum(item["score"] for item in analyses) / answered
    metric_rate = sum(bool(item["numbers"]) for item in analyses) / answered
    action_rate = sum(bool(item["has_action"]) for item in analyses) / answered
    star_rate = sum(item["star_hits"] >= 2 for item in analyses) / answered
    covered = []
    for turn in turns:
        label = QUESTION_CATEGORY_LABELS.get(
            question_map[turn["question_id"]].get("category"), "其他"
        )
        if label not in covered:
            covered.append(label)
    practice_turns = sorted(
        turns, key=lambda turn: turn["analysis"]["score"]
    )[:3]
    model_answers = []
    for turn in practice_turns:
        question = question_map[turn["question_id"]]
        model_answers.append(
            {
                "question": question["question"],
                "outline": question.get("answer_outline"),
                "structure": question.get("answer_structure"),
                "source_label": QUESTION_ORIGIN_LABELS.get(question.get("origin_type")),
            }
        )
    gaps = []
    if metric_rate < 1:
        gaps.append("部分回答缺少数字、指标、基线或时间范围。")
    if action_rate < 1:
        gaps.append("部分回答没有清楚区分个人行动和团队贡献。")
    if star_rate < 0.6:
        gaps.append("行为题的结构稳定性不足，需要练习 STAR 组织。")
    if not gaps:
        gaps.append("未发现系统性结构缺口，可继续提高案例难度和追问深度。")
    return {
        "answered": answered,
        "effective_information": [
            f"{turn['question_id']}：回答提供了 "
            + ("、".join(turn["analysis"]["numbers"]) if turn["analysis"]["numbers"] else "定性信息")
            for turn in turns
        ],
        "logic_organization": (
            "多数回答能区分情境与行动，并出现结果表述。"
            if avg_score >= 4
            else "回答已有基本信息，但结构和因果关系仍可更清晰。"
        ),
        "domain_coverage": covered,
        "evidence_specificity": (
            "多数回答包含量化结果或个人行动。"
            if metric_rate >= 0.6 and action_rate >= 0.6
            else "具体程度不足，需增加本人行动、数据与前后对比。"
        ),
        "gaps": gaps,
        "practice_questions": [
            {
                "id": turn["question_id"],
                "question": question_map[turn["question_id"]]["question"],
                "reason": "本次回答得分相对较低，建议重新练习。",
            }
            for turn in practice_turns
        ],
        "improved_answer_outlines": model_answers,
        "disclaimer": "本反馈只评价本次模拟对话，不推断真实录用概率。",
    }


def create_session(
    research: dict[str, Any],
    *,
    scene: str = "auto",
    difficulty: str = "auto",
) -> dict[str, Any]:
    preview_questions = research.get("interview_prep", {}).get("questions", [])
    if isinstance(preview_questions, list) and preview_questions and scene != "auto":
        preview_questions = [
            item for item in preview_questions if isinstance(item, dict)
        ]
        choose_scene(preview_questions, scene, research.get("request", {}).get("role", {}).get("title"))
    normalized = validate_research(research)
    request = normalized.get("request", {})
    role = request.get("role", {}).get("title")
    if not role:
        raise ValueError("模拟面试需要岗位名称")
    questions = normalized.get("interview_prep", {}).get("questions", [])
    if len(questions) < 10:
        questions = generate_question_bank(normalized)
        normalized.setdefault("interview_prep", {})["questions"] = questions
    if len(questions) != 10:
        raise ValueError("模拟面试需要十个已标注来源的题目")
    selected_scene = choose_scene(questions, scene, role)
    selected_difficulty = (
        _default_difficulty(request.get("role", {}).get("level"))
        if difficulty == "auto"
        else difficulty
    )
    if selected_difficulty not in DIFFICULTIES:
        raise ValueError(f"未知难度：{selected_difficulty}")
    question_map = {item["id"]: item for item in questions}
    remaining = sorted(
        [item["id"] for item in questions],
        key=lambda question_id: _question_priority(
            question_map[question_id], selected_scene, selected_difficulty
        ),
    )
    first_id = remaining.pop(0)
    state = {
        "schema_version": "0.1",
        "session_id": str(uuid.uuid4()),
        "created_at": _now(),
        "updated_at": _now(),
        "company": request.get("company", {}).get("name"),
        "role": role,
        "scene": selected_scene,
        "requested_difficulty": difficulty,
        "current_difficulty": selected_difficulty,
        "status": "in_progress",
        "question_bank": questions,
        "remaining_question_ids": remaining,
        "current_question_id": first_id,
        "followup_asked": False,
        "turns": [],
        "feedback": None,
    }
    return state


def start_response(state: dict[str, Any]) -> dict[str, Any]:
    question = next(
        item for item in state["question_bank"] if item["id"] == state["current_question_id"]
    )
    return {
        "session_id": state["session_id"],
        "status": state["status"],
        "scene": state["scene"],
        "difficulty": state["current_difficulty"],
        "progress": {
            "answered": len(state.get("turns", [])),
            "remaining": 1 + len(state["remaining_question_ids"]),
        },
        "question": _public_question(question),
        "message": "请回答当前问题。输入“结束面试”可随时结束并获取反馈。",
    }


def answer_session(state: dict[str, Any], answer: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if state.get("status") != "in_progress":
        raise ValueError("当前模拟面试已结束")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("回答不能为空")
    if answer.strip() in {"结束面试", "结束", "finish"}:
        return finish_session(state)
    question_id = state["current_question_id"]
    question = next(item for item in state["question_bank"] if item["id"] == question_id)
    turn = next((item for item in state["turns"] if item["question_id"] == question_id), None)
    previous_answers = turn.get("answers", []) if turn else []
    analysis = _answer_analysis(
        "\n".join([*previous_answers, answer.strip()]),
        question.get("category", ""),
    )
    if turn is None:
        turn = {
            "question_id": question_id,
            "question": question["question"],
            "answers": [],
            "followups": [],
            "analysis": analysis,
        }
        state["turns"].append(turn)
    else:
        turn["answers"].append(answer.strip())
        turn["analysis"] = analysis
    if not turn["answers"]:
        turn["answers"].append(answer.strip())

    followup = None if state.get("followup_asked") else _follow_up(question, analysis)
    state["current_difficulty"] = _adjust_difficulty(
        state["current_difficulty"], analysis["completeness"]
    )
    state["updated_at"] = _now()
    if followup:
        state["followup_asked"] = True
        turn["followups"].append(followup)
        return state, {
            "session_id": state["session_id"],
            "status": state["status"],
            "scene": state["scene"],
            "difficulty": state["current_difficulty"],
            "kind": "follow_up",
            "question": {"id": question_id, "question": followup},
            "message": "请先补充这一追问。",
        }

    if state["remaining_question_ids"]:
        next_id = _select_next(
            state, {item["id"]: item for item in state["question_bank"]}
        )
        state["remaining_question_ids"].remove(next_id)
        state["current_question_id"] = next_id
        state["followup_asked"] = False
        next_question = next(item for item in state["question_bank"] if item["id"] == next_id)
        return state, {
            "session_id": state["session_id"],
            "status": state["status"],
            "scene": state["scene"],
            "difficulty": state["current_difficulty"],
            "progress": {
                "answered": len(state["turns"]),
                "remaining": 1 + len(state["remaining_question_ids"]),
            },
            "question": _public_question(next_question),
            "message": "请回答当前问题，或输入“结束面试”。",
        }

    state["status"] = "completed"
    state["current_question_id"] = None
    state["feedback"] = _feedback(state)
    return state, {
        "session_id": state["session_id"],
        "status": "completed",
        "scene": state["scene"],
        "difficulty": state["current_difficulty"],
        "feedback": state["feedback"],
    }


def finish_session(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if state.get("status") == "completed" and state.get("feedback"):
        return state, {
            "session_id": state["session_id"],
            "status": "completed",
            "feedback": state["feedback"],
        }
    state["status"] = "completed"
    state["current_question_id"] = None
    state["updated_at"] = _now()
    state["feedback"] = _feedback(state)
    return state, {
        "session_id": state["session_id"],
        "status": "completed",
        "feedback": state["feedback"],
    }


def skip_question(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if state.get("status") != "in_progress":
        raise ValueError("当前模拟面试已结束")
    state["updated_at"] = _now()
    state["followup_asked"] = False
    if state.get("remaining_question_ids"):
        next_id = _select_next(
            state, {item["id"]: item for item in state["question_bank"]}
        )
        state["remaining_question_ids"].remove(next_id)
        state["current_question_id"] = next_id
        next_question = next(
            item for item in state["question_bank"] if item["id"] == next_id
        )
        return state, {
            "session_id": state["session_id"],
            "status": state["status"],
            "scene": state["scene"],
            "difficulty": state["current_difficulty"],
            "kind": "skipped",
            "progress": {
                "answered": len(state.get("turns", [])),
                "remaining": 1 + len(state["remaining_question_ids"]),
            },
            "question": _public_question(next_question),
            "message": "已跳过当前题，本题不计入已回答数量。",
        }
    state["status"] = "completed"
    state["current_question_id"] = None
    state["feedback"] = _feedback(state)
    return state, {
        "session_id": state["session_id"],
        "status": "completed",
        "feedback": state["feedback"],
    }


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_state(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("模拟面试状态必须是 JSON 对象")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a stateful evidence-grounded mock interview.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a new mock interview")
    start.add_argument("research")
    start.add_argument("--state", default=".interview-intel/session.json")
    start.add_argument("--scene", default="auto", choices=["auto", *sorted(SCENES)])
    start.add_argument("--difficulty", default="auto", choices=["auto", *sorted(DIFFICULTIES)])

    answer = subparsers.add_parser("answer", help="Submit one answer and receive a follow-up or next question")
    answer.add_argument("--state", default=".interview-intel/session.json")
    answer.add_argument("--answer")
    answer.add_argument("--answer-file", help="Read the answer from a UTF-8 file; use - for stdin")

    finish = subparsers.add_parser("finish", help="End the interview and generate feedback")
    finish.add_argument("--state", default=".interview-intel/session.json")

    skip = subparsers.add_parser("skip", help="Skip the current question without treating it as answered")
    skip.add_argument("--state", default=".interview-intel/session.json")

    status = subparsers.add_parser("status", help="Show the current question without answers")
    status.add_argument("--state", default=".interview-intel/session.json")

    reset = subparsers.add_parser("reset", help="Start over and overwrite the local session")
    reset.add_argument("research")
    reset.add_argument("--state", default=".interview-intel/session.json")
    reset.add_argument("--scene", default="auto", choices=["auto", *sorted(SCENES)])
    reset.add_argument("--difficulty", default="auto", choices=["auto", *sorted(DIFFICULTIES)])

    args = parser.parse_args()
    state_path = Path(args.state)
    try:
        if args.command in {"start", "reset"}:
            research = json.loads(Path(args.research).read_text(encoding="utf-8"))
            state = create_session(research, scene=args.scene, difficulty=args.difficulty)
            save_state(state_path, state)
            response = start_response(state)
        elif args.command == "answer":
            if args.answer and args.answer_file:
                raise ValueError("--answer 和 --answer-file 只能使用一个")
            if args.answer_file:
                answer_text = sys.stdin.read() if args.answer_file == "-" else Path(args.answer_file).read_text(encoding="utf-8")
            else:
                answer_text = args.answer or ""
            state = load_state(state_path)
            state, response = answer_session(state, answer_text)
            save_state(state_path, state)
        elif args.command == "finish":
            state = load_state(state_path)
            state, response = finish_session(state)
            save_state(state_path, state)
        elif args.command == "skip":
            state = load_state(state_path)
            state, response = skip_question(state)
            save_state(state_path, state)
        else:
            state = load_state(state_path)
            if state.get("status") == "completed":
                response = {
                    "session_id": state["session_id"],
                    "status": "completed",
                    "feedback": state.get("feedback"),
                }
            else:
                response = start_response(state)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
