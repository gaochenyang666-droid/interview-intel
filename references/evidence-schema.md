# Evidence and research schema

The renderer rejects unsupported factual claims. The schema is intentionally explicit so that summaries do not erase provenance.

## Top-level document

```json
{
  "schema_version": "0.1",
  "request": {},
  "research": {},
  "evidence": [],
  "findings": [],
  "market": {},
  "summary": {},
  "interview_prep": {},
  "assessment": {"metrics": []},
  "sources_consulted": []
}
```

Use the complete starter emitted by `python3 scripts/interview_intel.py scaffold request.json`.

## Research metadata

`research` requires:

- `network_status`: `available`, `partial`, `unavailable`, or `failed`.
- `search_completed_at`: ISO date or timestamp.
- `languages_attempted`: list of language tags actually used.
- `entity`: `{ "status": "confirmed|probable|ambiguous|not_found", "name": "...", "basis": "..." }`.
- `coverage`: `{ "queries_attempted": [], "sources_attempted": [], "failed_attempts": [] }`, plus `community_required` and `community_attempts` in new plans.

When network status is `unavailable` or `failed`, `evidence` and all research claim collections must be empty.

The validator treats page text as untrusted. It rejects prompt-injection patterns and redacts detected personal email addresses, private phone numbers, and residential addresses from rendered research text. Mark a source as a gap when the relevant public content cannot be used without exposing unrelated private information.

## Community platform attempts

For newly planned company research, the scaffold sets `research.coverage.community_required: true` and `community_attempts: []`. Live company research needs **at least two separate platform attempts**, whether they found inspectable original content or encountered access restrictions. New artifacts with fewer attempts fail validation. Old research files without this field stay valid.

```json
{
  "community_required": true,
  "community_attempts": [
    {
      "platform_id": "zhihu",
      "query": "site:zhihu.com 公司名称 员工 工作体验",
      "result": "found",
      "evidence_ids": ["E011"]
    },
    {
      "platform_id": "maimai",
      "query": "site:maimai.cn 公司名称 员工评价",
      "result": "login_required",
      "evidence_ids": []
    }
  ]
}
```

Results may be `found`, `blocked`, `login_required`, `snippet_only`, `no_results`, `irrelevant`, `error`. A `found` attempt must reference verified evidence of type `employee_review`, `forum_post`, `social_post` or `interview_report`. An inaccessible page cannot support a review claim. This validates documentation of actual searches, not the truth of an anonymous author's employment claim.

## Evidence records

Each evidence item represents one opened or otherwise inspected page, not an aggregate search-result page.

```json
{
  "id": "E001",
  "title": "Original page title",
  "url": "https://original.example/page",
  "platform": "Official company site",
  "source_type": "official",
  "published_at": "2026-08-10",
  "published_at_precision": "day",
  "retrieved_at": "2026-11-02",
  "language": "en",
  "excerpt": "Short original-language excerpt.",
  "access_status": "verified",
  "independence_group": "lineage-2026-08-10-announcement",
  "supports": ["F001"],
  "limitations": "Limited to the information on this page."
}
```

Allowed `source_type` values:

`official`, `official_filing`, `job_posting`, `first_party`, `professional_profile`, `news`, `interview_report`, `employee_review`, `social_post`, `forum_post`, `aggregator`, `candidate_provided`.

Allowed `access_status` values:

`verified` means the content was opened and checked. `snippet_only` means only a search snippet was available. `blocked` means access was denied. `unavailable` means the page did not load. Only `verified` evidence can support a high-confidence finding. A source record may be retained to document what was attempted, but blocked and unavailable records cannot support a factual conclusion.

`independence_group` identifies common origin. Reposts, syndication, screenshots of one post, and multiple URLs with the same source content should share one group. Two links in one group count as a single origin.

The renderer removes duplicate canonical URLs. It annotates shared lineages so corroboration is not overstated.

## Findings

Allowed `kind` values and evidence rules:

- `fact`: verified primary or credible secondary evidence; at least one eligible source.
- `person_statement`: evidence with a verified first-person source.
- `third_party_assessment`: third-party review, news, or community evidence.
- `inference`: public evidence plus explicit `basis`; label it as analysis, not fact.
- `prediction`: public evidence plus explicit `basis`; label it as a prediction.
- `gap`: no evidence may exist; describe what could not be confirmed.
- `advice`: preparation action based on supplied context; no evidence required but it must not introduce a factual claim.

Each finding has:

```json
{
  "id": "F001",
  "section": "company|reviews|role|prep",
  "kind": "fact",
  "statement": "简体中文结论",
  "evidence_ids": ["E001"],
  "confidence": "high",
  "basis": "Only needed for inference or prediction.",
  "limitations": "Sample and scope limitations."
}
```

High confidence requires at least one verified `official`, `official_filing`, `job_posting`, or profile-authored `first_party` source. Medium confidence requires a verified credible secondary source or at least two independent origins. Low confidence covers anonymous reviews, single social posts, and snippet-only evidence. The CLI calculates the maximum allowed confidence and rejects unsupported claims.

## Legacy compatibility

Older research JSON files may contain `interviewers` or findings with `section: "interviewer"`. The validator retains safety checks for legacy records, but new plans do not collect personal interviewer data, and reports do not render interviewer profiles.

## Market data

Use `market.salary_observations`, not a fabricated range:

```json
{
  "currency": "USD",
  "location": "Seattle, US",
  "salary_observations": [
    {
      "label": "Senior software engineer",
      "min": null,
      "p25": null,
      "max": null,
      "median": null,
      "p90": null,
      "period": "year",
      "sample_size": null,
      "as_of": "2026-10-01",
      "evidence_ids": ["E020"],
      "limitations": "Page did not disclose sample size."
    }
  ],
  "benchmark_note": "No reliable local sample was found."
}
```

Do not calculate a range when the source has no usable values. Keep currency, time period, level, and location attached to every number.

## One-page summary and preparation

`summary` contains `company_view`, `opportunity_finding_ids`, `risk_finding_ids`, `top_topics`, and `unresolved_questions`.

`interview_prep` contains:

- `priorities`: up to five evidence-backed focus topics;
- `mock_questions`: exactly ten items with `question`, `kind="prediction"`, `basis`, `evidence_ids`, and `answer_outline`;
- `star_framework`: one concise adaptation;
- `candidate_fit`: `strengths`, `gaps`, `evidence`, and `not_disclosed`;
- `questions_to_ask`;
- `negotiation_notes`;
- `final_checklist`.

The renderer labels all mock questions as predictions.

## Optional evidence-driven opportunity score

The optional `assessment.metrics` array contains 0–7 fixed ratings. Each item is `{ "key": "stability", "rating": 4, "reason": "可核查的评分说明", "finding_ids": ["F001"] }`. Every rating must use verified evidence-backed findings, and uses the published fixed weights. Empty metrics means no score. The CLI calculates the index using `score`; **do not provide manual overall or confidence values**. Missing factors are excluded and reported as unscored. Full anchors, source-independence requirements and calculation details: [scoring-rubric.md](scoring-rubric.md).
