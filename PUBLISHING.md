# Interview Intel distribution and directory submissions

This project is hosted at **https://github.com/gaochenyang666-droid/interview-intel**. It is open source under MIT. Its canonical instructions are `SKILL.md`; all plugin hosts use the same shared research scripts and references.

## Immediately installable from GitHub

- **skills.sh and compatible agents:** `npx skills add gaochenyang666-droid/interview-intel --skill interview-intel`. The skills.sh leaderboard lists a skill after real installs; the repository alone is not proof of a listing.
- **Claude Code:** `/plugin marketplace add gaochenyang666-droid/interview-intel`, then `/plugin install interview-intel@interview-intel-marketplace`. This installs from our self-hosted marketplace, not the curated Anthropic directory.
- **Gemini CLI:** `gemini extensions install https://github.com/gaochenyang666-droid/interview-intel`. The gallery separately requires the GitHub topic `gemini-cli-extension` and a successful crawler validation.
- **Cursor:** Supports the root Agent Plugins `plugin.json` and Skill entry at `skills/interview-intel/SKILL.md`; users can import the repository as a compatible plugin where supported. For public Cursor Marketplace review use https://cursor.com/marketplace/publish.

## Public directory submission checklist

| Directory | Submission | Current publication status |
| --- | --- | --- |
| skills.sh | Install telemetry using `npx skills add` | Repository prepared; listing not confirmed |
| Gemini CLI gallery | Add repository Topic `gemini-cli-extension` on GitHub; automatic daily crawler | Manifest prepared; GitHub Topic/action required |
| Claude official/community plugin directory | https://clau.de/plugin-directory-submission | Self-hosted marketplace prepared; curated directory submission not confirmed |
| Cursor public marketplace | https://cursor.com/marketplace/publish | Agent Plugin prepared; manual review/form required |
| agentskill.sh | https://agentskill.sh/submit | GitHub import form; not confirmed |
| OpenAgentSkill | https://www.openagentskill.com/submit | Free repository queue; not confirmed |
| SkillsMP | https://skillsmp.com | Indexed from GitHub; no guaranteed or verified listing |
| KillerSkills | https://killerskills.ai/submit | Requires sign-in; not submitted |
| agent-skills.market | https://agent-skills.market/submit | Paid listing ($25); **do not pay without explicit approval** |

Other marketplaces may have different eligibility, review and security requirements. Installing the project from a compatible GitHub source does not imply endorsement by any vendor.

## Listing text

**Title:** Interview Intel

**Subtitle:** Global interview research with authentic public workplace discussions

**Description:** An open-source Agent Skill for researching employers and job roles across countries. It checks official job postings, public employee reviews, local-language workplace communities, salary evidence and public interview experiences. Produces a source-cited Chinese interview intelligence report with explicit limitations. Requires only country, company and role. No interviewer identity profiling; numeric scoring off by default.

**Categories:** Research, Productivity, Job Search, Career, Agent Skills

**Keywords:** interview preparation, employer research, job research, employee reviews, workplace culture, salary insights, global hiring, osint, agent skill

**Source:** https://github.com/gaochenyang666-droid/interview-intel

**SKILL.md:** https://github.com/gaochenyang666-droid/interview-intel/blob/main/SKILL.md

**License:** MIT

## Before public directory submission

1. Run `python3 -m unittest discover -s tests -v` and check GitHub Actions.
2. Confirm the chosen host can read the plugin wrapper and repository-root `SKILL.md` and invoke scripts using the correct installed absolute path.
3. If requested, submit the GitHub repository URL and the listing text above through each official form. Do not claim approval or indexing until a published directory entry or acceptance notice exists.
