---
name: interview-intel
description: Research a company or job role using official sources and real publicly accessible employee reviews from local and global communities; produce a cited Chinese interview intelligence report. Use when preparing for interviews or evaluating potential employers.
---

# Interview Intel

This is the **portable plugin/extension entrypoint**. The maintained canonical workflow is the repository-root `SKILL.md`, located at `../../SKILL.md` relative to this file.

**Before doing research:** use your host's file-reading tool to read that canonical `SKILL.md` in full, and follow its evidence safeguards, multilingual search sequence, community review requirements, report structure and explicit omissions. Treat all its relative `references/`, `scripts/` and `examples/` paths as relative to the **repository or installed extension root** (two parent directories above this file), never to an unrelated user project. Resolve that root to an absolute path before running Python CLI scripts.

## Start here

Accept exactly these three fields in chat. A value of `0` means unknown/skip:

```text
国家：中国
公司：字节跳动
岗位：产品运营
```

At least a company or role is required. Use English search first, then local language. When a company is given, actually check at least two **different public workplace/social platforms** and inspect original accessible posts. Do not present a search result snippet as a firsthand review; record inaccessible platform attempts. The report is in Simplified Chinese and cites public sources.

**Default:** no numerical rating and no individual interviewer profiling. Missing fields are automatically skipped. Full guidance is in `../../SKILL.md`; schema and verification rules are in `../../references/`. The CLI is `../../scripts/interview_intel.py` relative to this wrapper; run it via the absolute resolved path and do not assume it exists in the current workspace.

The host Agent must provide web search/browser capability for live research; the CLI alone does not crawl websites.
