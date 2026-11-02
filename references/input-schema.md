# Input schema

The CLI accepts UTF-8 JSON. The standard chat and CLI interface uses **country / company / role**, with `0` for unknowns. At least one of company or role must be provided; country `0` means global research. Advanced JSON remains supported, but interviewer profiling is retired.

```json
{
  "company": {
    "name": "Example Corporation",
    "website": "https://example.com",
    "industry": "Enterprise software"
  },
  "role": {
    "title": "Senior Product Manager",
    "url": "https://example.com/jobs/123",
    "description": "Paste a public JD only. Remove candidate data.",
    "level": "Senior"
  },
  "location": {
    "country": "US",
    "city": "Seattle"
  },
  "candidate": {
    "summary": "Eight years in B2B product; enterprise platform and API experience.",
    "skills": ["product discovery", "platform strategy", "SQL"],
    "preferences": ["hybrid work", "learning opportunities"]
  },
  "focus": ["organization health", "system design", "salary negotiation"],
  "research": {
    "max_queries": 18,
    "recency_months": 18,
    "languages": ["en"]
  }
}
```

## Quick input

Three lines work directly in an Agent chat:

```text
国家：中国
公司：字节跳动
岗位：产品运营
```

The Agent automatically skips any field containing `0`. Use the CLI to create a normalized JSON request:

```bash
python3 scripts/interview_intel.py quick "中国/字节跳动/产品运营" --output request.json
```

Alternatively use `quick --country CN --company 字节跳动 --role 产品运营 --output request.json`; or supply three named lines as a quoted input string. `quick --plan` emits the corresponding research plan. This CLI does not make network requests; the Agent performs live research after planning.

For partial requests: company `0` skips company conclusions; role `0` skips job analysis and mock questions; country `0` triggers global research. If both company and role are `0`, the request is rejected. Optional candidate background and personal preferences never block research or company/role-level scoring.

## Field behavior

- `company.website` and `role.url` are strong entity clues, not proof that the search results concern the correct employer.
- `location.country` accepts a two-letter ISO-style code, English country name, or common Chinese name. Unknown values produce a warning and fall back to global English research.
- `research.languages` adds languages to the country route. The planner still runs English first.
- `candidate.summary` must contain role-relevant information only. The tool does not log or persist it separately.
- Interviewer names are not requested or researched. Legacy input fields are ignored by the active planning workflow.

## Research plan output

`plan` returns:

- normalized input and inferred or supplied country;
- entity resolution status and questions that genuinely block attribution;
- ordered query tasks with language, category, priority, and candidate domains;
- a ranked source shortlist;
- network state and capability limits;
- the required research JSON skeleton.

- `candidate.preferences` is optional and is used only for the contextual preference-match score. If the user does not disclose preferences, this factor remains **unscored**. See [scoring-rubric.md](scoring-rubric.md).
