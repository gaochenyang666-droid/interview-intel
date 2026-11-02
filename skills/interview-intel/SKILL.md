---
name: interview-intel
description: Research public employer information, workplace discussions, role requirements, and historical interview experiences, then produce a source-graded Chinese report and evidence-labelled mock interview. Use for company due diligence, job analysis, and interview practice.
---

# Interview Intel

This is the portable plugin and extension entrypoint. Before doing research, read the canonical repository-root `SKILL.md` at `../../SKILL.md` in full. Resolve the repository root to an absolute path, then treat its `references/`, `scripts/`, and `examples/` paths as relative to that root.

Accept three chat fields, with `0` meaning unknown and skipped:

```text
国家：中国
公司：字节跳动
岗位：产品运营
```

Require at least a company or role. Search in English first, then the main local language. When a company is supplied, attempt at least two independent public workplace or social platforms and open accessible originals. Keep source links, dates, independence, and limitations. Enforce no individual interviewer profiling, no access-control bypass, no invented evidence, and no numeric company score by default.

The canonical workflow adds public interview-experience tiers, ten source-labelled questions, and a stateful mock interview that asks one question at a time. Read `../../references/interview-practice.md` for that mode and run `../../scripts/interview_intel.py` and `../../scripts/interview_simulator.py` through resolved absolute paths. The host agent must provide public web access; the CLI does not crawl.
