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
PRODUCT_VERSION = "0.1.0-beta.1"

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
INTERVIEWER_STATUSES = {"confirmed", "probable", "unconfirmed", "not_found"}
NETWORK_STATUSES = {"available", "partial", "unavailable", "failed", "unknown"}
SECTION_ORDER = [
    ("company", "1. 公司概况与综合评价"),
    ("reviews", "2. 员工及社交媒体评价"),
    ("role", "3. 岗位评价"),
    ("interviewer", "4. HR / 面试官公开情报"),
    ("prep", "5. 面试预测与准备"),
]
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
    interviewers = request.get("interviewers", [])
    if not isinstance(interviewers, list):
        warnings.append("interviewers 不是数组，已忽略")
        interviewers = []

    cleaned_interviewers: list[dict[str, Any]] = []
    for index, person in enumerate(interviewers, start=1):
        if not isinstance(person, dict):
            warnings.append(f"第 {index} 位面试官不是对象，已忽略")
            continue
        name = _optional_target(person.get("name"), f"interviewers[{index - 1}].name", issues)
        if not name and _skip_value(person.get("profile_url")):
            warnings.append(f"第 {index} 位面试官缺少姓名和公开主页，已忽略")
            continue
        cleaned_interviewers.append(
            {
                "name": name,
                "title": _clean_optional(person.get("title")),
                "department": _clean_optional(person.get("department")),
                "profile_url": _clean_optional(person.get("profile_url")),
            }
        )

    if not (company_name or role_title or cleaned_interviewers):
        issues.append("国家之外至少需要公司、岗位或面试官中的一项；全部填写 0 无法开展研究")
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
        },
        "location": {
            "country": country,
            "country_input": _clean_optional(location.get("country")),
            "city": _clean_optional(location.get("city")),
        },
        "interviewers": cleaned_interviewers,
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


def build_queries(request: dict[str, Any], country_code: str | None) -> list[dict[str, Any]]:
    """Skip searches that require missing targets; still search English and local languages."""
    profiles = load_country_profiles()
    profile = profiles["countries"].get(country_code, profiles["default"]) if country_code else profiles["default"]
    company = request["company"].get("name")
    role = request["role"].get("title")
    city = request["location"].get("city")
    industry = request["company"].get("industry")
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
        queries.append(_query("en", "role_interview", f'{contextual} interview experience questions', 96,
                              ["glassdoor", "reddit", "youtube", "blind"], "收集岗位面试流程和问题"))
        queries.append(_query("en", "role_market", f'{contextual} salary level compensation benchmark', 90,
                              ["levels-fyi", "glassdoor", "indeed"], "了解薪酬区间及适用地点"))
        if company:
            queries.append(_query("en", "company_culture", f'{contextual} work life balance promotion management', 82,
                                  ["glassdoor", "reddit", "blind"], "查找团队工作体验"))
    for person in request.get("interviewers", []):
        name = person.get("name")
        title = person.get("title")
        if name:
            context = " ".join(x for x in [name, company, title, person.get("department")] if x)
            queries.append(_query("en", "interviewer_identity", f'{_quote(context)} professional profile employer', 97,
                                  ["linkedin", "github"], "核验职业身份和履历"))
            queries.append(_query("en", "interviewer_public_work", f'{_quote(name)} {_quote(company)} articles speaking professional work', 85,
                                  ["github", "youtube", "x"], "查找公开专业观点"))
        elif person.get("profile_url"):
            queries.append(_query("en", "interviewer_identity", f'{person["profile_url"]} employment role', 97,
                                  ["linkedin", "github"], "核验公开资料"))
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
                queries.append(_query(language, "local_interview", f'{_quote(target)} {terms} interview', 89, platforms,
                                      "使用当地语言查找面试经验"))
        for person in request.get("interviewers", []):
            if person.get("name"):
                queries.append(_query(language, "local_interviewer",
                                      f'{_quote(person["name"])} {_quote(company)} {terms}', 80, ["linkedin", "github"],
                                      "本地语言核验公开职业资料"))
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
    selected_query_keys = {(item["language"], item["query"]) for item in mandatory}
    queries = list(mandatory)
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
    interviewer_warnings = []
    for person in normalized["interviewers"]:
        if not person.get("profile_url"):
            interviewer_warnings.append("仅凭姓名不能确认面试官身份，需至少两个相互兼容的公开属性。")
            break

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
            "coverage": {"queries_attempted": [], "sources_attempted": [], "failed_attempts": []},
        },
        "evidence": [],
        "findings": [],
        "interviewers": [],
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
            "interviewer_note": "未提供可核验面试官资料" if not normalized["interviewers"] else "",
            "top_topics": [],
            "unresolved_questions": [],
        },
        "interview_prep": {
            "priorities": [],
            "mock_questions": [],
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
        "warnings": warnings + interviewer_warnings,
        "stopping_rule": "关键结论具备独立来源后停止；若结果开始重复同一来源血缘或核心页面不可访问，则记录缺口并结束。",
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
    for observation in output.get("market", {}).get("salary_observations", []):
        if isinstance(observation, dict):
            observation["evidence_ids"] = remap_ids(observation.get("evidence_ids", []))
    for question in output.get("interview_prep", {}).get("mock_questions", []):
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
        if finding.get("section") not in {item[0] for item in SECTION_ORDER}:
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

    interviewers = normalized_data.get("interviewers")
    if not isinstance(interviewers, list):
        issues.append("interviewers 必须是数组")
        interviewers = []
    for index, person in enumerate(interviewers):
        prefix = f"interviewers[{index}]"
        if not isinstance(person, dict):
            issues.append(f"{prefix} 必须是对象")
            continue
        status = person.get("identity_status")
        if status not in INTERVIEWER_STATUSES:
            issues.append(f"{prefix}.identity_status 无效")
            continue
        match_confidence = person.get("match_confidence")
        if match_confidence not in CONFIDENCE:
            issues.append(f"{prefix}.match_confidence 无效")
        matching_basis = person.get("matching_basis", [])
        valid_basis = (
            matching_basis
            if isinstance(matching_basis, list)
            and all(isinstance(item, str) for item in matching_basis)
            else []
        )
        if status in {"confirmed", "probable"} and len(
            [item for item in valid_basis if item.strip()]
        ) < 2:
            issues.append(f"{prefix} 身份为 {status} 时必须提供至少两个相互兼容的公开匹配属性")
        attributes = ["career", "professional_focus", "public_hiring_signals", "possible_interview_topics"]
        if status in {"unconfirmed", "not_found"}:
            for field in attributes:
                if person.get(field):
                    issues.append(f"{prefix} 身份为 {status} 时不得归因 {field}")
        else:
            ids = person.get("evidence_ids", [])
            if not isinstance(ids, list) or not ids:
                issues.append(f"{prefix} 身份为 {status} 时必须提供公开证据")
                ids = []
            missing = [item_id for item_id in ids if item_id not in evidence]
            if missing:
                issues.append(f"{prefix} 引用不存在证据: {', '.join(missing)}")
            eligible = _eligible_evidence(ids, evidence)
            groups = {item.get("independence_group") for item in eligible}
            if status == "confirmed" and len(groups) < 2:
                issues.append(f"{prefix} 身份为 confirmed 时至少需要两个独立来源")
            if any(source_trust(item["source_type"], item["access_status"]) == "low" for item in eligible):
                issues.append(f"{prefix} 的身份归因不能依赖低可信员工评价或社交帖子")

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

    prep = normalized_data.get("interview_prep")
    if not isinstance(prep, dict):
        issues.append("interview_prep 必须是对象")
        prep = {}
    if network_status in {"available", "partial"} and normalized_data.get("request", {}).get("role", {}).get("title"):
        questions = prep.get("mock_questions", [])
        if not isinstance(questions, list) or len(questions) != 10:
            issues.append("可用网络状态下 interview_prep.mock_questions 必须正好有 10 个问题")
        else:
            for index, question in enumerate(questions):
                if not isinstance(question, dict):
                    issues.append(f"mock_questions[{index}] 必须是对象")
                    continue
                for field in ["question", "basis", "answer_outline"]:
                    if not isinstance(question.get(field), str) or not question[field].strip():
                        issues.append(f"mock_questions[{index}].{field} 必须是非空字符串")
                if question.get("kind") != "prediction":
                    issues.append(f"mock_questions[{index}].kind 必须为 prediction")
                if not question.get("evidence_ids"):
                    issues.append(f"mock_questions[{index}] 缺少 evidence_ids")
    if network_status in {"unavailable", "failed"}:
        for collection_name in ["evidence", "findings", "interviewers"]:
            if normalized_data.get(collection_name):
                issues.append(f"网络状态为 {network_status} 时不得输出 {collection_name}")
        if observations:
            issues.append(f"网络状态为 {network_status} 时不得输出薪酬观察")

    validate_assessment(normalized_data, issues)
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
        f"> 检索日期：{search_date}　地点：{location}　网络状态：`{network}`　报告版本：Interview Intel v{SCHEMA_VERSION}",
        "",
    ]
    if network in {"unavailable", "failed"}:
        lines.extend(
            [
                "## 检索限制",
                "",
                "本次无法使用外部搜索或公开页面访问能力，因此没有生成公司、岗位、薪酬、员工评价或面试官事实。以下研究计划和缺口可供后续重试。",
                "",
                "未找到可靠公开证据。",
                "",
            ]
        )
        for key, title in SECTION_ORDER:
            if request.get("quick_mode") and ((key in {"company", "reviews"} and not request.get("company", {}).get("name")) or (key in {"role", "prep"} and not request.get("role", {}).get("title")) or (key == "interviewer" and not request.get("interviewers"))):
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
            *render_score_lines(data),
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
            f"**面试官信息**：{_md_text(summary.get('interviewer_note'), '未提供可核验的面试官资料。')}",
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
            if section_key == "interviewer" and not request.get("interviewers"):
                continue
        lines.extend([f"## {title}", ""])
        section_findings = by_section.get(section_key, [])
        if section_findings:
            for finding in section_findings:
                lines.append(_render_finding(finding))
        else:
            lines.append("- 未找到可靠公开证据。")
        if section_key == "interviewer":
            lines.append("")
            interviewers = data.get("interviewers", [])
            if interviewers:
                for person in interviewers:
                    name = _md_text(person.get("display_name"), "未命名联系人")
                    status = _md_text(person.get("identity_status"), "unconfirmed")
                    lines.append(
                        f"### {name} · 身份状态：{status} · 匹配置信度：{_md_text(person.get('match_confidence'), 'low')}"
                    )
                    basis = person.get("matching_basis", [])
                    if basis:
                        lines.append(f"- 匹配依据：{_join_zh(basis)}")
                    if status in {"unconfirmed", "not_found"}:
                        lines.append("- 身份未可靠确认，已暂停对该人的履历、关注点和偏好归因。")
                    else:
                        lines.append(f"- 公开职位：{_md_text(person.get('public_role'), '未披露')}")
                        for field, label in [
                            ("career", "已核实职业背景"),
                            ("professional_focus", "专业领域"),
                            ("public_hiring_signals", "公开招聘关注点"),
                            ("possible_interview_topics", "可能面试主题"),
                            ("gaps", "信息缺口"),
                        ]:
                            values = person.get(field, [])
                            if values:
                                lines.append(f"- {label}：{_join_zh(values)}")
                    refs = " ".join(
                        f"[{item}](#{item.lower()})" for item in person.get("evidence_ids", [])
                    )
                    if refs:
                        lines.append(f"- 公开来源：{refs}")
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
        if section_key == "prep":
            prep = data.get("interview_prep", {})
            priorities = prep.get("priorities", [])
            if priorities:
                lines.extend(["", "### 准备优先级", ""])
                for value in priorities:
                    lines.append(f"- {_md_text(value)}")
            lines.extend(["", "### 十个模拟问题（均为预测）", ""])
            for index, question in enumerate(prep.get("mock_questions", []), start=1):
                refs = " ".join(
                    f"[{item}](#{item.lower()})" for item in question.get("evidence_ids", [])
                )
                lines.extend(
                    [
                        f"{index}. **{_md_text(question.get('question'))}**",
                        f"   - 预测依据：{_md_text(question.get('basis'))} {refs}",
                        f"   - 回答思路：{_md_text(question.get('answer_outline'))}",
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
            "- 本报告中的模拟问题属于预测，面试官个人关注点仅在身份确认后采用。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def research_fingerprint(data: dict[str, Any]) -> str:
    """Return a stable hash for local deduplication without storing source text separately."""
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
