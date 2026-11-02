# Interview Intel

**Global interview research for AI agents, with traceable sources.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Tests](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Latest beta release](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [MIT License](LICENSE)

Prepare for an interview with more context than a job description. **Interview Intel** is an installable Agent Skill that researches an employer, a specific role, public workplace discussions, compensation signals, interview processes, . It produces a **source-linked report in Simplified Chinese** with explicit confidence and evidence limitations.

> **Public beta: v0.1.0-beta.1.** The Skill uses the **host agent's web search/browser tools** for live research. The included Python scripts plan queries, validate evidence, and render reports; they **do not independently crawl websites**.

## Quick start: just three fields

Paste these three lines into any supported Agent with Interview Intel installed:

```text
Country: China
Company: ByteDance
Role: Product Operations
```

**Use `0` for any unknown field.** Country `0` means global search; company `0` means role-level research; role `0` means employer research. At least one of company or role is required. No résumé, job link or personal profile is needed. Numeric scoring is off by default.

For CLI users:

```bash
python3 scripts/interview_intel.py quick "China/ByteDance/Product Operations" --output request.json
```

The Agent then performs the web research and generates the report. This command only builds the input JSON.

## What can it help with?

| Question | What the report covers |
| --- | --- |
| Is this company worth considering? | Official company facts, business context, workplace feedback, recent hiring signals, and disagreements across sources. |
| What is this job really asking for? | Verified job description, responsibilities, skill gaps, compensation observations, role and location differences. |
| How do employees describe the workplace? | Public employee reviews and social discussions with dates, sampling caveats, and source independence checks. |
| How should I prepare? | A targeted preparation plan, follow-up questions, and **10 labeled practice questions** tied to available evidence. |

Search begins in **English** and adds the relevant **local language**. A country-aware source catalog includes candidates such as LinkedIn, Indeed, Glassdoor, Reddit, Blind, 牛客, 脉脉, OpenWork, JobPlanet, Naukri, SEEK and regional job boards. **Listing a platform does not imply unrestricted access or verified content.**

## Install on your AI agent

Interview Intel follows the **Agent Skills (`SKILL.md`)** format. It can be installed on several AI coding agents that read skill folders; the underlying model name (GPT, Claude, Gemini, etc.) is not itself an installation method.

**Requirements:** Git, Python 3.10+, and an agent with public web search/browser access and permission to run local Python commands. No paid API or third-party Python runtime dependencies are required for the included utilities.

### Option A: One shared installation for several agents

On macOS or Linux, the cross-agent **`~/.agents/skills/`** location is supported by Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode and compatible Windsurf / Devin Desktop versions:

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Open a new session or reload the agent's skills. **Claude Code uses `~/.claude/skills/`**, so install to its dedicated directory with:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

Alternatively, use a client's dedicated directory or install only for one repository:

| AI client | Personal skill folder | Project skill folder |
| --- | --- | --- |
| **OpenAI Codex** | `~/.agents/skills/` | `.agents/skills/` |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Google Gemini CLI** | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| **Cursor** | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| **GitHub Copilot (CLI / VS Code Agent)** | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` or `~/.agents/skills/` | `.opencode/skills/` or `.agents/skills/` |
| **Windsurf / Devin Desktop** | `~/.codeium/windsurf/skills/` or `~/.agents/skills/` | `.windsurf/skills/` or `.agents/skills/` |

All locations in the table are **parent folders**. The complete project folder, including `SKILL.md`, `scripts/` and `references/`, must be installed as `<parent>/interview-intel/`. Do not copy `SKILL.md` alone. You can use `cp -R interview-intel <parent>/interview-intel` after cloning. On Windows, use the equivalent user-home paths and file-copy commands.

### Option B: Gemini CLI's installer

Gemini CLI also provides an official Git repository installer:

```bash
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
gemini skills list
```

Inside Gemini CLI, use `/skills list` or `/skills reload` to confirm discovery and approve activation when prompted.

### China-developed AI agents

The following China-developed clients support native Agent Skills based on `SKILL.md`: **Qwen Code, Kimi Code CLI, TRAE China, Qoder, Tencent CodeBuddy Code and Zhipu ZCode**. After cloning the repository as shown above, install its **complete directory** (including scripts and references) in your preferred client:

```bash
# Qwen Code
mkdir -p ~/.qwen/skills && cp -R interview-intel ~/.qwen/skills/interview-intel
# Kimi Code CLI
mkdir -p ~/.kimi-code/skills && cp -R interview-intel ~/.kimi-code/skills/interview-intel
# TRAE (China)
mkdir -p ~/.trae-cn/skills && cp -R interview-intel ~/.trae-cn/skills/interview-intel
# Tencent CodeBuddy Code
mkdir -p ~/.codebuddy/skills && cp -R interview-intel ~/.codebuddy/skills/interview-intel
# Zhipu ZCode
mkdir -p ~/.zcode/skills && cp -R interview-intel ~/.zcode/skills/interview-intel
```

**Qoder:** Reuse `~/.agents/skills/interview-intel/`, or import a reviewed ZIP via **Extensions → Skills → Add Skills → Upload Skill**.

**Invoking the Skill:** Qwen Code: `/interview-intel` (or `/skills`); Kimi Code CLI: `/skill:interview-intel`; Tencent CodeBuddy Code: check `/skills`; ZCode: **Settings → Skills → Refresh**; TRAE: ask the Agent to use Interview Intel; Qoder: select through `/`.

**Other supported locations:** Qwen Code: `~/.agents/skills/`, project `.qwen/skills/`; Kimi Code CLI: `~/.agents/skills/`, project `.kimi-code/skills/`; TRAE project `.trae/skills/` (project `.agents/skills/` must be enabled in Settings → Skills & Commands); CodeBuddy Code project `.codebuddy/skills/`.

**Models versus clients:** DeepSeek, Doubao, GLM and MiniMax can be used through agents that support them. The model or consumer chatbot alone does not guarantee `SKILL.md` loading. Full Interview Intel operation still requires live web search and Python execution.

Official documentation: [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) · [Kimi Code CLI](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html) · [TRAE](https://docs.trae.cn/ide_skills?lang=zh) · [Qoder](https://docs.qoder.com/qoder/skills) · [CodeBuddy Code](https://www.codebuddy.cn/docs/cli/skills) · [ZCode](https://zcode.z.ai/en/docs/skill)

### ChatGPT and Claude in the browser

- **ChatGPT Skills:** On an eligible ChatGPT workspace, open **Plugins → Skills → Create → Upload from your computer** and upload a reviewed copy of the skill package. Availability depends on account/workspace settings. This is separate from installing a folder for Codex. See [OpenAI's Skills guide](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
- **Claude.ai:** Eligible users can add custom Skills via Claude's Skills/settings interface, typically using a ZIP package. The browser's code and web access may differ from Claude Code. See [Anthropic's Agent Skills guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

Because Interview Intel relies on **live searches and Python validation**, make sure the chosen interface offers both capabilities. In a chat-only interface without file execution, you can reuse the research methodology, but you cannot claim the full validated CLI workflow ran.

### Invoke the skill

| Host | Example invocation or discovery |
| --- | --- |
| Codex | `Use the Interview Intel skill to research ...` |
| Claude Code | `/interview-intel` or ask Claude to use the Interview Intel skill |
| Gemini CLI | Ask to use Interview Intel; inspect with `/skills list` |
| Cursor / GitHub Copilot / OpenCode | Use agent mode and ask: `Use the Interview Intel skill to research ...` |
| Windsurf / Devin Desktop | Ask Cascade to use Interview Intel; `@interview-intel` where supported |
| ChatGPT / Claude browser | Select or invoke the uploaded custom skill where available |

Example prompt (works conceptually across all supported agents):

```text
Use the Interview Intel skill to prepare a source-linked interview report.
Company: Microsoft
Role: Software Engineer II
Location: Redmond, Washington, United States
Job URL: [optional public job posting]
My background: C#, distributed systems, Azure, testing
Focus: interview process, team culture, system design and compensation
```

**At least company or role is required.** Country, job URL, interview stage and candidate experience are optional. The current report renderer outputs **Simplified Chinese**, regardless of the language of these installation instructions.

**Official setup references:** [Codex](https://learn.chatgpt.com/docs/build-skills) · [Claude Code](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [Gemini CLI](https://geminicli.com/docs/cli/skills/) · [Cursor](https://cursor.com/docs/skills) · [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) · [OpenCode](https://opencode.ai/docs/skills) · [Windsurf / Devin Desktop](https://docs.devinai.cn/desktop/cascade/skills)

## Usage examples

**Explore an employer and role:**

```text
Use $interview-intel. Company: Toyota. Role: Product Manager.
Country: Japan. Search Japanese workplace and job sources, compare
the responsibilities with the official listing, and output the cited Chinese report.
```

**Evaluate competing evidence:**

```text
Use the Interview Intel skill to research [company] for [role] in [city].
Compare official hiring information with recent, accessible employee
reviews. Distinguish first-hand claims, anonymous opinions and unknowns.
```

## What the finished report looks like

The output is a **Simplified Chinese Markdown report**, with a one-page summary followed by five numbered sections:

1. Company background and assessment
2. Employee and social-media perspectives
3. Role, responsibilities, compensation and risks
4. Interview predictions and preparation
5. Sources, confidence and unresolved gaps

Findings are identified as verified facts, first-person statements, third-party opinions, analysis, predictions, or missing information. Important findings cite inspected public pages, original URLs and available dates. If the company cannot be identified reliably, its details are withheld rather than guessed.

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

## Public workplace discussions, firsthand reviews and social media

When a company is supplied, Interview Intel **actively searches at least two different external community platforms**, ideally three. It uses site-specific queries and the target country's local language. In China, candidates include Zhihu, Maimai, Xiaohongshu, Nowcoder and Weibo; elsewhere it selects appropriate local and international communities.

The report lists **platforms actually attempted**, links to publicly accessible original posts, and positive or negative experiences when available. It flags anonymous authors, unknown sample sizes, older posts, team/location differences, login barriers and inaccessible pages. Publicly accessible anonymous posts are **not independently verified employee identities**. Company marketing pages do not replace community accounts.

**Numeric scoring is disabled by default** so attention stays on traceable research. Users can explicitly request the advanced [optional scoring rubric](references/scoring-rubric.md).

## Skill marketplaces and direct installation

Interview Intel includes plugin/extension manifests for **Claude Code**, **Gemini CLI** and **Cursor**, alongside its original cross-agent `SKILL.md`. These install from the public GitHub repository; inclusion in a vendor's **curated directory** requires separate indexing or review.

```bash
# skills.sh and compatible Agent Skills clients
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel

# Gemini CLI extension
gemini extensions install https://github.com/gaochenyang666-droid/interview-intel
```

In Claude Code run `/plugin marketplace add gaochenyang666-droid/interview-intel`, then `/plugin install interview-intel@interview-intel-marketplace`. The public Cursor Marketplace uses a separate review process.

See [publishing status, submission links and ready-made listing metadata](PUBLISHING.md). Public directory approval is **not** implied by a working GitHub install.

### Mainland China Skill directories

Qwen AI Platform offers a public Skill marketplace with ZIP submission and identity verification. Build a checked, root-level-SKILL.md ZIP with `python3 scripts/package_skill.py --format qwen-ai --output ~/Downloads/interview-intel-skill.zip`. Kimi supports installing a shared GitHub Skill URL. See [the publishing guide](PUBLISHING.md) for the Qwen ZIP packaging command, publisher review requirements and links.

## Coverage and reliability

- **Global discovery:** country profiles and a modifiable [source catalog](references/source-catalog.json) route searches toward official sites, job boards, professional profiles, public communities and employer-review sites.
- **Evidence first:** search snippets and blocked pages are leads, not verified evidence. Reposts with one origin do not count as independent corroboration.
- **Privacy:** no login/CAPTCHA bypass, private-contact harvesting or unrelated sensitive personal profiling. Do not submit private resumes, passwords or restricted pages.
- **Honest failure:** inaccessible platforms, unmatched positions and missing evidence are reported as limitations. With no search tool, the Skill can provide a plan but not a live company research report.

Read the [research playbook](references/research-playbook.md), [source-routing rules](references/source-routing.md) and [known release limitations](CHANGELOG.md) for details.

## Development and contributions

```bash
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
```

Contributions and corrections are welcome through [Issues](https://github.com/gaochenyang666-droid/interview-intel/issues) and pull requests. Please do not publish candidate personal data, private personal details or copied login-gated content. See [CONTRIBUTING.md](CONTRIBUTING.md).

**License:** [MIT](LICENSE).
