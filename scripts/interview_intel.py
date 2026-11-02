#!/usr/bin/env python3
"""Command-line entry point for Interview Intel v0.1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from intel_core import (
    IntelValidationError,
    PRODUCT_VERSION,
    build_plan,
    load_source_catalog,
    render_report,
    route_sources,
    validate_research,
)


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_or_print(text: str, output: str | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"已写入 {path.resolve()}")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def _plan_markdown(plan: dict) -> str:
    request = plan["request"]
    lines = [
        f"# {request['company']['name']} · {request['role']['title']} 研究计划",
        "",
        f"- 国家或地区：{plan.get('country_code') or '全球'}",
        f"- 计划语言：{', '.join(plan['languages_planned'])}",
        f"- 网络状态：{plan['network_status']}",
        f"- 实体状态：{plan['entity_resolution']['status']}",
        "",
        "## 搜索任务",
        "",
    ]
    for query in plan["queries"]:
        lines.append(f"- `{query['id']}` [{query['language']}] {query['query']}")
        lines.append(f"  - 目的：{query['purpose']}；优先平台：{', '.join(query['platform_ids']) or '通用搜索'}")
    lines.extend(["", "## 数据源路由", ""])
    for source in plan["sources"]:
        lines.append(f"- {source['name']}（{source['id']}，分数 {source['score']}）：{'；'.join(source['reasons'])}")
    if plan["warnings"]:
        lines.extend(["", "## 注意事项", ""])
        lines.extend(f"- {item}" for item in plan["warnings"])
    return "\n".join(lines) + "\n"


def cmd_plan(args: argparse.Namespace) -> int:
    request = _read_json(args.request)
    plan = build_plan(request, max_queries=args.max_queries, network_status=args.network_status)
    if args.format == "markdown":
        _write_or_print(_plan_markdown(plan), args.output)
    else:
        _write_or_print(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", args.output)
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    request = _read_json(args.request)
    plan = build_plan(request, max_queries=args.max_queries, network_status=args.network_status)
    _write_or_print(json.dumps(plan["scaffold"], ensure_ascii=False, indent=2) + "\n", args.output)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = _read_json(args.research)
    warnings: list[str] = []
    normalized = validate_research(data, warnings)
    result = {
        "valid": True,
        "evidence_count": len(normalized.get("evidence", [])),
        "finding_count": len(normalized.get("findings", [])),
        "interviewer_count": len(normalized.get("interviewers", [])),
        "warnings": warnings,
    }
    _write_or_print(json.dumps(result, ensure_ascii=False, indent=2) + "\n", args.output)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    data = _read_json(args.research)
    report = render_report(data)
    _write_or_print(report, args.output)
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    if args.raw:
        catalog = load_source_catalog()
        _write_or_print(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", args.output)
        return 0
    sources = route_sources(args.country.upper() if args.country else None, [], limit=args.limit)
    _write_or_print(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="interview-intel",
        description="Plan, validate, and render source-graded Chinese interview intelligence.",
    )
    parser.add_argument("--version", action="version", version=f"Interview Intel {PRODUCT_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Build a multilingual search and source-routing plan")
    plan.add_argument("request", help="Input request JSON")
    plan.add_argument("--format", choices=["json", "markdown"], default="json")
    plan.add_argument("--max-queries", type=int)
    plan.add_argument("--network-status", default="unknown", choices=["available", "partial", "unavailable", "failed", "unknown"])
    plan.add_argument("--output", "-o")
    plan.set_defaults(func=cmd_plan)

    scaffold = subparsers.add_parser("scaffold", help="Emit a blank research JSON document")
    scaffold.add_argument("request", help="Input request JSON")
    scaffold.add_argument("--max-queries", type=int)
    scaffold.add_argument("--network-status", default="available", choices=["available", "partial", "unavailable", "failed", "unknown"])
    scaffold.add_argument("--output", "-o")
    scaffold.set_defaults(func=cmd_scaffold)

    validate = subparsers.add_parser("validate", help="Validate evidence, claims, and identity attribution")
    validate.add_argument("research", help="Completed research JSON")
    validate.add_argument("--output", "-o")
    validate.set_defaults(func=cmd_validate)

    render = subparsers.add_parser("render", help="Render a validated six-section Chinese report")
    render.add_argument("research", help="Completed research JSON")
    render.add_argument("--output", "-o")
    render.set_defaults(func=cmd_render)

    catalog = subparsers.add_parser("catalog", help="Inspect or route the candidate source catalog")
    catalog.add_argument("--country")
    catalog.add_argument("--limit", type=int, default=12)
    catalog.add_argument("--raw", action="store_true")
    catalog.add_argument("--output", "-o")
    catalog.set_defaults(func=cmd_catalog)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        if isinstance(exc, IntelValidationError):
            message = "校验失败：\n- " + "\n- ".join(exc.issues)
        else:
            message = f"错误：{exc}"
        print(message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
