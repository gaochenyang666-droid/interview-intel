"""Conservative evidence-driven opportunity scoring for Interview Intel.

Ratings are coded judgments, not measurements, company rankings, or hiring probabilities.
Missing factors stay unrated; source volume does not automatically improve a score.
"""
from __future__ import annotations
from typing import Any

RUBRIC = {
    "stability": {"label": "公司经营与稳定性", "dimension": "company", "weight": 15, "sections": {"company"}},
    "culture": {"label": "工作文化与环境", "dimension": "company", "weight": 20, "sections": {"reviews"}},
    "clarity": {"label": "岗位职责与透明度", "dimension": "role", "weight": 15, "sections": {"role"}},
    "growth": {"label": "职业成长", "dimension": "role", "weight": 15, "sections": {"role", "company"}},
    "compensation": {"label": "薪酬竞争力", "dimension": "role", "weight": 10, "sections": {"role"}},
    "skills": {"label": "个人技能匹配", "dimension": "fit", "weight": 15, "sections": {"role"}},
    "preferences": {"label": "个人偏好匹配", "dimension": "fit", "weight": 10, "sections": {"role", "reviews"}},
}
DIMENSIONS = {
    "company": {"label": "公司", "weight": 35, "threshold": 0.70},
    "role": {"label": "岗位", "weight": 40, "threshold": 0.60},
    "fit": {"label": "个人匹配", "weight": 25, "threshold": 0.60},
}
VALID_KINDS = {"fact", "person_statement", "third_party_assessment", "inference"}


def _origins(metric: dict[str, Any], data: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
    """Resolve independently originated, actually opened sources via finding IDs."""
    findings = {f.get("id"): f for f in data.get("findings", []) if isinstance(f, dict)}
    evidence = {e.get("id"): e for e in data.get("evidence", []) if isinstance(e, dict)}
    by_group: dict[str, dict[str, Any]] = {}
    for fid in metric.get("finding_ids", []):
        finding = findings.get(fid)
        if not finding or finding.get("kind") not in VALID_KINDS:
            continue
        for eid in finding.get("evidence_ids", []):
            source = evidence.get(eid)
            if source and source.get("access_status") == "verified":
                group = source.get("independence_group")
                if isinstance(group, str) and group.strip():
                    by_group.setdefault(group, source)
    return list(by_group.values()), set(by_group)


def validate_assessment(data: dict[str, Any], issues: list[str]) -> None:
    """Validate optional ratings after the source and finding structure was checked."""
    if "assessment" not in data:
        return
    block = data["assessment"]
    if not isinstance(block, dict) or not isinstance(block.get("metrics"), list):
        issues.append("assessment.metrics 必须是数组")
        return
    metrics = block["metrics"]
    if not metrics:
        return
    if data.get("research", {}).get("network_status") not in {"available", "partial"}:
        issues.append("网络不可用时不得生成机会评分")
    if data.get("research", {}).get("entity", {}).get("status") != "confirmed":
        issues.append("公司实体未确认时不得生成机会评分")
    findings = {f.get("id"): f for f in data.get("findings", []) if isinstance(f, dict)}
    seen: set[str] = set()
    for index, metric in enumerate(metrics):
        prefix = f"assessment.metrics[{index}]"
        if not isinstance(metric, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        key = metric.get("key")
        if not isinstance(key, str) or key not in RUBRIC:
            issues.append(f"{prefix}.key 必须属于预定义评分项")
            continue
        if key in seen:
            issues.append(f"{prefix}.key 重复: {key}")
        seen.add(key)
        rating = metric.get("rating")
        if type(rating) is not int or not 1 <= rating <= 5:
            issues.append(f"{prefix}.rating 必须是 1 至 5 的整数")
        reason = metric.get("reason")
        if not isinstance(reason, str) or len(reason.strip()) < 12:
            issues.append(f"{prefix}.reason 至少需要 12 个字符的可核查解释")
        ids = metric.get("finding_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(x, str) for x in ids):
            issues.append(f"{prefix}.finding_ids 必须是非空结论 ID 数组")
            continue
        if len(ids) != len(set(ids)):
            issues.append(f"{prefix}.finding_ids 存在重复")
        for fid in ids:
            finding = findings.get(fid)
            if not finding:
                issues.append(f"{prefix} 引用了不存在的结论 {fid}")
            elif finding.get("kind") not in VALID_KINDS:
                issues.append(f"{prefix} 不得以预测、建议或信息缺口 {fid} 评分")
            elif finding.get("section") not in RUBRIC[key]["sections"]:
                issues.append(f"{prefix} 结论 {fid} 不属于该评分项的研究范围")
        sources, groups = _origins(metric, data)
        if not sources:
            issues.append(f"{prefix} 缺少已实际打开核验的来源")
        if key == "culture":
            if len(groups) < 2 or not any(
                s.get("source_type") in {"employee_review", "forum_post", "social_post", "interview_report"}
                for s in sources
            ):
                issues.append(f"{prefix} 工作文化必须有至少两个独立来源，且包含外部职场体验")
        if key == "compensation" and len(groups) < 2:
            issues.append(f"{prefix} 薪酬竞争力需要至少两个独立来源用于比较")
        if key == "skills":
            candidate = data.get("request", {}).get("candidate", {})
            if not (candidate.get("summary") or candidate.get("skills")):
                issues.append(f"{prefix} 未提供个人技能背景，不能计算技能匹配")
        if key == "preferences":
            candidate = data.get("request", {}).get("candidate", {})
            if not candidate.get("preferences"):
                issues.append(f"{prefix} 未提供个人偏好，不能计算偏好匹配")


def evaluate_assessment(data: dict[str, Any]) -> dict[str, Any]:
    """Compute reproducible weighted scores from validated rubric entries."""
    metrics = data.get("assessment", {}).get("metrics", [])
    items = {m["key"]: m for m in metrics}
    results: list[dict[str, Any]] = []
    for key, spec in RUBRIC.items():
        item = items.get(key)
        if item is None:
            results.append({
                "key": key, "label": spec["label"], "dimension": spec["dimension"],
                "weight": spec["weight"], "rating": None, "score": None,
                "quality": "unavailable", "source_origins": 0, "finding_ids": [],
            })
            continue
        sources, groups = _origins(item, data)
        types = {s.get("source_type") for s in sources}
        if len(groups) >= 2 and types.intersection({"official", "official_filing", "job_posting", "first_party"}):
            quality = "high"
        elif types.intersection({"official", "official_filing", "job_posting", "first_party", "professional_profile", "news", "aggregator"}):
            quality = "medium"
        else:
            quality = "low"
        results.append({
            "key": key, "label": spec["label"], "dimension": spec["dimension"],
            "weight": spec["weight"], "rating": item["rating"],
            "score": (item["rating"] - 1) * 25, "reason": item["reason"],
            "quality": quality, "source_origins": len(groups),
            "finding_ids": item["finding_ids"],
        })
    dimensions: dict[str, dict[str, Any]] = {}
    for name, spec in DIMENSIONS.items():
        rated = [x for x in results if x["dimension"] == name and x["rating"] is not None]
        used = sum(x["weight"] for x in rated)
        coverage = round(100 * used / spec["weight"], 1)
        score = (round(sum(x["score"] * x["weight"] for x in rated) / used, 1)
                 if used and used / spec["weight"] >= spec["threshold"] else None)
        quality = ("unavailable" if score is None else
                   "low" if any(x["quality"] == "low" for x in rated) else
                   "high" if all(x["quality"] == "high" for x in rated) else "medium")
        dimensions[name] = {"label": spec["label"], "score": score,
                            "coverage_pct": coverage, "quality": quality}
    covered = sum(x["weight"] for x in results if x["rating"] is not None)
    rated_all = [x for x in results if x["rating"] is not None]
    can_overall = covered >= 80 and all(
        x["score"] is not None and x["quality"] != "low" for x in dimensions.values()
    )
    overall = round(sum(x["score"] * x["weight"] for x in rated_all) / covered, 1) if can_overall else None
    return {
        "status": "scored" if overall is not None else "insufficient_evidence",
        "overall": overall, "coverage_pct": round(float(covered), 1),
        "dimensions": dimensions, "metrics": results,
        "method": "固定权重；1 至 5 档映射为 0/25/50/75/100；缺失项不填 0；维度覆盖至少 60% 至 70%，综合覆盖至少 80%；评分不代表录用概率或客观公司排名。",
    }


def render_score_lines(data: dict[str, Any]) -> list[str]:
    """Render a transparent assessment inside the existing executive summary."""
    if not data.get("assessment", {}).get("metrics"):
        return ["### 面试机会评分", "",
                "暂未评分：尚未提供足够的逐项证据评分，报告保留原有事实与准备建议。", ""]
    result = evaluate_assessment(data)
    score = f"{result['overall']}/100" if result["overall"] is not None else "暂不生成"
    lines = [
        "### 面试机会评分（证据驱动 · 试验性）", "",
        f"**综合参考分：{score}**　证据覆盖率：**{result['coverage_pct']}%**", "",
        "| 维度 | 分数 | 证据覆盖 | 来源质量 |", "|---|---:|---:|---|",
    ]
    quality_labels = {"high": "较高", "medium": "中等", "low": "较低", "unavailable": "不足"}
    for item in result["dimensions"].values():
        score_value = f"{item['score']}/100" if item["score"] is not None else "未评分"
        lines.append(f"| {item['label']} | {score_value} | {item['coverage_pct']}% | {quality_labels[item['quality']]} |")
    lines += ["", "| 评分项（固定权重） | 五档评级 | 证据来源 |", "|---|---|---|"]
    for item in result["metrics"]:
        rating = f"{item['rating']}/5" if item["rating"] is not None else "未评分"
        refs = " ".join(f"[{fid}](#{fid.lower()})" for fid in item["finding_ids"]) or "暂无"
        lines.append(f"| {item['label']}（{item['weight']}%） | {rating} | {refs} |")
    lines += [
        "", "评分方法：" + result["method"],
        "单项评级由 Agent 根据可核验结论判断，程序负责来源校验和固定权重运算；评级仍含主观判断，不代表实际录取机会。", "",
    ]
    return lines
