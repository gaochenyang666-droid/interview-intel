# Interview Intel

**Global interview research for AI agents, with traceable sources.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Tests](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Latest beta release](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [MIT License](LICENSE)

Prepare for an interview with more context than a job description. **Interview Intel** is an installable Agent Skill that researches an employer, a specific role, public workplace discussions, compensation signals, interview processes, and the verified *professional* background of a named interviewer or HR contact. It produces a **source-linked report in Simplified Chinese** with explicit confidence and evidence limitations.

> **Public beta: v0.1.0-beta.1.** The Skill uses the **host agent's web search/browser tools** for live research. The included Python scripts plan queries, validate evidence, and render reports; they **do not independently crawl websites**.

## What can it help with?

| Question | What the report covers |
| --- | --- |
| Is this company worth considering? | Official company facts, business context, workplace feedback, recent hiring signals, and disagreements across sources. |
| What is this job really asking for? | Verified job description, responsibilities, skill gaps, compensation observations, role and location differences. |
| How do employees describe the workplace? | Public employee reviews and social discussions with dates, sampling caveats, and source independence checks. |
| What do we know about the interviewer? | Identity-checked professional history, published work, and stated hiring criteria, where publicly available. |
| How should I prepare? | A targeted preparation plan, follow-up questions, and **10 labeled practice questions** tied to available evidence. |

Search begins in **English** and adds the relevant **local language**. A country-aware source catalog includes candidates such as LinkedIn, Indeed, Glassdoor, Reddit, Blind, 牛客, 脉脉, OpenWork, JobPlanet, Naukri, SEEK and regional job boards. **Listing a platform does not imply unrestricted access or verified content.**

## Quick start: install for Codex

**Requirements:** Python 3.10+, Git, and a Codex/Agent environment with web search or browser tools. No paid API or third-party Python runtime packages are required for the local utilities.

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.codex/skills
cp -R interview-intel ~/.codex/skills/interview-intel
```

Start a **new Codex session** so it can discover the Skill. Invoke it explicitly with `$interview-intel`:

```text
Use $interview-intel to prepare a cited interview intelligence report.
Company: Microsoft
Role: Software Engineer II
Location: Redmond, Washington, United States
Job URL: [paste the public job posting, if available]
Interviewer: [optional name and public professional profile]
My background: C#, distributed systems, Azure, testing
Focus: team culture, interview process, system design, salary
```

**Only the company and role are required.** Country/city, a job posting or URL, an interviewer/HR contact, interview stage, candidate skills and focus questions improve the research. Leave unknown fields blank; the agent should identify and label any information gaps.

Other Agent Skills-compatible hosts can use the same [SKILL.md](SKILL.md), but installation and tool availability depend on the host. The Codex path above is the documented local installation.

## Usage examples

**Explore an employer and role (no interviewer provided):**

```text
Use $interview-intel. Company: Toyota. Role: Product Manager.
Country: Japan. Search Japanese workplace and job sources, compare
the responsibilities with the official listing, and output the cited Chinese report.
```

**Prepare for a named interviewer:**

```text
Use $interview-intel. Company: [company]. Role: [position].
Interviewer: [full name, job title, public profile link].
Verify the identity before attributing career information.
Summarize publicly expressed professional interests and prepare
role-specific questions. Mark all interview-question forecasts as predictions.
```

**Evaluate competing evidence:**

```text
Use $interview-intel to research [company] for [role] in [city].
Compare official hiring information with recent, accessible employee
reviews. Distinguish first-hand claims, anonymous opinions and unknowns.
```

## What the finished report looks like

The output is a **Simplified Chinese Markdown report**, with a one-page summary followed by six numbered sections:

1. Company background and assessment
2. Employee and social-media perspectives
3. Role, responsibilities, compensation and risks
4. Public HR/interviewer professional intelligence
5. Interview predictions and preparation
6. Sources, confidence and unresolved gaps

Findings are identified as verified facts, first-person statements, third-party opinions, analysis, predictions, or missing information. Important findings cite inspected public pages, original URLs and available dates. When the company or interviewer cannot be identified reliably, the report limits attribution rather than guessing.

**[Read a complete sample: Microsoft Software Engineer II](examples/report-us-software-engineer.md)** · [Input format](references/input-schema.md) · [Evidence format](references/evidence-schema.md) · [Report specification](references/report-spec.md)

## Advanced: run the local CLI

The CLI is useful for building or validating structured research. **It does not perform web searches by itself**; the agent fills the evidence document after inspecting accessible sources.

```bash
cd interview-intel

# See supported commands
python3 scripts/interview_intel.py --help

# Generate an English-first, country-aware research plan
python3 scripts/interview_intel.py plan examples/input-us-software-engineer.json --format markdown

# Create an empty research document for an agent to populate
python3 scripts/interview_intel.py scaffold examples/input-us-software-engineer.json --output research.json

# Validate a completed evidence document
python3 scripts/interview_intel.py validate research.json

# Produce the Chinese Markdown report
python3 scripts/interview_intel.py render research.json --output report.md

# Inspect candidate sources for Japan
python3 scripts/interview_intel.py catalog --country JP
```

Use [examples/research-us-software-engineer.json](examples/research-us-software-engineer.json) to try validation and rendering with already prepared example evidence. See [README.zh-CN.md](README.zh-CN.md) for a longer guided CLI walkthrough.

## Coverage and reliability

- **Global discovery:** country profiles and a modifiable [source catalog](references/source-catalog.json) route searches toward official sites, job boards, professional profiles, public communities and employer-review sites.
- **Evidence first:** search snippets and blocked pages are leads, not verified evidence. Reposts with one origin do not count as independent corroboration.
- **Interviewer identity:** a shared name is insufficient; public, compatible attributes and independent sources are required. Professional background does not prove participation in your interview or personal scoring preferences.
- **Privacy:** no login/CAPTCHA bypass, private-contact harvesting or unrelated sensitive personal profiling. Do not submit private resumes, passwords or restricted pages.
- **Honest failure:** inaccessible platforms, unmatched positions and missing evidence are reported as limitations. With no search tool, the Skill can provide a plan but not a live company research report.

Read the [research playbook](references/research-playbook.md), [source-routing rules](references/source-routing.md) and [known release limitations](CHANGELOG.md) for details.

## Development and contributions

```bash
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
```

Contributions and corrections are welcome through [Issues](https://github.com/gaochenyang666-droid/interview-intel/issues) and pull requests. Please do not publish candidate personal data, private interviewer details or copied login-gated content. See [CONTRIBUTING.md](CONTRIBUTING.md).

**License:** [MIT](LICENSE).
