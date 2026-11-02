# Changelog

All notable changes to Interview Intel are documented here.

The format follows Keep a Changelog and the project uses semantic versioning.

## [0.2.0-beta.1] - 2026-11-02

### Added

- Added public historical interview research with four source tiers: same company and role, same company and related role, comparable company and role, and role-based prediction.
- Added a ten-question generator with source labels, migration rationale, category diversity, competencies, answer outlines, and recommended answer structure.
- Added evidence validation that requires historical question text to match a linked public interview experience.
- Added a stateful interactive mock interview with scene selection, one-question-at-a-time output, contextual follow-up, adaptive difficulty, local state, and final feedback.
- Added conversational controls for starting, finishing, and restarting a mock session.
- Added role-specific question mixes for engineering, data, product, operations, and management roles.
- Added regression tests for evidence tiers, mislabelled questions, duplicate prompts, follow-ups, difficulty changes, and complete sessions.

### Changed

- Expanded the Chinese report to six sections, adding public historical interview experiences and matching before interview preparation.
- Updated the canonical Skill, portable entrypoint, evidence schema, report specification, input schema, and four language READMEs.
- Kept three-field input with `0` as unknown, interviewer profiling disabled, and company numeric scoring off by default.
- Preserved legacy research JSON and `mock_questions` compatibility by normalizing legacy questions to predictions.
- Made engineering, data, product, operations, and management roles produce materially different question categories.
- Prioritized the selected mock interview scene while retaining historical evidence preference inside relevant categories.

### Fixed

- Accepted month-precision interview dates from public interview posts.
- Removed weak-action false positives from mock answer analysis.
- Added evidence ID remapping for interview experiences and comparable companies during URL deduplication.
- Prevented fabricated historical questions by requiring exact text in the linked public account.
- Fixed the Qwen AI ZIP packager so its archive contains a root-level `SKILL.md`, filters cache files, verifies archive integrity and size, and supports the QwenWork folder-wrapped layout.

### Distribution

- Added Gemini CLI extension metadata and a shared portable plugin skill wrapper.
- Added Claude Code self-hosted marketplace and Agent Plugins manifest support for Cursor.
- Added publishing instructions and offline packaging regression tests. Public directory approval remains separate.

### Security

- Rejected prompt-injection instructions from source text.
- Required independent source origins before high-confidence corroboration.
- Redacted unrelated private email addresses, phone numbers, and residential addresses.
- Kept raw QA research, source excerpts, local mock interview state, and candidate data out of the public repository.

### Known limitations

- Search depends on the host agent and accessible public sources.
- Login-gated and CAPTCHA-protected pages remain out of scope.
- Anonymous reviews and self-reported salaries cannot support high-confidence facts.
- Local simulator follow-up analysis uses deterministic heuristics.
- Native-language alias coverage remains limited.

## [0.1.0-beta.1] - 2026-11-02

### Added

- Installable Agent Skill with a standard `SKILL.md` entrypoint.
- English-first multilingual search planning for 19 country profiles.
- Extensible catalog of global, regional, and local research sources.
- Evidence schema, source deduplication, lineage tracking, and confidence ceilings.
- Simplified Chinese report rendering.
- Company, role, salary, and public employee research workflows.
- Three-field input with `0` as unknown.
- Input validation for ambiguous company entities.
- Offline and partial-network degradation behavior.
- Security hardening for prompt injection and unrelated private information.
- GitHub Actions test matrix and community documentation.

### Changed

- Removed individual interviewer profiling from active planning and reports.
- Retired the historical `kanzhun.com` route after the domain no longer served the expected employer-review product.
- Local-language query selection now survives a four-query research budget.
- Numeric opportunity scoring became opt-in.

### Known limitations

- Search is performed by the host Agent rather than a bundled search engine.
- Login-gated and CAPTCHA-protected sources are intentionally out of scope.
- Anonymous employee reviews and self-reported salaries cannot support high-confidence company facts.

[0.2.0-beta.1]: https://github.com/gaochenyang666-droid/interview-intel/compare/v0.1.0-beta.1...main
[0.1.0-beta.1]: https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1
