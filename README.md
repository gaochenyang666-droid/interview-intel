# Interview Intel

[中文说明](README.zh-CN.md)

Interview Intel is an installable Agent Skill for evidence-led interview research and employer due diligence. It helps an AI agent investigate a company, role, compensation signals, workplace discussions, interview process, and publicly documented HR or interviewer backgrounds, then produce a cited Simplified Chinese report.

> **Status:** `v0.1.0-beta.1`. The core workflow is functional and tested, but it intentionally depends on the host agent's search and browser capabilities.

## What it does

- Routes research across global and country-specific recruiting, employer-review, salary, social, and professional sources.
- Runs English searches first, then adds the primary local language for the target country.
- Collects evidence from opened public pages instead of treating search snippets as facts.
- Separates official facts, first-person statements, third-party assessments, inferences, predictions, and information gaps.
- Calculates conservative confidence from source type, access status, and source independence.
- Deduplicates canonical URLs and identifies shared-origin reposts.
- Supports public research on named HR contacts or interviewers without assuming they are part of a specific interview.
- Produces a six-section Chinese report with a one-page summary and ten evidence-bounded mock questions.
- Records access failures and never bypasses logins, CAPTCHAs, paywalls, or platform permissions.
- Quarantines prompt-injection text and redacts unrelated personal email addresses, phone numbers, and residential addresses.

## Requirements

- Python 3.10 or newer.
- A host Agent with public web search or browser access.
- No paid API and no third-party Python runtime dependency.

The local scripts do not crawl the web. They build the research plan, validate evidence, deduplicate sources, and render the report. The Agent performs the searches and opens the cited pages.

## Installation

Clone the repository and install it as a local Codex skill:

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.codex/skills
cp -R interview-intel ~/.codex/skills/interview-intel
```

Start a new Agent session after installation. You can invoke the skill explicitly:

```text
Use $interview-intel to research this job.

Company: Microsoft
Role: Software Engineer II
Country: United States
City: Redmond
Job URL: <public job URL>
Candidate background: backend systems, C#, cloud services, testing
Focus: technical interviews, system design, team culture
```

The Agent will produce the research plan, perform public-source research, validate the resulting evidence document, and render a Chinese report.

## Command-line tools

```bash
python3 scripts/interview_intel.py --help

python3 scripts/interview_intel.py plan \
  examples/input-us-software-engineer.json \
  --format markdown \
  --network-status available

python3 scripts/interview_intel.py scaffold \
  examples/input-us-software-engineer.json \
  --output research.json

python3 scripts/interview_intel.py validate research.json

python3 scripts/interview_intel.py render \
  research.json \
  --output report.md

python3 scripts/interview_intel.py catalog --country JP
```

`plan` and `catalog` read local configuration only. They do not make network requests.

## Input

Only a company name and role title are required:

```json
{
  "company": {
    "name": "Example Corp"
  },
  "role": {
    "title": "Product Manager"
  }
}
```

Optional fields include country, city, official website, role URL or public description, interviewer names and public profiles, interview stage, a role-relevant candidate summary, and focus questions.

See [references/input-schema.md](references/input-schema.md) for the full input format.

## Research and validation flow

1. Normalize the request and identify the company entity.
2. Generate English-first queries, then local-language queries.
3. Rank candidate sources using the country, role, language, access mode, and research category.
4. Open and verify the original pages.
5. Record evidence with URL, date, access status, source type, an original-language excerpt, and limitations.
6. Classify conclusions and validate the evidence graph.
7. Render the Chinese report with traceable source links.

Evidence rules are documented in [references/evidence-schema.md](references/evidence-schema.md). The report contract is in [references/report-spec.md](references/report-spec.md).

## Report structure

Every online report contains:

1. One-page summary
2. Company overview and evaluation
3. Employee and social-media assessments
4. Role assessment
5. HR and interviewer public intelligence
6. Interview predictions and preparation
7. Sources and confidence

Mock interview questions are labeled as predictions. Reports do not use unsupported 0 to 100 company scores.

## Source coverage

The modular catalog covers:

- Global: LinkedIn, Glassdoor, Indeed, Levels.fyi, Reddit, X, YouTube, and GitHub.
- China: BOSS直聘, 智联招聘, 前程无忧, 脉脉, 牛客, 知乎, 小红书, and 微博.
- North America: Glassdoor, Indeed, Blind, Fishbowl, Wellfound, and Reddit.
- Europe: LinkedIn, Glassdoor, kununu, StepStone, Welcome to the Jungle, and local communities.
- Japan: OpenWork, 転職会議, Wantedly, X, and note.
- Korea: JobPlanet, Saramin, JobKorea, Blind Korea, and Naver communities.
- India: Naukri, AmbitionBox, LinkedIn, and Reddit.
- Australia and New Zealand: SEEK, Glassdoor, LinkedIn, and local communities.
- Southeast Asia: JobStreet, JobsDB, LinkedIn, and publicly indexed Facebook communities.
- Latin America: LinkedIn, Indeed, Glassdoor, InfoJobs, and local communities.

Catalog entries are discovery candidates, not guarantees of access. See [references/source-catalog.json](references/source-catalog.json) and [references/source-routing.md](references/source-routing.md).

## Evidence and privacy

- Do not bypass authentication, CAPTCHA, paywalls, robots restrictions, or platform permissions.
- A search-result snippet is not verified evidence.
- Anonymous reviews remain opinions and default to low confidence.
- Reposts sharing one origin count as one independent source.
- A name alone cannot establish an interviewer's identity.
- Public professional information is used only when relevant to the target role.
- Private contact details, home addresses, family information, health data, political views, and unrelated personal data are out of scope.
- Candidate resumes and contact information are not written to logs or cache files.

## Development

Run the complete test suite:

```bash
python3 -m unittest discover -s tests -v
```

Validate the example research artifact:

```bash
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

The test suite covers country routing, multilingual planning, duplicate source handling, unsupported claims, conflicting reviews, sparse evidence, offline behavior, interviewer disambiguation, prompt injection, private-data redaction, and regression cases.

## Project layout

```text
interview-intel/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── agents/
│   └── openai.yaml
├── references/
├── scripts/
├── tests/
├── examples/
└── .github/workflows/
```

QA source material is intentionally excluded from the public Git history. The local QA workspace may contain public-page excerpts and must be reviewed again before any separate publication.

## Known limitations

- Search quality depends on the host Agent's available tools.
- Public pages can require login or change without notice.
- Anonymous review and salary aggregates may omit sample size and level details.
- Native-language company and role aliases are not exhaustive.
- An interviewer's public career does not prove participation, personality, or scoring preference.
- The project does not support authenticated scraping or private-data investigation.

See [CHANGELOG.md](CHANGELOG.md) for release history and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules.

## License

MIT. See [LICENSE](LICENSE).
