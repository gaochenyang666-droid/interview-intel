# Contributing to Interview Intel

## Before opening a change

- Keep the research workflow evidence-led and source-grounded.
- Do not add private, purchased, login-protected, or access-controlled content.
- Do not add API keys, credentials, résumés, home addresses, private contact information, or unrelated personal data.
- Do not claim an interviewer's participation or preference without a public evidence basis.
- Treat search snippets as discovery only.

## Development setup

No third-party runtime dependencies are required.

```bash
python3 --version
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

Use Python 3.10 or newer. The GitHub Actions workflow tests Python 3.10 through 3.13.

## Pull requests

1. Describe the problem and the evidence source.
2. Keep changes narrowly scoped.
3. Add or update tests for behavior changes.
4. Run the full test suite.
5. Confirm no private or restricted material was added.

## Commit messages

Use Conventional Commit style:

```text
feat(scope): Add a capability
fix(scope): Correct a reproducible defect
docs: Update usage guidance
test: Add regression coverage
ci: Update workflow configuration
```

Keep the subject imperative and under 70 characters. Explain the reason in the body.

## Source changes

When adding a source:

- verify its official public URL;
- record region, language, category, access constraints, and login status;
- do not invent undocumented endpoints;
- mark obsolete or repurposed domains as `retired`;
- update routing tests.

## Evidence changes

An important conclusion should reference evidence records rather than becoming an unsupported narrative assertion. Do not average away conflicting anonymous reviews. Keep regional, departmental, and temporal limitations visible.
