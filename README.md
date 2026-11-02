# Interview Intel

**Evidence-led company research, interview intelligence, and mock interview practice for AI agents.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Tests](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Releases](https://github.com/gaochenyang666-droid/interview-intel/releases) · [MIT License](LICENSE)

Interview Intel is an installable Agent Skill for researching an employer and role, finding public employee discussions, collecting historical interview experiences, generating source-labelled questions, and running a stateful mock interview. It produces a Simplified Chinese report with original links, dates, confidence levels, and explicit information gaps.

> Development version: `0.2.0-beta.1`. Live research uses the host agent's public web search and browser tools. The Python utilities plan searches, validate evidence, generate questions, persist interview state, and render reports. They do not crawl the web by themselves.

## Quick start

Paste three fields into a supported agent:

```text
Country: China
Company: ByteDance
Role: Product Operations
```

Use `0` for an unknown field. At least a company or role is required. No resume, job URL, or interviewer details are needed. Numeric company scoring is off by default.

Create the normalized request locally:

```bash
python3 scripts/interview_intel.py quick "China/ByteDance/Product Operations" --output request.json
python3 scripts/interview_intel.py plan request.json --format json --output research-plan.json
```

The agent performs live research and records inspected public sources in the research JSON.

## What it does

- Resolves the employer and collects official company, role, compensation, and recent-context evidence.
- Searches at least two independent public workplace or social platforms when a company is supplied, preferably three.
- Preserves positive, negative, and mixed public experiences with source dates and limitations.
- Searches public interview accounts in English and the target country's main language.
- Prioritizes same-company and same-role accounts, then related roles, comparable companies, and role-based predictions.
- Generates ten role-sensitive questions with exact source labels and links.
- Supports HR, professional, technical, business-case, and final-round mock interviews.
- Asks one question at a time, creates contextual follow-ups, adjusts difficulty, and stops on command.
- Keeps answer outlines hidden until feedback.

Interviewers are not profiled. The workflow does not bypass login pages, CAPTCHAs, paywalls, or platform permissions. Search snippets are discovery leads and never count as verified evidence.

## Interview evidence levels

| Level | Evidence | Question label |
| --- | --- | --- |
| 1 | Same company, same role | `historical_exact` |
| 2 | Same company, related role | `historical_similar_role` |
| 3 | Comparable company, same role | `similar_company` |
| 4 | Role and JD based prediction | `prediction` |

Historical labels require a verbatim question in the linked public interview account. Peer-company and related-role questions require a migration rationale. AI predictions are never presented as company originals.

See [the interview practice guide](references/interview-practice.md) for the schema and matching rules.

## Generate and practice

```bash
# Add ten evidence-labelled questions to the research file
python3 scripts/interview_intel.py generate-questions research.json \
  --output research-labelled.json

# Validate and render the Chinese report
python3 scripts/interview_intel.py validate research-labelled.json
python3 scripts/interview_intel.py render research-labelled.json --output report.md

# Start a stateful mock interview
python3 scripts/interview_simulator.py start research-labelled.json \
  --state .interview-intel/session.json
python3 scripts/interview_simulator.py answer --answer "My answer"
python3 scripts/interview_simulator.py skip
python3 scripts/interview_simulator.py finish
```

In chat, say `开始模拟面试` to start and `结束面试` to receive feedback. Use `重新开始` to reset the current session. The state file is local and ignored by Git.

## Report structure

The Simplified Chinese report contains a one-page summary and six sections:

1. Company overview and assessment
2. Employee and public social-media experiences
3. Role, compensation, and career analysis
4. Public historical interview experiences and matching
5. Interview predictions, preparation, and mock interview entry
6. Sources, confidence, and limitations

[Input format](references/input-schema.md) · [Evidence schema](references/evidence-schema.md) · [Report specification](references/report-spec.md) · [Example report](examples/report-us-software-engineer.md)

## Install

Requirements: Git, Python 3.10 or newer, and an agent with public web access and local Python execution permission.

### Shared Agent Skills directory

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode, and compatible Windsurf / Devin Desktop versions use this shared location. Claude Code uses:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

Install the complete directory, including `SKILL.md`, `scripts/`, and `references/`.

| Client | Personal folder | Project folder |
| --- | --- | --- |
| OpenAI Codex | `~/.agents/skills/` | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| GitHub Copilot | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |

### Marketplace installs

```bash
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
```

Claude Code users can add the self-hosted marketplace:

```text
/plugin marketplace add gaochenyang666-droid/interview-intel
/plugin install interview-intel@interview-intel-marketplace
```

Additional installation and publishing details are in [PUBLISHING.md](PUBLISHING.md).

## Invocation examples

```text
Use Interview Intel for Microsoft, Software Engineer II, Redmond.
Find recent public employee discussions and interview experiences.
Create ten source-labelled questions and offer a technical mock interview.
```

```text
Use the Interview Intel skill. Country: Japan. Company: Toyota.
Role: Product Manager. Search English and Japanese public sources.
```

## Reliability and privacy

- Official pages establish company and role facts. They do not prove employee experience.
- Anonymous posts remain opinions with unverified employment status.
- Duplicate or reposted material counts as one source lineage.
- Missing evidence is reported as a gap and never interpreted as an absence of complaints.
- Resumes, private contacts, family information, addresses, and unrelated sensitive data are excluded.
- Offline mode returns a plan and limitations without invented findings.

## Test

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

The suite covers evidence validation, source deduplication, country routing, community attempts, interview tiers, source-label integrity, role-sensitive question mixes, contextual follow-ups, difficulty changes, finish behavior, packaging, and distribution.

## Known limitations

- Live coverage depends on the host's search and browser capabilities.
- Login-gated and anti-bot protected pages are intentionally unavailable.
- Interview questions appear only when a public account explicitly reports them.
- Comparable-company selection needs verified business and role rationale.
- The local simulator uses deterministic heuristics for follow-ups and feedback. The host agent can provide richer conversational judgment while keeping the same evidence and privacy rules.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and [the research playbook](references/research-playbook.md) before contributing.

**License:** [MIT](LICENSE).
