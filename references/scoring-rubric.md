# Opportunity scoring rubric (experimental)

This is a **decision-support index for one candidate considering one employer and one role**, not a validated psychometric instrument, a universal employer ranking, a salary percentile, or a probability of receiving an offer.

## Fixed, auditable weights

| ID | Dimension | Metric | Weight |
| --- | --- | --- | ---: |
| `stability` | Company | Financial/business stability, hiring risks, documented changes | 15% |
| `culture` | Company | Employee experience, management practices, workload | 20% |
| `clarity` | Role | JD specificity, scope, responsibilities, hiring transparency | 15% |
| `growth` | Role | Career learning, progression, transferable skills | 15% |
| `compensation` | Role | Location- and level-adjusted market competitiveness | 10% |
| `skills` | Candidate fit | Candidate's disclosed skills versus actual role requirements | 15% |
| `preferences` | Candidate fit | Candidate's explicitly stated work preferences versus role conditions | 10% |

Metrics use a five-grade **ordinal rubric** with common anchors:

- **1**: clearly unfavorable, verified major gaps or significant downside.
- **2**: below expectations, notable negative signals.
- **3**: mixed/neutral with enough evidence for a limited assessment.
- **4**: good, concrete positive findings support the judgment.
- **5**: unusually strong, corroborated advantages relevant to the candidate.

A metric is converted to an **index** by `(rating - 1) × 25`, giving 0, 25, 50, 75, 100. The weights are normative product defaults; they are **not empirically calibrated**. Ratings must explicitly explain why the verified findings warrant the selected grade. For compensation, compare the same market/currency/period and approximate level, or leave it blank. For skills or preferences, do not infer candidate experience or preferences not provided by the user.

## Provenance and withholding rules

- Ratings live in the **optional** `assessment.metrics` field of a research JSON artifact. Do not put computed totals or agent-invented weights into input.
- Each metric requires a nonempty `finding_ids` list, actual verified source pages behind those findings, and an explanatory `reason` (at least 12 characters). An interview **prediction**, advice, or gap cannot justify a score.
- Work culture needs **at least two independent source origins** and at least one outside workplace experience. Compensation requires **at least two independent origins** for a comparison.
- A candidate fit rating requires disclosed candidate skills; a preference rating also requires explicit `request.candidate.preferences`.
- Unknown values remain **unrated**, not 0 or 50. Unconfirmed company identity, offline research, and invalid source attribution cannot produce ratings.
- A dimension publishes a numeric score only if enough of its **fixed weight** was covered: company 70%, role 60%, fit 60%. Rated factors are reweighted within a qualifying dimension.
- The **overall index** is displayed only when the rated weight totals **at least 80%**, all three dimensions qualify, and none has low source-quality status. Rated factors are reweighted by their original global weights.
- The **coverage percentage** means `sum(weights of rated metrics) / 100`, **not** percentage of facts independently verified. Source-quality labels are separate and conservative.
- Reposts from one origin count once. More links and positive adjectives never increase a rating automatically. Source quality reflects basic type and origin diversity, not an independently audited truth score.
- Scores are contextual and time-sensitive. Compare two opportunities only when the same candidate profile, rubric, city/level adjustments, and approximately similar source quality are used.

## Metric-specific coding guidance

- `stability`: use current audited disclosures, official results, financing/operations context, reliable restructuring coverage; do not assume a large employer is automatically secure.
- `culture`: capture both favorable and unfavorable independent reports and note city/department/date/sample limitations. A single anonymous review cannot score this metric.
- `clarity`: open the actual job posting; distinguish generic template language from explicit scope, outputs, seniority and reporting lines.
- `growth`: source career paths, role scope and demonstrated learning opportunities, noting where promotion promises are unverified.
- `compensation`: compare disclosed pay for the exact role and locality with a second independently sourced market comparator; avoid false precision.
- `skills`: match user-disclosed skills with the verified JD; clarify gaps and time to bridge them.
- `preferences`: use only user-stated values (e.g., remote work, hours, location, career goals) and verified job conditions. No assumptions about family, health, personality, or other private traits.

## JSON example (partial assessment)

```json
{
  "assessment": {
    "metrics": [
      {
        "key": "stability",
        "rating": 4,
        "reason": "公司近期财务披露显示经营活动稳定，但团队招聘仍有变化。",
        "finding_ids": ["F001", "F008"]
      },
      {
        "key": "clarity",
        "rating": 3,
        "reason": "岗位公开说明了部分职责和技能要求，缺少团队目标细节。",
        "finding_ids": ["F012"]
      }
    ]
  }
}
```

Only cite actual `F...` identifiers in the research file. Run:

```bash
python3 scripts/interview_intel.py validate research.json
python3 scripts/interview_intel.py score research.json --output scores.json
python3 scripts/interview_intel.py render research.json --output report.md
```

The report includes the scoring breakdown **inside the existing executive summary** and retains its previous six numbered sections.
