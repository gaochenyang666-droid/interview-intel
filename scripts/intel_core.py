"""Core planning, validation, deduplication, and rendering for Interview Intel."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scoring import validate_assessment, render_score_lines


ROOT = Path(__file__).resolve().parent.parent
REFERENCES = ROOT / "references"
SCHEMA_VERSION = "0.1"
PRODUCT_VERSION = "0.2.0-beta.1"

SOURCE_TYPES = {
    "official",
    "official_filing",
    "job_posting",
    "first_party",
    "professional_profile",
    "news",
    "interview_report",
    "employee_review",
    "social_post",
    "forum_post",
    "aggregator",
    "candidate_provided",
}
ACCESS_STATUSES = {"verified", "snippet_only", "blocked", "unavailable"}
FINDING_KINDS = {
    "fact",
    "person_statement",
    "third_party_assessment",
    "inference",
    "prediction",
    "gap",
    "advice",
}
CONFIDENCE = {"high", "medium", "low"}
NETWORK_STATUSES = {"available", "partial", "unavailable", "failed", "unknown"}
SECTION_ORDER = [
    ("company", "1. 公司概况与综合评价"),
    ("reviews", "2. 员工及社交媒体评价"),
    ("role", "3. 岗位评价"),
    ("experiences", "4. 公开历史面经与匹配"),
    ("prep", "5. 面试预测与准备"),
]
INTERVIEW_SOURCE_LEVELS = {1, 2, 3, 4}
INTERVIEW_ORIGIN_TYPES = {
    "historical_exact",
    "historical_similar_role",
    "similar_company",
    "prediction",
}
QUESTION_CATEGORIES = {
    "hr_motivation",
    "professional_knowledge",
    "project_experience",
    "business_scenario",
    "case_analysis",
    "behavioral",
    "situational_judgment",
    "communication_collaboration",
    "technical",
    "system_design",
    "coding",
    "product_sense",
    "data_analysis",
    "portfolio_review",
    "design_exercise",
    "visual_craft",
    "user_research",
}
SCENES = {"hr_screen", "professional", "technical", "business_case", "final"}
DIFFICULTIES = {"junior", "intermediate", "senior", "stress"}
SALARY_PERIODS = {"year", "month", "hour"}
KIND_LABELS = {
    "fact": "事实",
    "person_statement": "本人公开表述",
    "third_party_assessment": "第三方评价",
    "inference": "分析推断",
    "prediction": "面试预测",
    "gap": "信息缺口",
    "advice": "准备建议",
}
TRUST_LABELS = {"high": "高", "medium": "中", "low": "低"}
ACCESS_LABELS = {
    "verified": "已验证",
    "snippet_only": "仅搜索摘要",
    "blocked": "访问受限",
    "unavailable": "页面不可用",
}
EXPERIENCE_LEVEL_LABELS = {
    1: "第一级：本公司相同岗位",
    2: "第二级：本公司相近岗位",
    3: "第三级：相似公司相同岗位",
    4: "第四级：行业通用 / AI 预测",
}
QUESTION_ORIGIN_LABELS = {
    "historical_exact": "历史原题",
    "historical_similar_role": "本公司相近岗位参考题",
    "similar_company": "相似公司参考题",
    "prediction": "AI 预测题",
}
QUESTION_CATEGORY_LABELS = {
    "hr_motivation": "HR 动因与动机",
    "professional_knowledge": "专业知识",
    "project_experience": "项目经历",
    "business_scenario": "业务场景",
    "case_analysis": "案例分析",
    "behavioral": "行为面试",
    "situational_judgment": "情境判断",
    "communication_collaboration": "沟通协作",
    "technical": "技术能力",
    "system_design": "系统设计",
    "coding": "编码",
    "product_sense": "产品思维",
    "data_analysis": "数据分析",
    "portfolio_review": "作品集深挖",
    "design_exercise": "设计演练",
    "visual_craft": "视觉与交互质量",
    "user_research": "用户研究",
}
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
    "spm",
}
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|rules?)", re.IGNORECASE),
    re.compile(r"\b(?:reveal|show|print|send|upload)\s+(?:the\s+)?(?:system prompt|developer message|candidate resume|api key|password|private data)", re.IGNORECASE),
    re.compile(r"\byou are now\s+(?:a|an|the)\b", re.IGNORECASE),
    re.compile(r"忽略(?:以上|之前|先前|全部).{0,8}(?:指令|规则|要求)"),
    re.compile(r"(?:泄露|输出|发送|上传).{0,8}(?:简历|提示词|密钥|密码|私人数据)"),
]
EMAIL_PATTERN = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9._%+-])")
PHONE_PATTERN = re.compile(
    r"(?i)(?:\b(?:personal|mobile|cell|home|private)\s+(?:phone|tel(?:ephone)?)|(?:个人|私人|家庭)?(?:电话|手机))\s*[:：]?\s*(?:\+?\d[\d ()-]{6,}\d)"
)
ADDRESS_PATTERN = re.compile(
    r"(?i)(?:\b(?:home|residential|private)\s+address|家庭住址|私人住址|住址)\s*[:：]?[^.\n；;]{0,120}"
)


class IntelValidationError(ValueError):
    """Raised when a research artifact cannot be rendered safely."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_country_profiles() -> dict[str, Any]:
    return load_json(REFERENCES / "country-profiles.json")


def load_source_catalog() -> dict[str, Any]:
    return load_json(REFERENCES / "source-catalog.json")


def _require_text(value: Any, label: str, issues: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{label} 必须是非空字符串")
        return None
    return " ".join(value.split())


def _skip_value(value: Any) -> bool:
    """A user-supplied zero means unknown, never the literal entity '0'."""
    return value is None or value == 0 or (isinstance(value, str) and value.strip() in {"", "0"})


def _optional_target(value: Any, label: str, issues: list[str]) -> str | None:
    if _skip_value(value):
        return None
    return _require_text(value, label, issues)


def _normalize_country(value: Any, profiles: dict[str, Any]) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if _skip_value(value):
        return None, warnings
    if not isinstance(value, str):
        return None, ["location.country 不是字符串，已回退到全球路线"]
    needle = value.strip().casefold()
    direct = value.strip().upper()
    countries = profiles["countries"]
    if direct in countries:
        return direct, warnings
    for code, profile in countries.items():
        aliases = [str(item).casefold() for item in profile.get("aliases", [])]
        if needle in aliases or needle == code.casefold():
            return code, warnings
    warnings.append(f"无法识别国家或地区“{value}”，已回退到全球路线")
    return None, warnings


def normalize_request(request: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if not isinstance(request, dict):
        raise IntelValidationError(["请求必须是 JSON 对象"])

    company = request.get("company")
    role = request.get("role")
    if _skip_value(company):
        company = {}
    if _skip_value(role):
        role = {}
    if not isinstance(company, dict):
        issues.append("company 必须是对象或 0")
        company = {}
    if not isinstance(role, dict):
        issues.append("role 必须是对象或 0")
        role = {}

    company_name = _optional_target(company.get("name"), "company.name", issues)
    role_title = _optional_target(role.get("title"), "role.title", issues)

    location = request.get("location") if isinstance(request.get("location"), dict) else {}
    country, warnings = _normalize_country(location.get("country"), load_country_profiles())
    # Interviewer profiling has been retired from the active research workflow.
    # Ignore old interviewer fields for backward-compatible input parsing.
    cleaned_interviewers: list[dict[str, Any]] = []

    if not (company_name or role_title):
        issues.append("国家之外至少需要公司或岗位中的一项；全部填写 0 无法开展研究")
    if issues:
        raise IntelValidationError(issues)

    candidate = request.get("candidate") if isinstance(request.get("candidate"), dict) else {}
    research = request.get("research") if isinstance(request.get("research"), dict) else {}
    languages = research.get("languages", [])
    if not isinstance(languages, list) or not all(isinstance(item, str) and item for item in languages):
        warnings.append("research.languages 无效，已忽略")
        languages = []

    normalized = {
        "company": {
            "name": company_name,
            "website": _clean_optional(company.get("website")),
            "industry": _clean_optional(company.get("industry")),
        },
        "role": {
            "title": role_title,
            "url": _clean_optional(role.get("url")),
            "description": _clean_optional(role.get("description"), collapse=False),
            "level": _clean_optional(role.get("level")),
            "family": _clean_optional(role.get("family")),
        },
        "location": {
            "country": country,
            "country_input": _clean_optional(location.get("country")),
            "city": _clean_optional(location.get("city")),
        },
        "interviewers": cleaned_interviewers,
        "similar_companies": _clean_string_list(
            company.get("similar_companies", request.get("similar_companies"))
        ),
        "candidate": {
            "summary": _clean_optional(candidate.get("summary"), collapse=False),
            "skills": _clean_string_list(candidate.get("skills")),
            "preferences": _clean_string_list(candidate.get("preferences")),
        },
        "quick_mode": bool(request.get("quick_mode", False)),
        "focus": _clean_string_list(request.get("focus")),
        "research": {
            "max_queries": research.get("max_queries"),
            "recency_months": research.get("recency_months"),
            "languages": languages,
        },
    }
    if issues:
        raise IntelValidationError(issues)
    return normalized, warnings


def _clean_optional(value: Any, collapse: bool = True) -> str | None:
    if _skip_value(value) or not isinstance(value, str):
        return None
    return " ".join(value.split()) if collapse else value.strip()


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [" ".join(item.split()) for item in value if isinstance(item, str) and item.strip()]


def _quote(value: str | None) -> str:
    return f'"{value}"' if value else ""


def _query(
    language: str,
    category: str,
    text: str,
    priority: int,
    platforms: Iterable[str],
    why: str,
) -> dict[str, Any]:
    return {
        "language": language,
        "category": category,
        "query": " ".join(text.split()),
        "priority": priority,
        "platform_ids": sorted(set(platforms)),
        "purpose": why,
    }



# Prioritize public discussion platforms over official employer marketing pages.
# Domains come from the existing source catalog, never from inferred URL templates.
COMMUNITY_ORDER = {
    "CN": ["zhihu", "maimai", "xiaohongshu", "nowcoder", "weibo"],
    "US": ["reddit", "blind", "indeed", "glassdoor"],
    "CA": ["reddit", "blind", "indeed", "glassdoor"],
    "JP": ["note", "openwork", "転職会議", "x"],
    "KR": ["naver", "blind-korea", "jobplanet"],
    "IN": ["reddit", "ambitionbox", "indeed"],
    "DE": ["kununu", "reddit", "indeed"],
}
COMMUNITY_FALLBACK = ["reddit", "indeed", "x", "facebook"]
COMMUNITY_ACCESS = {"found", "blocked", "login_required", "snippet_only",
                    "no_results", "irrelevant", "error"}
COMMUNITY_POST_TYPES = {"employee_review", "forum_post", "social_post", "interview_report"}


def _community_targets(country_code: str | None) -> list[dict[str, str]]:
    """Return candidate platforms with actual indexed domains, not fabricated URLs."""
    sources = {s["id"]: s for s in load_source_catalog()["sources"]
               if s.get("status") != "retired"}
    names = [*COMMUNITY_ORDER.get(country_code, []), *COMMUNITY_FALLBACK]
    targets: list[dict[str, str]] = []
    for name in names:
        source = sources.get(name)
        if not source or any(t["platform_id"] == name for t in targets):
            continue
        regions = set(source.get("regions", []))
        if country_code and country_code not in regions and "global" not in regions:
            continue
        domains = source.get("search_domains") or []
        if not domains:
            continue
        domain = domains[0].split("/", 1)[0]
        if not re.fullmatch(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", domain):
            continue
        targets.append({"platform_id": name, "domain": domain, "name": source["name"]})
    return targets[:5]


def _community_queries(company: str, role: str | None,
                       country_code: str | None) -> list[dict[str, Any]]:
    local_language = {
        "CN": "zh-Hans", "JP": "ja", "KR": "ko", "DE": "de",
        "ES": "es", "FR": "fr", "IN": "en",
    }.get(country_code, "en")
    words = {
        "CN": "员工 评价 正面 负面 加班 离职 工作体验",
        "JP": "社員 口コミ 良い点 悪い点 労働環境 退職",
        "KR": "직원 후기 장점 단점 근무환경 퇴사",
        "DE": "Mitarbeiter Erfahrungen Vorteile Nachteile Arbeitsklima",
        "ES": "opiniones empleados ventajas desventajas ambiente laboral",
        "FR": "avis salariés avantages inconvénients conditions de travail",
    }.get(country_code, "employee experience culture workload")
    terms = f'{_quote(company)} {role or ""} {words}'
    queries: list[dict[str, Any]] = []
    for position, target in enumerate(_community_targets(country_code)):
        queries.append(_query(local_language, "community_platform",
                              f'site:{target["domain"]} {terms}',
                              93 - position, [target["platform_id"]],
                              "寻找可公开打开的第一手职场体验、讨论和原帖，检查正反观点"))
    return queries


def _validate_community_attempts(data: dict[str, Any], issues: list[str]) -> None:
    """For new research artifacts, require transparent attempts or honest access failures."""
    research = data.get("research", {})
    coverage = research.get("coverage", {})
    if not isinstance(coverage, dict) or not coverage.get("community_required"):
        return  # Legacy research files are still accepted.
    if not data.get("request", {}).get("company", {}).get("name"):
        return
    if research.get("network_status") not in {"available", "partial"}:
        return
    attempts = coverage.get("community_attempts")
    if not isinstance(attempts, list) or len(attempts) < 2:
        issues.append("社交口碑研究至少需记录两个独立平台的检索尝试或访问失败")
        return
    evidence = _evidence_map(data)
    distinct: set[str] = set()
    for index, attempt in enumerate(attempts):
        prefix = f"research.coverage.community_attempts[{index}]"
        if not isinstance(attempt, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        name = attempt.get("platform_id")
        query = attempt.get("query")
        result = attempt.get("result")
        if not isinstance(name, str) or not name.strip():
            issues.append(f"{prefix}.platform_id 必填")
        else:
            distinct.add(name)
        if not isinstance(query, str) or not query.strip():
            issues.append(f"{prefix}.query 必填，需记录实际执行的检索词")
        if result not in COMMUNITY_ACCESS:
            issues.append(f"{prefix}.result 无效")
        ids = attempt.get("evidence_ids", [])
        if not isinstance(ids, list):
            issues.append(f"{prefix}.evidence_ids 必须是数组")
            continue
        if result == "found":
            adopted = [evidence.get(eid) for eid in ids if isinstance(eid, str)]
            if not adopted or not any(item and item.get("access_status") == "verified"
                                      and item.get("source_type") in COMMUNITY_POST_TYPES
                                      for item in adopted):
                issues.append(f"{prefix} 标记 found 时必须关联可打开的原帖或员工评价证据")
        elif ids:
            issues.append(f"{prefix} 检索未采纳原帖时不能填写 evidence_ids")
    if len(distinct) < 2:
        issues.append("社交口碑研究至少需要两个不同的平台；同一平台多次检索仅计一次")
    for finding in data.get("findings", []):
        if not isinstance(finding, dict) or finding.get("section") != "reviews":
            continue
        if finding.get("kind") != "third_party_assessment":
            continue
        sources = [evidence.get(eid) for eid in finding.get("evidence_ids", [])]
        if not any(item and item.get("access_status") == "verified"
                   and item.get("source_type") in COMMUNITY_POST_TYPES for item in sources):
            issues.append(f"{finding.get('id', 'reviews')} 社区评价必须引用实际打开的第三方原帖或员工体验")

def build_queries(request: dict[str, Any], country_code: str | None) -> list[dict[str, Any]]:
    """Skip searches that require missing targets; still search English and local languages."""
    profiles = load_country_profiles()
    profile = profiles["countries"].get(country_code, profiles["default"]) if country_code else profiles["default"]
    company = request["company"].get("name")
    role = request["role"].get("title")
    city = request["location"].get("city")
    industry = request["company"].get("industry")
    similar_companies = request.get("similar_companies", [])
    catalog = load_source_catalog()
    active_ids = {item["id"] for item in catalog["sources"] if item.get("status") != "retired"}
    platforms = [p for p in profile.get("platforms", []) if p in active_ids]
    languages: list[str] = []
    for lang in ["en", *profile.get("languages", ["en"]), *request["research"].get("languages", [])]:
        if lang not in languages:
            languages.append(lang)
    queries: list[dict[str, Any]] = []
    location_part = " ".join(x for x in [company, city] if x)
    if company:
        queries.append(_query("en", "company_official", f'{_quote(company)} official website investor relations', 100, ["linkedin"], "确认公司实体与官方披露"))
        queries.append(_query("en", "company_reviews", f'{location_part} employee reviews salary culture layoffs', 94, platforms, "收集雇主评价与薪酬情况"))
        queries.append(_query("en", "company_recent", f'{_quote(company)} latest results layoffs hiring news', 88, ["news_search"], "核验近期经营和招聘变化"))
        if industry:
            queries.append(_query("en", "company_context", f'{_quote(company)} {_quote(industry)} business model competitors', 76, ["news_search"], "了解业务背景"))
    if role:
        contextual = " ".join(x for x in [f'"{company}"' if company else None, f'"{role}"', city] if x)
        queries.append(_query("en", "company_jobs" if company else "role_jobs",
                              f'{contextual} careers job opening responsibilities', 98, platforms, "查询公开岗位职责与要求"))
        interviews = ["glassdoor", "reddit", "youtube", "blind", "nowcoder", "leetcode"]
        if company:
            queries.append(_query("en", "interview_exact", f'{contextual} interview experience questions rounds', 97,
                                  interviews, "优先寻找本公司与相同岗位的公开面经和原题"))
            queries.append(_query("en", "interview_similar_role",
                                  f'{_quote(company)} related role interview experience questions',
                                  83, interviews, "完全匹配不足时寻找本公司相近岗位面经"))
        if similar_companies:
            peer_expression = " OR ".join(_quote(name) for name in similar_companies[:5])
            queries.append(_query("en", "interview_peer_company",
                                  f'({peer_expression}) {_quote(role)} interview experience questions',
                                  79, interviews, "参考已确认的同行业、相近业务公司同岗位面经"))
        else:
            queries.append(_query("en", "interview_peer_discovery",
                                  f'{_quote(industry or "")} companies {_quote(role)} interview experience questions',
                                  74, interviews, "先发现业务模式和岗位相近的可比公司，再检索同岗位面经"))
        queries.append(_query("en", "interview_role_general",
                              f'{_quote(role)} interview questions competencies common scenarios',
                              70, ["youtube", "reddit", "leetcode"], "没有公司专属面经时补充行业通用岗位问题"))
        queries.append(_query("en", "role_market", f'{contextual} salary level compensation benchmark', 90,
                              ["levels-fyi", "glassdoor", "indeed"], "了解薪酬区间及适用地点"))
        if company:
            queries.append(_query("en", "company_culture", f'{contextual} work life balance promotion management', 82,
                                  ["glassdoor", "reddit", "blind"], "查找团队工作体验"))
    if company:
        queries.extend(_community_queries(company, role, country_code))
    for language in languages:
        if language == "en":
            continue
        terms = " ".join(profile.get("local_terms", [])[:4])
        target = " ".join(x for x in [company, role, city] if x)
        if target:
            category = "local_company_role" if company and role else "local_target"
            queries.append(_query(language, category, f'{_quote(target)} {terms}', 92, platforms,
                                  "使用当地语言查找岗位、企业及社区信息"))
            if role:
                local_interview_terms = {
                    "zh-Hans": "面经 面试题 面试流程 面试经验",
                    "ja": "面接体験 面接質問 選考フロー",
                    "ko": "면접 후기 면접 질문 채용 절차",
                    "de": "Vorstellungsgespräch Erfahrung Fragen",
                    "fr": "expérience entretien questions processus",
                    "es": "experiencia entrevista preguntas proceso",
                    "pt-BR": "experiência entrevista perguntas processo",
                    "hi": "साक्षात्कार अनुभव प्रश्न प्रक्रिया",
                }.get(language, terms)
                queries.append(_query(language, "interview_local",
                                      f'{_quote(target)} {local_interview_terms}', 96, interviews,
                                      "使用当地语言优先检索本公司和同岗位公开面经"))
    seen: set[tuple[str, str]] = set()
    de_duplicated: list[dict[str, Any]] = []
    for item in sorted(queries, key=lambda q: (-q["priority"], q["language"])):
        key = item["language"], item["query"].casefold()
        if key not in seen:
            seen.add(key)
            de_duplicated.append(item)
    for index, item in enumerate(de_duplicated, 1):
        item["id"] = f"Q{index:03d}"
    return de_duplicated


def route_sources(country_code: str | None, language_order: list[str], limit: int = 12) -> list[dict[str, Any]]:
    catalog = load_source_catalog()
    ranked: list[dict[str, Any]] = []
    for source in catalog["sources"]:
        if source.get("status") == "retired":
            continue
        regions = set(source.get("regions", []))
        if country_code and country_code not in regions and "global" not in regions:
            continue
        if not country_code and "global" not in regions:
            continue
        score = 10
        reasons: list[str] = []
        if country_code and country_code in regions:
            score += 30
            reasons.append("本地覆盖")
        if "global" in regions:
            score += 12
            reasons.append("全球覆盖")
        use = set(source.get("use", []))
        for category, points in {
            "official": 0,
            "jobs": 8,
            "reviews": 9,
            "interview": 10,
            "salary": 7,
            "professional": 6,
            "community": 5,
        }.items():
            if category in use:
                score += points
        if "search_index" in source.get("access", []):
            score += 4
            reasons.append("可经公开索引发现")
        if source.get("login_gated"):
            score -= 2
            reasons.append("正文可能需登录，仅使用公开部分")
        ranked.append(
            {
                "id": source["id"],
                "name": source["name"],
                "home_url": source["home_url"],
                "score": score,
                "use": source.get("use", []),
                "login_gated": bool(source.get("login_gated")),
                "reasons": reasons,
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    return ranked[:limit]


def _recommended_question_mix(role_title: str | None, industry: str | None = None) -> list[str]:
    role_text = (role_title or "").casefold()
    combined = f"{role_title or ''} {industry or ''}".casefold()
    if any(term in role_text for term in ["designer", "design", "ux", "ui", "设计", "交互"]):
        return [
            "portfolio_review",
            "design_exercise",
            "user_research",
            "visual_craft",
            "communication_collaboration",
            "behavioral",
        ]
    if any(term in role_text for term in ["software", "developer", "engineer", "开发", "工程师", "程序"]):
        return [
            "technical",
            "coding",
            "system_design",
            "project_experience",
            "behavioral",
            "situational_judgment",
        ]
    if any(term in role_text for term in ["data", "analyst", "analytics", "数据", "分析"]):
        return [
            "data_analysis",
            "professional_knowledge",
            "case_analysis",
            "project_experience",
            "behavioral",
            "communication_collaboration",
        ]
    if any(term in role_text for term in ["product", "产品"]):
        return [
            "product_sense",
            "business_scenario",
            "case_analysis",
            "project_experience",
            "behavioral",
            "communication_collaboration",
        ]
    if any(term in role_text for term in ["operation", "运营", "growth", "增长"]):
        return [
            "business_scenario",
            "data_analysis",
            "project_experience",
            "case_analysis",
            "behavioral",
            "communication_collaboration",
        ]
    if any(term in role_text for term in ["manager", "director", "经理", "管理"]):
        return [
            "behavioral",
            "situational_judgment",
            "business_scenario",
            "communication_collaboration",
            "project_experience",
            "professional_knowledge",
        ]
    if any(term in combined for term in ["software", "developer", "engineer", "开发", "工程师", "程序"]):
        return [
            "technical",
            "coding",
            "system_design",
            "project_experience",
            "behavioral",
            "situational_judgment",
        ]
    return [
        "professional_knowledge",
        "project_experience",
        "behavioral",
        "situational_judgment",
        "communication_collaboration",
        "case_analysis",
    ]


def _default_difficulty(role_level: str | None) -> str:
    level = (role_level or "").casefold()
    if any(term in level for term in ["intern", "entry", "junior", "assistant", "初级", "实习"]):
        return "junior"
    if any(term in level for term in ["senior", "lead", "staff", "principal", "manager", "director", "高级", "资深", "经理"]):
        return "senior"
    return "intermediate"


def build_plan(request: dict[str, Any], max_queries: int | None = None, network_status: str = "unknown") -> dict[str, Any]:
    normalized, warnings = normalize_request(request)
    if network_status not in NETWORK_STATUSES:
        raise IntelValidationError([f"未知网络状态: {network_status}"])
    requested_limit = max_queries or normalized["research"].get("max_queries") or 18
    try:
        requested_limit = int(requested_limit)
    except (TypeError, ValueError):
        requested_limit = 18
        warnings.append("搜索次数上限无效，已使用 18")
    if not 4 <= requested_limit <= 30:
        warnings.append("搜索次数上限已限制在 4 到 30")
        requested_limit = min(30, max(4, requested_limit))

    country_code = normalized["location"]["country"]
    profiles = load_country_profiles()
    profile = profiles["countries"].get(country_code, profiles["default"]) if country_code else profiles["default"]
    all_queries = build_queries(normalized, country_code)
    local_languages = [
        language
        for language in profile.get("languages", [])
        if language != "en"
    ]
    mandatory: list[dict[str, Any]] = []
    for language in local_languages:
        candidates = [item for item in all_queries if item["language"] == language]
        if candidates:
            mandatory.append(max(candidates, key=lambda item: item["priority"]))
    community = [item for item in all_queries if item["category"] == "community_platform"]
    if normalized["company"].get("name") and requested_limit >= 6:
        mandatory.extend(community[:2])
    elif normalized["company"].get("name") and requested_limit >= 4 and not mandatory:
        mandatory.extend(community[:1])
    if normalized["company"].get("name") and normalized["role"].get("title"):
        exact_interviews = [item for item in all_queries if item["category"] == "interview_exact"]
        if exact_interviews:
            mandatory.append(exact_interviews[0])
    selected_query_keys = {(item["language"], item["query"]) for item in mandatory}
    queries = list({(item["language"], item["query"]): item for item in mandatory}.values())
    for item in sorted(all_queries, key=lambda entry: (-entry["priority"], entry["language"])):
        key = (item["language"], item["query"])
        if len(queries) >= requested_limit:
            break
        if key not in selected_query_keys:
            queries.append(item)
            selected_query_keys.add(key)
    queries = sorted(queries, key=lambda entry: (-entry["priority"], entry["language"], entry["query"]))
    for index, item in enumerate(queries, start=1):
        item["id"] = f"Q{index:03d}"
    selected_languages = []
    for item in queries:
        if item["language"] not in selected_languages:
            selected_languages.append(item["language"])
    selected_sources = route_sources(country_code, selected_languages)

    supplied_identifiers = []
    if normalized["company"].get("website"):
        supplied_identifiers.append("公司官网")
    if normalized["role"].get("url"):
        supplied_identifiers.append("岗位链接")
    entity_status = ("not_applicable" if not normalized["company"]["name"] else
                     "probable" if supplied_identifiers else "unverified")
    questions: list[str] = []
    if normalized["company"]["name"] and not supplied_identifiers and not country_code:
        questions.append("若搜索结果中出现多个同名雇主，需确认公司官网或岗位链接后再归因。")
    scaffold = {
        "schema_version": SCHEMA_VERSION,
        "request": normalized,
        "research": {
            "network_status": network_status,
            "search_completed_at": "YYYY-MM-DD",
            "languages_attempted": [],
            "entity": {
                "status": ("not_applicable" if not normalized["company"]["name"] else
                           "probable" if supplied_identifiers else "ambiguous"),
                "name": normalized["company"]["name"],
                "basis": " | ".join(supplied_identifiers) or "",
            },
            "coverage": {
                "queries_attempted": [], "sources_attempted": [], "failed_attempts": [],
                "community_required": bool(normalized["company"].get("name")),
                "community_attempts": [],
            },
        },
        "evidence": [],
        "findings": [],
        "interviewers": [],
        "interview_experiences": [],
        "similar_companies": [],
        "market": {
            "currency": profile.get("currency"),
            "location": ", ".join(
                item for item in [normalized["location"].get("city"), country_code] if item
            ) or None,
            "salary_observations": [],
            "benchmark_note": "",
        },
        "summary": {
            "company_view": "",
            "opportunity_finding_ids": [],
            "risk_finding_ids": [],
            "experience_note": "",
            "top_topics": [],
            "unresolved_questions": [],
        },
        "interview_prep": {
            "priorities": [],
            "questions": [],
            "star_framework": "",
            "candidate_fit": {
                "strengths": [],
                "gaps": [],
                "evidence": [],
                "not_disclosed": "用户未提供可用的简历摘要或技能背景" if not normalized["candidate"].get("summary") else "",
            },
            "questions_to_ask": [],
            "negotiation_notes": [],
            "final_checklist": [],
        },
        "interaction": {
            "recommended_scene": "auto",
            "default_difficulty": _default_difficulty(normalized["role"].get("level")),
            "questions_per_session": 10,
        },
        "sources_consulted": [],
        "assessment": {"metrics": []},
    }

    return {
        "product": "Interview Intel",
        "version": PRODUCT_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "network_status": network_status,
        "request": normalized,
        "country_code": country_code,
        "country_profile": {
            "name_zh": profile.get("name_zh"),
            "languages": profile.get("languages", []),
            "currency": profile.get("currency"),
        },
        "entity_resolution": {
            "status": entity_status,
            "supplied_identifiers": supplied_identifiers,
            "confirmation_questions": questions,
        },
        "languages_planned": selected_languages,
        "queries": queries,
        "sources": selected_sources,
        "community_targets": _community_targets(country_code) if normalized["company"].get("name") else [],
        "interview_strategy": {
            "company": normalized["company"].get("name"),
            "role": normalized["role"].get("title"),
            "supplied_similar_companies": normalized.get("similar_companies", []),
            "question_mix": _recommended_question_mix(
                normalized["role"].get("title"),
                normalized["company"].get("industry"),
            ),
            "selection_order": [
                "1_same_company_same_role_recent",
                "2_same_company_similar_role",
                "3_similar_company_same_role",
                "4_role_and_jd_prediction",
            ],
        },
        "warnings": warnings,
        "stopping_rule": "公司身份核实后必须尝试至少两个独立职场社区或社交平台，记录实际查询词与访问失败。面经优先使用本公司同岗位原帖；不足时按相近岗位、相似公司、岗位预测逐级降级，并清晰标注来源级别。",
        "scaffold": scaffold,
    }


def _canonical_url(raw_url: str) -> str:
    parts = urlsplit(raw_url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), path, urlencode(sorted(query)), ""))


def _valid_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    return parts.scheme in {"http", "https"} and bool(parts.netloc)


def _valid_date(value: Any) -> bool:
    if value in {None, ""}:
        return True
    if not isinstance(value, str):
        return False
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _contains_prompt_injection(value: str) -> bool:
    return any(pattern.search(value) for pattern in PROMPT_INJECTION_PATTERNS)


def _redact_sensitive_text(value: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    redacted = value
    replacement, count = EMAIL_PATTERN.subn("[已脱敏：电子邮箱]", redacted)
    if count:
        redacted = replacement
        flags.append("电子邮箱")
    replacement, count = PHONE_PATTERN.subn("[已脱敏：私人电话]", redacted)
    if count:
        redacted = replacement
        flags.append("私人电话")
    replacement, count = ADDRESS_PATTERN.subn("[已脱敏：私人地址]", redacted)
    if count:
        redacted = replacement
        flags.append("私人地址")
    return redacted, flags


def _sanitize_structure(
    value: Any,
    path: str,
    issues: list[str],
    warnings: list[str],
    key: str | None = None,
) -> Any:
    if isinstance(value, dict):
        return {
            item_key: _sanitize_structure(
                item_value,
                f"{path}.{item_key}" if path else item_key,
                issues,
                warnings,
                item_key,
            )
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [
            _sanitize_structure(item, f"{path}[{index}]", issues, warnings, key)
            for index, item in enumerate(value)
        ]
    if not isinstance(value, str):
        return value
    if key in {"url", "profile_url", "home_url"} or value.startswith(("http://", "https://")):
        return value
    if _contains_prompt_injection(value):
        issues.append(f"{path} 含疑似网页提示词注入，已拒绝作为研究内容")
    redacted, flags = _redact_sensitive_text(value)
    if flags:
        warnings.append(f"{path} 含与求职无关的{('、'.join(flags))}，已自动脱敏")
    return redacted


def source_trust(source_type: str, access_status: str) -> str:
    if access_status != "verified":
        return "low"
    if source_type in {"official", "official_filing", "first_party"}:
        return "high"
    if source_type in {"job_posting", "professional_profile", "news", "interview_report", "aggregator"}:
        return "medium"
    return "low"


def _evidence_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in data.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _eligible_evidence(ids: list[str], evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        evidence[item_id]
        for item_id in ids
        if item_id in evidence and evidence[item_id].get("access_status") == "verified"
    ]


def _confidence_ceiling(source_items: list[dict[str, Any]]) -> str:
    if not source_items:
        return "low"
    trusts = [source_trust(item["source_type"], item["access_status"]) for item in source_items]
    if "high" in trusts:
        return "high"
    if "medium" in trusts:
        return "medium"
    independent = {item.get("independence_group") for item in source_items}
    if len(independent) >= 2:
        return "medium"
    return "low"


def _entity_name_key(value: Any) -> str:
    return re.sub(r"[\s\W_]+", "", str(value or "").casefold(), flags=re.UNICODE)


def _same_entity_name(left: Any, right: Any) -> bool:
    left_key = _entity_name_key(left)
    right_key = _entity_name_key(right)
    if not left_key or not right_key:
        return False
    return left_key == right_key or left_key in right_key or right_key in left_key


def _question_fingerprint(value: Any) -> str:
    return re.sub(r"[\s\W_]+", "", str(value or "").casefold(), flags=re.UNICODE)


def _valid_interview_date(value: Any) -> bool:
    """Accept a full ISO date/time or the month precision commonly used in interview posts."""
    if value in {None, ""}:
        return True
    if not isinstance(value, str):
        return False
    return bool(
        re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", value)
        or _valid_date(value)
    )


def _normalize_question(
    question: dict[str, Any],
    index: int,
    *,
    legacy: bool,
) -> dict[str, Any]:
    normalized = copy.deepcopy(question)
    normalized.setdefault("id", f"IQ{index:03d}")
    normalized.setdefault("category", "professional_knowledge")
    normalized.setdefault("source_level", 4)
    normalized.setdefault("origin_type", "prediction")
    normalized.setdefault("competencies", ["岗位核心能力"])
    normalized.setdefault("answer_structure", normalized.get("answer_outline", ""))
    normalized.setdefault("source_company", None)
    normalized.setdefault("source_role", None)
    normalized.setdefault("migration_rationale", None)
    normalized["_legacy_shape"] = legacy
    return normalized


def _validate_interview_research(
    data: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    issues: list[str],
    warnings: list[str],
) -> None:
    request = data.get("request", {})
    request_company = request.get("company", {}).get("name")
    request_role = request.get("role", {}).get("title")
    experiences = data.get("interview_experiences", [])
    if not isinstance(experiences, list):
        issues.append("interview_experiences 必须是数组")
        experiences = []
    seen_experience_ids: set[str] = set()
    available_levels: set[int] = set()
    experience_question_fingerprints: dict[int, set[str]] = {}
    for index, experience in enumerate(experiences):
        prefix = f"interview_experiences[{index}]"
        if not isinstance(experience, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        experience_id = experience.get("id")
        if not isinstance(experience_id, str) or not re.fullmatch(r"I[0-9]{3,}", experience_id):
            issues.append(f"{prefix}.id 必须使用 I001 形式")
            continue
        if experience_id in seen_experience_ids:
            issues.append(f"面经 ID 重复: {experience_id}")
            continue
        seen_experience_ids.add(experience_id)
        level = experience.get("source_level")
        if level not in INTERVIEW_SOURCE_LEVELS:
            issues.append(f"{experience_id}.source_level 必须为 1-4")
            continue
        ids = experience.get("evidence_ids", [])
        if not isinstance(ids, list) or not ids:
            issues.append(f"{experience_id} 必须关联至少一条公开面经证据")
            ids = []
        missing = [item_id for item_id in ids if item_id not in evidence]
        if missing:
            issues.append(f"{experience_id} 引用不存在证据: {', '.join(missing)}")
        eligible = _eligible_evidence(ids, evidence)
        if not eligible:
            issues.append(f"{experience_id} 没有可验证的已打开面经证据")
        if level in {1, 2, 3} and eligible and not any(
            item.get("source_type") in {"interview_report", "forum_post", "social_post", "employee_review"}
            for item in eligible
        ):
            issues.append(f"{experience_id} 需要来自公开面经、论坛、社交媒体或员工评价的原帖证据")
        if not _valid_date(experience.get("published_at")):
            issues.append(f"{experience_id}.published_at 必须是 ISO 日期或留空")
        if not _valid_interview_date(experience.get("interview_date")):
            issues.append(
                f"{experience_id}.interview_date 必须是 ISO 日期、年月或留空"
            )
        source_company = experience.get("company")
        source_role = experience.get("role")
        source_questions = experience.get("questions", [])
        if not isinstance(source_questions, list) or not all(
            isinstance(item, str) and item.strip() for item in source_questions
        ):
            issues.append(f"{experience_id}.questions 必须是字符串数组")
            source_questions = []
        elif eligible and source_questions:
            available_levels.add(level)
            experience_question_fingerprints.setdefault(level, set()).update(
                _question_fingerprint(item) for item in source_questions
            )
        if level in {1, 2} and request_company and not _same_entity_name(source_company, request_company):
            issues.append(f"{experience_id} 属于本公司级别，company 必须与请求公司一致")
        if not request_company and level in {1, 2}:
            issues.append(f"{experience_id} 没有请求公司时不能使用本公司专属来源级别")
        if level == 1 and request_role and not _same_entity_name(source_role, request_role):
            issues.append(f"{experience_id} 属于相同岗位级别，role 必须与请求岗位一致")
        if level == 2 and not (
            (isinstance(experience.get("role_relation"), str) and experience["role_relation"].strip())
            or (isinstance(experience.get("match_rationale"), str) and experience["match_rationale"].strip())
        ):
            issues.append(f"{experience_id} 作为相近岗位参考时必须说明角色相关性")
        if level == 3:
            similar_company = experience.get("similar_company") or source_company
            rationale = experience.get("match_rationale")
            if not similar_company or not isinstance(rationale, str) or not rationale.strip():
                issues.append(f"{experience_id} 作为相似公司参考时必须填写 similar_company 和 match_rationale")
            normalized_similar = {
                _entity_name_key(item.get("name"))
                for item in data.get("similar_companies", [])
                if isinstance(item, dict)
            }
            if similar_company and _entity_name_key(similar_company) not in normalized_similar:
                issues.append(f"{experience_id}.similar_company 必须出现在 similar_companies 中")
        if level == 4 and source_company and request_company and not _same_entity_name(source_company, request_company):
            issues.append(f"{experience_id} 属于行业通用级别，不得把其他公司问题伪装成本公司原题")

    similar_companies = data.get("similar_companies", [])
    if not isinstance(similar_companies, list):
        issues.append("similar_companies 必须是数组")
        similar_companies = []
    for index, company in enumerate(similar_companies):
        prefix = f"similar_companies[{index}]"
        if not isinstance(company, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        if not isinstance(company.get("name"), str) or not company["name"].strip():
            issues.append(f"{prefix}.name 必填")
        if not isinstance(company.get("match_rationale"), str) or not company["match_rationale"].strip():
            issues.append(f"{prefix}.match_rationale 必填，需说明行业、业务或岗位相关性")
        ids = company.get("evidence_ids", [])
        if not isinstance(ids, list) or not ids:
            issues.append(f"{prefix}.evidence_ids 必填")
        elif not _eligible_evidence(ids, evidence):
            issues.append(f"{prefix} 没有可验证的相似公司依据")

    prep = data.get("interview_prep", {})
    if not isinstance(prep, dict):
        issues.append("interview_prep 必须是对象")
        return
    raw_questions = prep.get("questions")
    legacy = False
    if raw_questions is None:
        raw_questions = prep.get("mock_questions", [])
        legacy = True
    if not isinstance(raw_questions, list):
        issues.append("interview_prep.questions 必须是数组")
        return
    questions = [
        _normalize_question(item, index, legacy=legacy)
        for index, item in enumerate(raw_questions, start=1)
        if isinstance(item, dict)
    ]
    if legacy:
        category_mix = _recommended_question_mix(
            request_role,
            request.get("company", {}).get("industry"),
        )
        for index, question in enumerate(questions):
            question["category"] = category_mix[index % len(category_mix)]
    prep["questions"] = questions
    if len(questions) != len(raw_questions):
        issues.append("所有模拟问题必须是对象")
        return
    if data.get("research", {}).get("network_status") in {"available", "partial"} and request_role:
        if len(questions) != 10:
            issues.append("可用网络状态下 interview_prep.questions 必须正好有 10 个问题")
        seen_questions: set[str] = set()
        categories: set[str] = set()
        levels_in_bank: set[int] = set()
        for index, question in enumerate(questions, start=1):
            prefix = f"questions[{index - 1}]"
            for field in ["question", "basis", "answer_outline"]:
                if not isinstance(question.get(field), str) or not question[field].strip():
                    issues.append(f"{prefix}.{field} 必须是非空字符串")
            category = question.get("category")
            if not isinstance(category, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", category):
                issues.append(f"{prefix}.category 必须使用英文蛇形分类")
            else:
                categories.add(category)
            level = question.get("source_level")
            if level not in INTERVIEW_SOURCE_LEVELS:
                issues.append(f"{prefix}.source_level 必须为 1-4")
            else:
                levels_in_bank.add(level)
            origin = question.get("origin_type")
            if origin not in INTERVIEW_ORIGIN_TYPES:
                issues.append(f"{prefix}.origin_type 无效")
                continue
            expected_origin = {
                1: "historical_exact",
                2: "historical_similar_role",
                3: "similar_company",
                4: "prediction",
            }[level] if level in INTERVIEW_SOURCE_LEVELS else None
            if not legacy and origin != expected_origin:
                issues.append(f"{prefix}.source_level 与 origin_type 不一致")
            if not legacy and level in {1, 2} and request_company and not _same_entity_name(
                question.get("source_company"), request_company
            ):
                issues.append(f"{prefix} 的本公司来源与请求公司不一致")
            if not legacy and level == 1 and request_role and not _same_entity_name(
                question.get("source_role"), request_role
            ):
                issues.append(f"{prefix} 标为历史原题时 source_role 必须与请求岗位一致")
            if not legacy and level == 3:
                if _same_entity_name(question.get("source_company"), request_company):
                    issues.append(f"{prefix} 属于相似公司级别，不得标成本公司来源")
                if not question.get("migration_rationale"):
                    issues.append(f"{prefix} 属于相似公司题目，必须说明迁移局限")
                similar_names = {
                    _entity_name_key(item.get("name"))
                    for item in similar_companies
                    if isinstance(item, dict)
                }
                if _entity_name_key(question.get("source_company")) not in similar_names:
                    issues.append(f"{prefix}.source_company 必须在 similar_companies 中声明")
            if not legacy and level == 4 and question.get("source_company") and request_company and _same_entity_name(
                question.get("source_company"), request_company
            ):
                issues.append(f"{prefix} AI 预测题不得伪装成本公司历史原题")
            competencies = question.get("competencies")
            if not isinstance(competencies, list) or not competencies or not all(
                isinstance(item, str) and item.strip() for item in competencies
            ):
                issues.append(f"{prefix}.competencies 必须是非空字符串数组")
            if not isinstance(question.get("answer_structure"), str) or not question["answer_structure"].strip():
                issues.append(f"{prefix}.answer_structure 必须是非空字符串")
            ids = question.get("evidence_ids", [])
            if not isinstance(ids, list) or not ids:
                issues.append(f"{prefix} 缺少 evidence_ids")
            elif not _eligible_evidence(ids, evidence):
                issues.append(f"{prefix} 没有可验证的证据支持")
            fingerprint = _question_fingerprint(question.get("question"))
            if not fingerprint:
                issues.append(f"{prefix}.question 无法标准化")
            elif fingerprint in seen_questions:
                issues.append(f"{prefix} 与其他模拟问题重复")
            else:
                seen_questions.add(fingerprint)
            if (
                not legacy
                and level in {1, 2, 3}
                and fingerprint
                and fingerprint not in experience_question_fingerprints.get(level, set())
            ):
                issues.append(
                    f"{prefix} 标为历史题，但未在对应级别的公开面经中找到原问题"
                )
            if legacy:
                question["origin_type"] = "prediction"
                question["source_level"] = 4
        if not legacy and len(categories) < 3:
            issues.append("十个模拟问题至少需要三种不同题型")
        if available_levels:
            best_level = min(available_levels)
            if best_level not in levels_in_bank:
                issues.append(
                    f"存在 source_level={best_level} 的公开面经，但十个模拟问题没有优先采用该级别"
                )
        elif not legacy and any(level != 4 for level in levels_in_bank):
            issues.append("没有可验证公开面经时，所有题目必须标为 source_level=4 的预测题")
        if legacy:
            warnings.append("旧版 mock_questions 已按 source_level=4 的预测题兼容处理")


def _deduplicate_evidence(data: dict[str, Any], issues: list[str], warnings: list[str]) -> dict[str, Any]:
    output = copy.deepcopy(data)
    evidence = output.get("evidence")
    if not isinstance(evidence, list):
        issues.append("evidence 必须是数组")
        return output

    id_to_canonical: dict[str, str] = {}
    canonical_to_item: dict[str, dict[str, Any]] = {}
    deduplicated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(evidence):
        prefix = f"evidence[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not re.fullmatch(r"E[0-9]{3,}", evidence_id):
            issues.append(f"{prefix}.id 必须使用 E001 形式")
            continue
        if evidence_id in seen_ids:
            issues.append(f"证据 ID 重复: {evidence_id}")
            continue
        seen_ids.add(evidence_id)
        for field in ["title", "platform", "source_type", "retrieved_at", "excerpt", "access_status", "independence_group"]:
            if not isinstance(item.get(field), str) or not item[field].strip():
                issues.append(f"{evidence_id}.{field} 必须是非空字符串")
        if item.get("source_type") not in SOURCE_TYPES:
            issues.append(f"{evidence_id}.source_type 无效")
        if item.get("access_status") not in ACCESS_STATUSES:
            issues.append(f"{evidence_id}.access_status 无效")
        if not _valid_http_url(item.get("url")):
            issues.append(f"{evidence_id}.url 必须是真实格式的 http(s) URL")
            continue
        if not _valid_date(item.get("published_at")):
            issues.append(f"{evidence_id}.published_at 必须是 ISO 日期或日期时间")
        if not _valid_date(item.get("retrieved_at")):
            issues.append(f"{evidence_id}.retrieved_at 必须是 ISO 日期或日期时间")
        supports = item.get("supports", [])
        if not isinstance(supports, list) or not all(isinstance(value, str) for value in supports):
            issues.append(f"{evidence_id}.supports 必须是字符串数组")
            item["supports"] = []

        canonical = _canonical_url(item["url"])
        if canonical in canonical_to_item:
            original = canonical_to_item[canonical]
            id_to_canonical[evidence_id] = original["id"]
            merged_supports = sorted(set(original.get("supports", [])) | set(item.get("supports", [])))
            original["supports"] = merged_supports
            if not original.get("limitations") and item.get("limitations"):
                original["limitations"] = item["limitations"]
            warnings.append(f"已合并且去掉重复 URL：{evidence_id} → {original['id']}")
            continue
        item["url"] = canonical
        item.setdefault("supports", [])
        item.setdefault("limitations", "")
        item.setdefault("published_at", None)
        item.setdefault("published_at_precision", "unknown")
        item.setdefault("language", "und")
        canonical_to_item[canonical] = item
        id_to_canonical[evidence_id] = evidence_id
        deduplicated.append(item)
    output["evidence"] = deduplicated

    def remap_ids(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return list(dict.fromkeys(id_to_canonical.get(value, value) for value in values if isinstance(value, str)))

    for collection_name in ["findings"]:
        collection = output.get(collection_name, [])
        if isinstance(collection, list):
            for finding in collection:
                if isinstance(finding, dict):
                    finding["evidence_ids"] = remap_ids(finding.get("evidence_ids", []))
    for person in output.get("interviewers", []):
        if isinstance(person, dict):
            person["evidence_ids"] = remap_ids(person.get("evidence_ids", []))
    for experience in output.get("interview_experiences", []):
        if isinstance(experience, dict):
            experience["evidence_ids"] = remap_ids(experience.get("evidence_ids", []))
    for company in output.get("similar_companies", []):
        if isinstance(company, dict):
            company["evidence_ids"] = remap_ids(company.get("evidence_ids", []))
    for observation in output.get("market", {}).get("salary_observations", []):
        if isinstance(observation, dict):
            observation["evidence_ids"] = remap_ids(observation.get("evidence_ids", []))
    prep = output.get("interview_prep", {})
    if isinstance(prep, dict):
        for key in ["questions", "mock_questions"]:
            for question in prep.get(key, []):
                if isinstance(question, dict):
                    question["evidence_ids"] = remap_ids(question.get("evidence_ids", []))
    return output


def validate_research(data: dict[str, Any], warnings_out: list[str] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = warnings_out if warnings_out is not None else []
    if not isinstance(data, dict):
        raise IntelValidationError(["研究文件必须是 JSON 对象"])
    data = _sanitize_structure(data, "", issues, warnings)
    if data.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version 必须为 {SCHEMA_VERSION}")
    normalized_data = _deduplicate_evidence(data, issues, warnings)
    research = normalized_data.get("research")
    if not isinstance(research, dict):
        issues.append("research 必须是对象")
        research = {}
    network_status = research.get("network_status")
    if network_status not in NETWORK_STATUSES:
        issues.append("research.network_status 无效")
    if not _valid_date(research.get("search_completed_at")) or not research.get("search_completed_at"):
        issues.append("research.search_completed_at 必须是有效 ISO 日期")
    languages = research.get("languages_attempted")
    if not isinstance(languages, list) or not all(isinstance(item, str) for item in languages):
        issues.append("research.languages_attempted 必须是字符串数组")
    elif network_status in {"available", "partial"}:
        request = normalized_data.get("request", {})
        country_code = request.get("location", {}).get("country")
        profiles = load_country_profiles()
        profile = profiles["countries"].get(country_code) if country_code else None
        expected_local = [
            language
            for language in (profile or {}).get("languages", [])
            if language != "en"
        ]
        if expected_local and not set(expected_local).intersection(languages):
            warnings.append(
                "研究计划包含非英语国家，但 languages_attempted 未记录本地语言尝试: "
                + ", ".join(expected_local)
            )
    entity = research.get("entity")
    if not isinstance(entity, dict) or entity.get("status") not in {"confirmed", "probable", "ambiguous", "not_found", "not_applicable"}:
        issues.append("research.entity.status 无效")
    elif entity.get("status") == "not_applicable" and normalized_data.get("request", {}).get("company", {}).get("name"):
        issues.append("提供公司名称时不得使用 not_applicable 实体状态")
    elif entity.get("status") in {"ambiguous", "not_found"}:
        claim_findings = [
            finding.get("id", f"index-{index}")
            for index, finding in enumerate(normalized_data.get("findings", []))
            if isinstance(finding, dict) and finding.get("kind") not in {"gap", "advice"}
        ]
        if claim_findings:
            issues.append(
                "公司实体状态为 ambiguous 或 not_found 时，不得输出事实、评价或预测: "
                + ", ".join(claim_findings)
            )
    coverage = research.get("coverage")
    if not isinstance(coverage, dict):
        issues.append("research.coverage 必须是对象")

    evidence = _evidence_map(normalized_data)
    findings = normalized_data.get("findings")
    if not isinstance(findings, list):
        issues.append("findings 必须是数组")
        findings = []
    seen_finding_ids: set[str] = set()
    for index, finding in enumerate(findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not re.fullmatch(r"F[0-9]{3,}", finding_id):
            issues.append(f"{prefix}.id 必须使用 F001 形式")
            continue
        if finding_id in seen_finding_ids:
            issues.append(f"结论 ID 重复: {finding_id}")
        seen_finding_ids.add(finding_id)
        if finding.get("section") not in {item[0] for item in SECTION_ORDER} | {"interviewer"}:
            issues.append(f"{finding_id}.section 无效")
        kind = finding.get("kind")
        if kind not in FINDING_KINDS:
            issues.append(f"{finding_id}.kind 无效")
            continue
        if not isinstance(finding.get("statement"), str) or not finding["statement"].strip():
            issues.append(f"{finding_id}.statement 必须是非空字符串")
        ids = finding.get("evidence_ids", [])
        if not isinstance(ids, list) or not all(isinstance(value, str) for value in ids):
            issues.append(f"{finding_id}.evidence_ids 必须是字符串数组")
            ids = []
        missing = [value for value in ids if value not in evidence]
        if missing:
            issues.append(f"{finding_id} 引用不存在证据: {', '.join(missing)}")
        source_items = _eligible_evidence(ids, evidence)
        if kind in {"fact", "person_statement", "third_party_assessment"} and not source_items:
            issues.append(f"{finding_id} 属于 {kind}，但没有可验证来源支持")
        if kind in {"inference", "prediction"}:
            if not finding.get("basis"):
                issues.append(f"{finding_id} 属于 {kind}，必须填写 basis")
            if not source_items:
                issues.append(f"{finding_id} 属于 {kind}，但没有任何可验证证据作为推断基础")
        if kind == "gap" and ids:
            issues.append(f"{finding_id} 是信息缺口，不应引用支持性证据")
        if kind == "advice" and not finding.get("statement"):
            issues.append(f"{finding_id} 缺少准备建议内容")
        confidence = finding.get("confidence")
        if confidence not in CONFIDENCE:
            issues.append(f"{finding_id}.confidence 无效")
        elif kind not in {"gap", "advice"}:
            ceiling = _confidence_ceiling(source_items)
            ranks = {"low": 0, "medium": 1, "high": 2}
            if ranks[confidence] > ranks[ceiling]:
                finding["confidence"] = ceiling
                warnings.append(f"{finding_id} 可信度从 {confidence} 降为 {ceiling}，依据为实际来源类型与独立性")

    _validate_interview_research(normalized_data, evidence, issues, warnings)

    market = normalized_data.get("market", {})
    if not isinstance(market, dict):
        issues.append("market 必须是对象")
        market = {}
    observations = market.get("salary_observations", [])
    if not isinstance(observations, list):
        issues.append("market.salary_observations 必须是数组")
        observations = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            issues.append(f"market.salary_observations[{index}] 必须是对象")
            continue
        ids = observation.get("evidence_ids", [])
        if not isinstance(ids, list) or not ids:
            issues.append(f"market.salary_observations[{index}] 缺少 evidence_ids")
        for numeric in ["min", "p25", "median", "p90", "max", "sample_size"]:
            value = observation.get(numeric)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
                issues.append(f"market.salary_observations[{index}].{numeric} 必须是非负数或 null")
        if observation.get("min") is not None and observation.get("max") is not None:
            if observation["min"] > observation["max"]:
                issues.append(f"market.salary_observations[{index}] 的 min 大于 max")
        ordered_values = [
            observation.get(field)
            for field in ["min", "p25", "median", "p90", "max"]
            if observation.get(field) is not None
        ]
        if ordered_values != sorted(ordered_values):
            issues.append(f"market.salary_observations[{index}] 的薪酬分位数值顺序不正确")

    summary = normalized_data.get("summary")
    if not isinstance(summary, dict):
        issues.append("summary 必须是对象")
        summary = {}
    for field in ["opportunity_finding_ids", "risk_finding_ids"]:
        ids = summary.get(field, [])
        if not isinstance(ids, list):
            issues.append(f"summary.{field} 必须是数组")
            continue
        missing = [value for value in ids if value not in seen_finding_ids]
        if missing:
            issues.append(f"summary.{field} 引用不存在结论: {', '.join(missing)}")

    if network_status in {"unavailable", "failed"}:
        for collection_name in ["evidence", "findings", "interview_experiences"]:
            if normalized_data.get(collection_name):
                issues.append(f"网络状态为 {network_status} 时不得输出 {collection_name}")
        if observations:
            issues.append(f"网络状态为 {network_status} 时不得输出薪酬观察")
        prep = normalized_data.get("interview_prep", {})
        if isinstance(prep, dict) and (prep.get("questions") or prep.get("mock_questions")):
            issues.append(f"网络状态为 {network_status} 时不得输出模拟问题")

    validate_assessment(normalized_data, issues)
    _validate_community_attempts(normalized_data, issues)
    if issues:
        raise IntelValidationError(issues)
    normalized_data["_validation_warnings"] = warnings
    return normalized_data


def _md_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).replace("\x00", "").strip()


def _with_period(value: Any) -> str:
    text = _md_text(value).rstrip("。；;.!? ")
    return f"{text}。" if text else ""


def _join_zh(values: Iterable[Any], separator: str = "；") -> str:
    cleaned = [_md_text(value).rstrip("。；; ") for value in values]
    return separator.join(item for item in cleaned if item)


def _finding_index(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in findings}


def _render_finding(finding: dict[str, Any]) -> str:
    label = KIND_LABELS[finding["kind"]]
    confidence = TRUST_LABELS.get(finding.get("confidence"), "未定")
    refs = " ".join(f"[{item}](#{item.lower()})" for item in finding.get("evidence_ids", []))
    suffix = f" {refs}" if refs else ""
    basis = f" 依据：{_with_period(finding.get('basis'))}" if finding.get("basis") else ""
    limitation = f" 限制：{_with_period(finding.get('limitations'))}" if finding.get("limitations") else ""
    statement = finding["statement"].rstrip("。；; ")
    return f"- **{label} · 可信度{confidence}**：{_md_text(statement)}。{suffix}{basis}{limitation}"


def render_report(data: dict[str, Any]) -> str:
    warnings: list[str] = []
    data = validate_research(data, warnings)
    request = data.get("request", {})
    company = _md_text(request.get("company", {}).get("name"), "公司未提供")
    role = _md_text(request.get("role", {}).get("title"), "岗位未提供")
    research = data["research"]
    country = _md_text(request.get("location", {}).get("country"), "全球")
    city = _md_text(request.get("location", {}).get("city"))
    location = ", ".join(item for item in [city, country] if item)
    search_date = _md_text(research.get("search_completed_at"))
    network = research.get("network_status")

    lines: list[str] = [
        f"# {company} · {role} 面试情报报告",
        "",
        f"> 检索日期：{search_date}　地点：{location}　网络状态：`{network}`　报告版本：Interview Intel v{PRODUCT_VERSION}",
        "",
    ]
    if network in {"unavailable", "failed"}:
        lines.extend(
            [
                "## 检索限制",
                "",
                "本次无法使用外部搜索或公开页面访问能力，因此没有生成公司、岗位、薪酬或员工评价事实。以下研究计划和缺口可供后续重试。",
                "",
                "未找到可靠公开证据。",
                "",
            ]
        )
        for key, title in SECTION_ORDER:
            if request.get("quick_mode") and ((key in {"company", "reviews"} and not request.get("company", {}).get("name")) or (key in {"role", "prep"} and not request.get("role", {}).get("title"))):
                continue
            lines.extend([f"## {title}", "", "未找到可靠公开证据。", ""])
        lines.extend(["## 6. 来源与可信度", "", "本次未采集任何在线来源。", ""])
        return "\n".join(lines).rstrip() + "\n"

    findings = data.get("findings", [])
    indexed = _finding_index(findings)
    by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        by_section[finding["section"]].append(finding)
    summary = data.get("summary", {})

    def summary_refs(field: str) -> str:
        refs = []
        for finding_id in summary.get(field, []):
            finding = indexed.get(finding_id)
            if finding:
                refs.append(f"- {_md_text(finding['statement'])} [{finding_id}](#{finding_id.lower()})")
        return "\n".join(refs) if refs else "- 未找到可靠公开证据。"

    lines.extend(
        [
            "## 一页式摘要",
            "",
            *(render_score_lines(data) if data.get("assessment", {}).get("show_score") is True else []),
            f"**公司判断**：{_md_text(summary.get('company_view'), '未找到可靠公开证据。')}",
            "",
            "**岗位机会**",
            "",
            summary_refs("opportunity_finding_ids"),
            "",
            "**主要风险**",
            "",
            summary_refs("risk_finding_ids"),
            "",
            f"**历史面经概况**：{_md_text(summary.get('experience_note'), '未找到可核验的公司与岗位面经。')}",
            "",
            "**最应准备的主题**",
            "",
        ]
    )
    topics = summary.get("top_topics", [])
    if topics:
        for topic in topics:
            lines.append(f"- {_md_text(topic)}")
    else:
        lines.append("- 未找到可靠公开证据。")
    lines.extend(["", "**仍无法确认**", ""])
    unresolved = summary.get("unresolved_questions", [])
    if unresolved:
        for item in unresolved:
            lines.append(f"- {_md_text(item)}")
    else:
        lines.append("- 未列出额外信息缺口。")
    lines.append("")

    for section_key, title in SECTION_ORDER:
        if request.get("quick_mode"):
            if section_key in {"company", "reviews"} and not request.get("company", {}).get("name"):
                continue
            if section_key in {"role", "prep"} and not request.get("role", {}).get("title"):
                continue
        lines.extend([f"## {title}", ""])
        if section_key == "reviews":
            attempts = research.get("coverage", {}).get("community_attempts", [])
            lines.extend(["### 社交平台与职场社区检索情况", ""])
            if attempts:
                lines.extend(["| 平台 | 检索结果 | 采用的原帖证据 |", "|---|---|---|"])
                statuses = {
                    "found": "已核实原帖", "blocked": "访问受限",
                    "login_required": "需要登录", "snippet_only": "仅搜索摘要",
                    "no_results": "未找到结果", "irrelevant": "结果不相关",
                    "error": "检索失败",
                }
                for attempt in attempts:
                    refs = " ".join(f"[{eid}](#{eid.lower()})" for eid in attempt.get("evidence_ids", []))
                    lines.append(f"| {_md_text(attempt.get('platform_id'))} | {statuses.get(attempt.get('result'), '未记录')} | {refs or '无'} |")
            else:
                lines.append("未记录可核查的社交平台原帖检索。")
            lines.append("")
            original_posts = [
                e for e in data.get("evidence", [])
                if e.get("source_type") in COMMUNITY_POST_TYPES
                and e.get("access_status") == "verified"
            ]
            if not original_posts:
                lines.extend(["**未核验到可公开访问的员工原帖或评价。** 以下调查只说明检索尝试和证据缺口。", ""])
        section_findings = by_section.get(section_key, [])
        if section_findings:
            for finding in section_findings:
                lines.append(_render_finding(finding))
        else:
            lines.append("- 未找到可靠公开证据。")
        if section_key == "role":
            market = data.get("market", {})
            observations = market.get("salary_observations", [])
            lines.extend(["", "### 薪酬观察", ""])
            if observations:
                for item in observations:
                    values = []
                    for field, label in [
                        ("min", "最低"),
                        ("p25", "25 分位"),
                        ("median", "中位"),
                        ("p90", "90 分位"),
                        ("max", "最高"),
                    ]:
                        if item.get(field) is not None:
                            values.append(f"{label} {item[field]}")
                    sample = item.get("sample_size") if item.get("sample_size") is not None else "未披露"
                    refs = " ".join(
                        f"[{item_id}](#{item_id.lower()})" for item_id in item.get("evidence_ids", [])
                    )
                    lines.append(
                        f"- {_md_text(item.get('label'), '岗位薪酬')}：{'、'.join(values) if values else '源页面未给出可用区间'}"
                        f" {_md_text(item.get('currency') or market.get('currency'))}/{_md_text(item.get('period'), '未注明周期')}；"
                        f"样本量 {sample}；截至 {_md_text(item.get('as_of'), '未披露')}。{refs}"
                    )
                    if item.get("limitations"):
                        lines.append(f"  - 限制：{_md_text(item['limitations'])}")
            else:
                lines.append(f"- {_md_text(market.get('benchmark_note'), '未找到可靠公开证据。')}")
        if section_key == "experiences":
            experiences = data.get("interview_experiences", [])
            similar_companies = data.get("similar_companies", [])
            lines.extend(["", "### 公开面经记录", ""])
            if experiences:
                for experience in experiences:
                    level = experience.get("source_level")
                    refs = " ".join(
                        f"[{item}](#{item.lower()})" for item in experience.get("evidence_ids", [])
                    )
                    meta = [
                        f"来源级别：{EXPERIENCE_LEVEL_LABELS.get(level, '未标注')}",
                        f"公司：{_md_text(experience.get('company'), '未注明')}",
                        f"岗位：{_md_text(experience.get('role'), '未注明')}",
                    ]
                    for field, label in [
                        ("country", "国家"),
                        ("city", "城市"),
                        ("level", "职级"),
                        ("interview_date", "面试时间"),
                        ("published_at", "发布时间"),
                        ("format", "形式"),
                        ("difficulty", "作者自述难度"),
                    ]:
                        if experience.get(field):
                            meta.append(f"{label}：{_md_text(experience.get(field))}")
                    lines.append(f"- {'；'.join(meta)} {refs}")
                    if experience.get("rounds"):
                        rounds = experience["rounds"]
                        if isinstance(rounds, list):
                            lines.append(f"  - 面试轮次：{'；'.join(_md_text(item) for item in rounds)}")
                        else:
                            lines.append(f"  - 面试轮次：{_md_text(rounds)}")
                    if experience.get("questions"):
                        lines.append("  - 原帖明确提到的问题：")
                        lines.extend(f"    - {_md_text(item)}" for item in experience["questions"])
                    if experience.get("author_impression"):
                        lines.append(f"  - 作者自述感受：{_md_text(experience['author_impression'])}")
                    if experience.get("match_rationale"):
                        lines.append(f"  - 匹配或迁移理由：{_md_text(experience['match_rationale'])}")
                    if experience.get("limitations"):
                        lines.append(f"  - 限制：{_md_text(experience['limitations'])}")
            else:
                lines.append("未找到可靠公开面经。以下模拟题只能按岗位和公开 JD 推断。")
            if similar_companies:
                lines.extend(["", "### 相似公司选择", ""])
                for company in similar_companies:
                    refs = " ".join(
                        f"[{item}](#{item.lower()})" for item in company.get("evidence_ids", [])
                    )
                    lines.append(
                        f"- {_md_text(company.get('name'))}：{_md_text(company.get('match_rationale'))} {refs}"
                    )
        if section_key == "prep":
            prep = data.get("interview_prep", {})
            priorities = prep.get("priorities", [])
            if priorities:
                lines.extend(["", "### 准备优先级", ""])
                for value in priorities:
                    lines.append(f"- {_md_text(value)}")
            lines.extend(["", "### 十个模拟问题", ""])
            for index, question in enumerate(prep.get("questions", prep.get("mock_questions", [])), start=1):
                refs = " ".join(
                    f"[{item}](#{item.lower()})" for item in question.get("evidence_ids", [])
                )
                origin_label = QUESTION_ORIGIN_LABELS.get(
                    question.get("origin_type"), "未标注来源"
                )
                category_label = QUESTION_CATEGORY_LABELS.get(
                    question.get("category"), _md_text(question.get("category"), "未分类")
                )
                level = question.get("source_level", 4)
                migration = (
                    f"；迁移限制：{_md_text(question.get('migration_rationale'))}"
                    if question.get("migration_rationale")
                    else ""
                )
                lines.extend(
                    [
                        f"{index}. **{_md_text(question.get('question'))}**",
                        f"   - 题型：{category_label}",
                        f"   - 来源：{origin_label}（{EXPERIENCE_LEVEL_LABELS.get(level, '未标注级别')}）",
                        f"   - 主要考察：{_join_zh(question.get('competencies', []))}",
                        f"   - 依据：{_md_text(question.get('basis'))} {refs}{migration}",
                        f"   - 回答思路：{_md_text(question.get('answer_outline'))}",
                        f"   - 答案结构：{_md_text(question.get('answer_structure'))}",
                    ]
                )
            lines.extend(
                [
                    "",
                    "### 交互式模拟面试",
                    "",
                    "在支持对话的 Agent 中输入“开始模拟面试”。默认从本轮最相关的场景和岗位级别开始，每轮只提出一个问题，并根据回答补充追问。输入“结束面试”可生成本次表现反馈；输入“重新开始”可清空会话。",
                ]
            )
            candidate_fit = prep.get("candidate_fit", {})
            lines.extend(["", "### 经历匹配", ""])
            for field, label in [
                ("strengths", "匹配优势"),
                ("gaps", "待补强"),
                ("evidence", "用户提供并采用的信息"),
            ]:
                values = candidate_fit.get(field, [])
                if values:
                    lines.append(f"- {label}：{_join_zh(values)}")
            if candidate_fit.get("not_disclosed"):
                lines.append(f"- 信息限制：{_md_text(candidate_fit['not_disclosed'])}")
            for field, label in [
                ("star_framework", "STAR 回答框架"),
                ("questions_to_ask", "值得反问的问题"),
                ("negotiation_notes", "薪酬谈判参考"),
                ("final_checklist", "面试前最后检查"),
            ]:
                value = prep.get(field)
                if isinstance(value, list) and value:
                    lines.extend(["", f"### {label}", ""])
                    lines.extend(f"- {_md_text(item)}" for item in value)
                elif isinstance(value, str) and value:
                    lines.extend(["", f"### {label}", "", _md_text(value)])
        lines.append("")

    lines.extend(["## 6. 来源与可信度", ""])
    evidence = data.get("evidence", [])
    if not evidence:
        lines.append("未找到可靠公开证据。")
    else:
        lines.extend(
            [
                "| 证据 ID | 来源 | 类型 | 公开时间 | 访问状态 | 基础可信度 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in evidence:
            trust = source_trust(item["source_type"], item["access_status"])
            published = item.get("published_at") or "未披露"
            lines.append(
                f"| [{item['id']}](#{item['id'].lower()}) | {_md_text(item.get('platform'))} | "
                f"{_md_text(item.get('source_type'))} | {_md_text(published)} | "
                f"{ACCESS_LABELS[item['access_status']]} | {TRUST_LABELS[trust]} |"
            )
        lines.append("")
        lineage_ids: dict[str, list[str]] = defaultdict(list)
        for item in evidence:
            lineage_ids[item["independence_group"]].append(item["id"])
        shared = {key: values for key, values in lineage_ids.items() if len(values) > 1}
        if shared:
            lines.extend(["### 来源独立性提示", ""])
            for lineage, ids in shared.items():
                lines.append(f"- {', '.join(ids)} 同属来源血缘 `{_md_text(lineage)}`，只计为一个独立来源。")
            lines.append("")
        for item in evidence:
            trust = source_trust(item["source_type"], item["access_status"])
            lines.extend(
                [
                    f'<a id="{item["id"].lower()}"></a>',
                    f"### {item['id']} · {_md_text(item.get('title'))}",
                    "",
                    f"- 平台：{_md_text(item.get('platform'))}",
                    f"- 类型：{_md_text(item.get('source_type'))}　基础可信度：{TRUST_LABELS[trust]}　访问状态：{ACCESS_LABELS[item['access_status']]}",
                    f"- 发表日期：{_md_text(item.get('published_at'), '未披露')}　检索日期：{_md_text(item.get('retrieved_at'))}　原文语言：{_md_text(item.get('language'), '未注明')}",
                    f"- 原文关键信息：{_md_text(item.get('excerpt'))}",
                    f"- 原始来源：[打开公开页面]({item['url']})",
                ]
            )
            if item.get("limitations"):
                lines.append(f"- 限制：{_md_text(item['limitations'])}")
            if item.get("supports"):
                lines.append(f"- 对应结论：{', '.join(item['supports'])}")
            lines.append("")

    failed = research.get("coverage", {}).get("failed_attempts", [])
    if failed:
        lines.extend(["### 未能采用的来源", ""])
        for item in failed:
            if isinstance(item, dict):
                lines.append(
                    f"- {_md_text(item.get('url'), '未记录 URL')}：{_md_text(item.get('reason'), '访问失败')}"
                )
            else:
                lines.append(f"- {_md_text(item)}")
        lines.append("")
    if warnings:
        lines.extend(["### 校验提示", ""])
        lines.extend(f"- {_md_text(item)}" for item in warnings)
        lines.append("")
    lines.extend(
        [
            "### 方法与限制",
            "",
            f"- 实际尝试语言：{', '.join(research.get('languages_attempted', [])) or '未记录'}。",
            "- 匿名员工评价、单一社交媒体爆料和搜索摘要均按低可信度处理，不作为已核实事实。",
            "- 同文转载按来源血缘合并，不当作独立交叉验证。",
            "- 每道模拟题都标注历史原题、相近岗位参考、相似公司参考或 AI 预测级别；不得把较低级别题目冒充本公司原题。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def research_fingerprint(data: dict[str, Any]) -> str:
    """Return a stable hash for local deduplication without storing source text separately."""
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
