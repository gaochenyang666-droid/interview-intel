# Changelog

All notable changes to Interview Intel are documented here.

The format follows Keep a Changelog and the project uses semantic versioning.

## [0.1.0-beta.1] - 2026-11-02

### Added

- Installable Agent Skill with a standard `SKILL.md` entrypoint.
- English-first multilingual search planning for 19 country profiles.
- Extensible catalog of global, regional, and local research sources.
- Evidence schema, source deduplication, lineage tracking, and confidence ceilings.
- Six-section Simplified Chinese report rendering.
- Company, role, salary, interview, and public interviewer research workflows.
- Ten role-specific mock questions with explicit prediction labels.
- Input validation for ambiguous company entities and unresolved interviewer identities.
- Offline and partial-network degradation behavior.
- Regression tests for the target countries, conflicting evidence, sparse data, and source deduplication.
- Security hardening for prompt injection and unrelated private information.
- GitHub Actions test matrix and community documentation.

### Changed

- Retired the historical `kanzhun.com` route after the domain was no longer serving the expected employer-review product.
- Local-language query selection now survives a four-query research budget.

### Security

- Reject evidence containing prompt-injection instructions.
- Require independent source origins before confirming a public person's identity.
- Redact unrelated private email addresses, phone numbers, and residential addresses.
- Exclude raw QA research and source-page excerpts from the public repository.

### Known limitations

- Search is performed by the host Agent rather than a bundled search engine.
- Login-gated and CAPTCHA-protected sources are intentionally out of scope.
- Anonymous employee reviews and self-reported salaries cannot support high-confidence company facts.
- Native-language entity aliases remain limited.

[0.1.0-beta.1]: https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1
