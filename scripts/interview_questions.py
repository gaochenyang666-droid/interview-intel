"""Generate a source-labelled ten-question interview bank from researched evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from intel_core import (
    QUESTION_CATEGORIES,
    _default_difficulty,
    _question_fingerprint,
    _recommended_question_mix,
)


CATEGORY_COMPETENCIES = {
    "hr_motivation": ["动机与稳定性", "自我认知"],
    "professional_knowledge": ["专业知识", "业务理解"],
    "project_experience": ["项目 ownership", "结果量化"],
    "business_scenario": ["问题定义", "业务判断"],
    "case_analysis": ["结构化分析", "商业推理"],
    "behavioral": ["协作", "冲突处理", "复盘"],
    "situational_judgment": ["优先级", "风险管理"],
    "communication_collaboration": ["沟通", "利益相关方管理"],
    "technical": ["技术深度", "工程判断"],
    "system_design": ["架构设计", "可扩展性", "可靠性"],
    "coding": ["算法", "代码质量", "测试"],
    "product_sense": ["用户价值", "产品判断"],
    "data_analysis": ["指标设计", "因果与实验", "数据质量"],
    "portfolio_review": ["作品集表达", "设计决策", "影响证明"],
    "design_exercise": ["问题定义", "信息架构", "交互设计"],
    "visual_craft": ["视觉层级", "设计系统", "细节质量"],
    "user_research": ["研究方法", "洞察提炼", "验证"],
}

CATEGORY_OUTLINES = {
    "hr_motivation": "说明选择该岗位的具体原因，连接个人经历、岗位要求和未来贡献。",
    "professional_knowledge": "先给结论，再说明关键概念、适用条件、常见误区和例子。",
    "project_experience": "使用 STAR，突出本人角色、关键决策、量化结果和复盘。",
    "business_scenario": "先定义目标和约束，再拆解问题、提出方案、说明指标与风险。",
    "case_analysis": "按问题定义、信息缺口、假设、分析路径、建议和验证组织答案。",
    "behavioral": "使用 STAR，说明冲突或挑战、你的具体行动、结果和后续改进。",
    "situational_judgment": "列出优先级、决策标准、沟通方案、失败边界和回滚计划。",
    "communication_collaboration": "识别不同利益相关方，说明对齐机制、决策权与结果。",
    "technical": "解释原理、实现选择、复杂度、边界、测试和故障处理。",
    "system_design": "从需求与约束出发，再讲数据流、接口、扩展、可靠性和可观测性。",
    "coding": "先澄清输入输出与复杂度，再实现、测试边界并解释取舍。",
    "product_sense": "明确用户、场景、价值和成功指标，再讨论优先级与验证。",
    "data_analysis": "先确认口径和数据质量，再分析分布或实验，区分相关与因果。",
    "portfolio_review": "选一个最相关案例，说明目标、约束、方案迭代、个人贡献、结果和复盘。",
    "design_exercise": "先澄清用户与目标，再给出信息架构、关键流程、低保真方案和验证计划。",
    "visual_craft": "说明视觉层级、排版、色彩与交互细节如何服务可用性和品牌一致性。",
    "user_research": "说明研究问题、样本、方法、证据质量、洞察和后续决策。",
}

ANSWER_STRUCTURE = "结论 → 背景与约束 → 关键行动或方案 → 权衡 → 量化结果 → 复盘"


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _category_for_question(question: str, role: str) -> str:
    text = f"{question} {role}".casefold()
    rules = [
        (("作品集", "portfolio"), "portfolio_review"),
        (("用户研究", "访谈", "调研", "usability", "user research"), "user_research"),
        (("视觉", "排版", "interaction", "交互", "design system"), "visual_craft"),
        (("设计演练", "design exercise", "wireframe", "prototype"), "design_exercise"),
        (("系统设计", "architecture", "架构", "扩展性", "高并发"), "system_design"),
        (("代码", "coding", "算法", "leetcode", "数据结构"), "coding"),
        (("sql", "数据", "指标", "analysis", "实验", "ab test"), "data_analysis"),
        (("设计", "用户", "product", "产品", "需求"), "product_sense"),
        (("冲突", "协作", "团队", "同事", "stakeholder"), "behavioral"),
        (("职业规划", "为什么", "动机", "why this"), "hr_motivation"),
        (("故障", "故障排除", "debug", "排查", "性能"), "technical"),
        (("案例", "case", "估算", "分析"), "case_analysis"),
    ]
    for words, category in rules:
        if any(word in text for word in words):
            return category
    return "professional_knowledge"


def _question(
    *,
    number: int,
    text: str,
    category: str,
    source_level: int,
    origin_type: str,
    basis: str,
    evidence_ids: list[str],
    difficulty: str,
    source_company: str | None = None,
    source_role: str | None = None,
    migration_rationale: str | None = None,
) -> dict[str, Any]:
    return {
        "id": f"IQ{number:03d}",
        "question": text,
        "category": category,
        "source_level": source_level,
        "origin_type": origin_type,
        "source_company": source_company,
        "source_role": source_role,
        "migration_rationale": migration_rationale,
        "evidence_ids": evidence_ids,
        "basis": basis,
        "competencies": CATEGORY_COMPETENCIES.get(category, ["岗位核心能力"]),
        "answer_outline": CATEGORY_OUTLINES.get(category, "说明结论、依据、行动和结果。"),
        "answer_structure": ANSWER_STRUCTURE,
        "difficulty": difficulty,
    }


def _prediction_templates(
    role: str,
    company: str | None,
    industry: str | None,
) -> list[tuple[str, str]]:
    organization = company or "目标企业"
    context = f"{industry}行业的{organization}" if industry else organization
    templates = {
        "hr_motivation": [
            f"你为什么选择 {organization} 的 {role} 岗位？请连接岗位要求、个人经历和长期规划。",
        ],
        "professional_knowledge": [
            f"针对 {role} 岗位，你认为最重要的三项专业能力是什么？请结合具体例子说明。",
            f"你会用哪些指标判断 {role} 工作是否真正创造价值？如何避免指标失真？",
        ],
        "project_experience": [
            f"请讲一个最能证明你适合 {role} 的项目。你本人做了什么，结果如何量化？",
        ],
        "business_scenario": [
            f"假设你刚加入 {context} 负责一项与 {role} 相关的重点项目，你会如何完成前 30 天的诊断？",
        ],
        "case_analysis": [
            f"面对一个目标明确但数据不足的 {role} 业务问题，你会如何拆解假设并决定下一步？",
            f"设计一个 90 天计划，用于验证你在 {organization} 的 {role} 岗位上的第一个业务假设。",
        ],
        "behavioral": [
            "请讲一次你与关键合作方意见不一致的经历。你如何推动决定，最终结果是什么？",
        ],
        "situational_judgment": [
            "如果截止日期临近而关键依赖突然延期，你会如何调整范围、资源和沟通？",
            "如果你最初判断错误，且已经投入了资源，你会怎样止损、复盘并调整方向？",
        ],
        "communication_collaboration": [
            "如何向不熟悉该领域的决策者解释你的方案、风险和投入产出？",
        ],
        "technical": [
            f"请挑一个与 {role} 相关的技术问题，说明根因定位、方案比较、验证方法和最终取舍。",
        ],
        "system_design": [
            f"请为一个与 {role} 相关的高并发业务设计核心系统，说明接口、数据流、扩展性和故障恢复。",
        ],
        "coding": [
            f"请为 {role} 常见的数据处理或算法任务说明解题思路，并分析复杂度、测试和边界条件。",
        ],
        "product_sense": [
            f"选择 {organization} 的一个产品或流程，说明你会如何发现用户问题、确定优先级并验证方案。",
        ],
        "data_analysis": [
            f"如果 {role} 的核心指标突然异常，你会如何检查口径、拆分维度并区分相关与因果？",
        ],
        "portfolio_review": [
            f"请挑一个最能证明你适合 {role} 的项目，说明目标、约束、方案迭代、个人贡献和量化影响。",
        ],
        "design_exercise": [
            f"为 {organization} 的一个真实用户场景完成设计演练，说明信息架构、关键流程、取舍和验证计划。",
        ],
        "visual_craft": [
            "你会如何在紧迫交付中平衡视觉质量、无障碍、设计一致性和开发成本？请用案例说明。",
        ],
        "user_research": [
            "请设计一次用户研究来验证一个高风险产品假设，说明样本、问题、证据判断和决策规则。",
        ],
    }
    mix = _recommended_question_mix(role, industry)
    role_text = role.casefold()
    if any(term in role_text for term in ["designer", "design", "ux", "ui", "设计", "交互"]):
        fallback = ["project_experience", "business_scenario", "professional_knowledge"]
    elif any(term in role_text for term in ["product", "operation", "business", "产品", "运营", "业务"]):
        fallback = ["data_analysis", "professional_knowledge", "situational_judgment"]
    elif any(term in role_text for term in ["data", "analyst", "数据", "分析"]):
        fallback = ["business_scenario", "situational_judgment", "communication_collaboration"]
    else:
        fallback = [
            category for category in templates if category not in mix
        ]
    ordered_categories = list(dict.fromkeys([*mix, *fallback]))
    result: list[tuple[str, str]] = []
    variant_index = {category: 0 for category in templates}
    while len(result) < 10:
        added = False
        for category in ordered_categories:
            variants = templates[category]
            index = variant_index[category]
            if index < len(variants):
                result.append((category, variants[index]))
                variant_index[category] += 1
                added = True
            if len(result) >= 10:
                break
        if not added:
            break
    return result


def generate_question_bank(data: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    """Prefer available historical evidence, then fill the bank with predictions."""
    request = data.get("request", {})
    company = request.get("company", {}).get("name")
    role = request.get("role", {}).get("title")
    if not role:
        return []
    difficulty = _default_difficulty(request.get("role", {}).get("level"))
    experiences = [
        item for item in data.get("interview_experiences", [])
        if isinstance(item, dict) and item.get("evidence_ids")
    ]
    experiences.sort(
        key=lambda item: (
            item.get("source_level", 99),
            -int(str(item.get("published_at") or "0").replace("-", "") or 0),
        )
    )
    question_bank: list[dict[str, Any]] = []
    seen: set[str] = set()
    for experience in experiences:
        level = experience.get("source_level")
        if level not in {1, 2, 3}:
            continue
        for raw_question in experience.get("questions", []):
            if not isinstance(raw_question, str) or not raw_question.strip():
                continue
            fingerprint = _question_fingerprint(raw_question)
            if fingerprint in seen:
                continue
            category = _category_for_question(raw_question, role)
            if category not in QUESTION_CATEGORIES:
                category = "professional_knowledge"
            origin_type = {
                1: "historical_exact",
                2: "historical_similar_role",
                3: "similar_company",
            }[level]
            question_bank.append(
                _question(
                    number=len(question_bank) + 1,
                    text=raw_question.strip(),
                    category=category,
                    source_level=level,
                    origin_type=origin_type,
                    basis=(
                        f"公开面经 {experience['id']} 明确记录"
                        f"{experience.get('company') or '相关公司'}的"
                        f"{experience.get('role') or role}面试中提出过该问题。"
                    ),
                    evidence_ids=list(experience["evidence_ids"]),
                    difficulty=_as_text(experience.get("difficulty")) or difficulty,
                    source_company=experience.get("company"),
                    source_role=experience.get("role"),
                    migration_rationale=experience.get("match_rationale") if level in {2, 3} else None,
                )
            )
            seen.add(fingerprint)
            if len(question_bank) >= min(limit, 7):
                break
        if len(question_bank) >= min(limit, 7):
            break

    evidence = data.get("evidence", [])
    job_ids = [
        item.get("id") for item in evidence
        if isinstance(item, dict)
        and item.get("id")
        and item.get("source_type") in {"job_posting", "official"}
    ][:2]
    if not job_ids:
        job_ids = [
            item.get("id") for item in evidence
            if isinstance(item, dict) and item.get("id")
        ][:2]
    for category, text in _prediction_templates(
        role,
        company,
        request.get("company", {}).get("industry"),
    ):
        if len(question_bank) >= limit:
            break
        fingerprint = _question_fingerprint(text)
        if fingerprint in seen:
            continue
        question_bank.append(
            _question(
                number=len(question_bank) + 1,
                text=text,
                category=category,
                source_level=4,
                origin_type="prediction",
                basis=f"根据公开岗位信息“{role}”及通用能力模型生成，未声称是该公司历史原题。",
                evidence_ids=job_ids,
                difficulty=difficulty,
            )
        )
        seen.add(fingerprint)
    return question_bank


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an evidence-labelled interview question bank.")
    parser.add_argument("research", help="Research JSON with evidence and optional interview_experiences")
    parser.add_argument("--output", "-o", help="Write updated research JSON")
    args = parser.parse_args()
    path = Path(args.research)
    data = json.loads(path.read_text(encoding="utf-8"))
    questions = generate_question_bank(data)
    data.setdefault("interview_prep", {})["questions"] = questions
    data["interview_prep"].pop("mock_questions", None)
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.write_text(rendered, encoding="utf-8")
        print(f"已写入 {output.resolve()}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
