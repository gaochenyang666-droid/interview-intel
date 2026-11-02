# Interview research and interactive practice

Use this reference after the employer and role have been identified and the host agent can access public web sources.

## Evidence tiers

Create one `interview_experiences` record for each public account or discussion that was opened. Use these levels consistently:

| level | scope | origin type |
| --- | --- | --- |
| 1 | Same company, same role, and similar location or level | `historical_exact` |
| 2 | Same company, related role, with relation rationale | `historical_similar_role` |
| 3 | Comparable company, same role, with comparability rationale | `similar_company` |
| 4 | Role and job-description prediction | `prediction` |

Prefer recent, specific, first-person accounts. A company review without reported interview details cannot become an interview account. A search snippet cannot support a verbatim question. Reposts sharing one origin use one independence group.

Comparable companies must be justified by industry, business model, role duties, team structure, or hiring requirements. Company size alone is insufficient.

## Interview experience record

```json
{
  "id": "I001",
  "source_level": 1,
  "company": "Example Corp",
  "role": "Software Engineer",
  "country": "US",
  "city": "Seattle",
  "level": "Mid-level",
  "published_at": "2026-09-20",
  "interview_date": "2026-09",
  "rounds": ["coding", "system design"],
  "format": "video",
  "questions": [
    "Verbatim question stated in the original public post."
  ],
  "difficulty": "Author-stated difficulty only",
  "author_impression": "Author-stated impression only",
  "match_rationale": "Required for a related role or comparable company",
  "role_relation": "Required for source level 2",
  "similar_company": "Required for source level 3",
  "evidence_ids": ["E010"],
  "limitations": "One anonymous public account; region and level self-reported."
}
```

Use full ISO dates or month precision for `interview_date`. Leave dates empty when the page does not show them. Do not infer a post date from search-engine ordering.

`questions` may be an empty array when a public account describes the process, rounds, or format but does not report a verbatim question. Keep that account as process evidence, and generate the question bank from prediction-level prompts unless another linked account contains explicit questions.

Record `similar_companies` separately when level 3 evidence is used:

```json
{
  "name": "Peer Corp",
  "match_rationale": "Same enterprise software segment and comparable backend platform scope.",
  "evidence_ids": ["E013"]
}
```

## Ten-question bank

Generate the bank after building the research artifact:

```bash
python3 scripts/interview_intel.py generate-questions research.json \
  --output research-labelled.json
```

Each question contains:

- `id`
- `question`
- `category`
- `source_level`
- `origin_type`
- `source_company`
- `source_role`
- `migration_rationale`
- `evidence_ids`
- `basis`
- `competencies`
- `answer_outline`
- `answer_structure`
- `difficulty`

Historical question text must match the linked experience exactly after punctuation and case normalization. Prediction questions require verified role or official evidence and must state that they are generated, not historical originals.

Use a role-sensitive mix. Engineering, data, product, operations, and management roles should receive materially different category distributions. Avoid duplicate or near-duplicate prompts and include at least three categories across ten questions.

## Mock interview session

Start with the default scene and difficulty or specify one:

```bash
python3 scripts/interview_simulator.py start research-labelled.json \
  --scene technical --difficulty intermediate
python3 scripts/interview_simulator.py skip
```

Supported scenes are `hr_screen`, `professional`, `technical`, `business_case`, and `final`. Supported difficulties are `junior`, `intermediate`, `senior`, and `stress`.

The state file defaults to `.interview-intel/session.json`, which is ignored by Git. Ask only one primary question, then wait. On a weak answer, inspect the actual missing element and ask one targeted follow-up:

- missing event or responsibility: ask for a concrete situation and personal role;
- missing metric: request a baseline, result, percentage, time range, or other verifiable measure;
- missing result: ask what changed and how it was checked;
- missing technical depth: ask about boundaries, failure modes, tradeoffs, testing, or rollback.

Do not repeat a question already asked. A skipped question is not counted as answered.

At the end, include:

- number of questions actually answered;
- useful facts and evidence supplied;
- logic and structure;
- domain coverage;
- specificity of actions, metrics, and results;
- main omissions;
- at most three questions to practice again;
- improved answer outlines.

State clearly that the feedback assesses only the mock session and does not estimate real hiring probability.
