# Research playbook

## Evidence collection order

1. Company identity: official site, official careers page, official investor relations or filing page, and an official social profile.
2. Company state: latest official results or filing, recent credible news, workforce changes, and product changes.
3. Role: exact public posting first; then similar active and archived postings from the same employer.
4. Employee experience: country-appropriate review platforms and public forums. Separate current and former employees where visible.
5. Interview experience: original posts with date, location, level, department, and interview stage. Prefer detailed contemporaneous accounts.
6. Compensation: level, location, currency, period, sample size, and date. Preserve missing sample size.
7. Interviewer: supplied public profile, official company bio, public technical projects, talks, articles, and first-person posts. Confirm the person with multiple compatible attributes.

## Query pattern

Use English first:

```text
"<company>" "<role>" interview experience
"<company>" employee reviews salaries
site:linkedin.com/in "<name>" "<company>" "<role>"
```

Then localize the action terms from the country profile:

```text
"<company>" "<local role>" (<local terms>)
"<name>" "<company>" (<local professional terms>)
```

Do not translate a company's registered or product name unless an official local-language name is found. Retain aliases with their source.

## Disambiguation

- Strong matches: supplied official domain, supplied job URL, headquarters and role location, exact product line, compatible employee size.
- Weak matches: similar brand, translated name, common founder name, regional subsidiary with unclear ownership.
- When strong identifiers conflict, label the entity `ambiguous`. Summarize the alternatives and stop employer-specific conclusions.
- For people, require at least two independent compatible attributes. A personalized profile URL supplied by the requester is a strong lead, but still verify public title and employer.

## Sample and bias checks

- Note self-selection in review sites; dissatisfied or departing employees may be overrepresented.
- Separate one person posting many times from multiple independent employees.
- Treat duplicate text, screenshots, content-farm summaries, and syndicated articles as one origin.
- Compare country, city, department, role, and time window. A company-wide average can hide team-level differences.
- Interview accounts change over time. Prefer recent accounts and state the cut-off.

## Compensation honesty

Report only observed values and source labels. Show `样本量未披露` when absent. Do not create a percentile, midpoint, or range from one anecdote. Keep currency and annualization explicit.

## Search budget and stopping rule

Start with official pages and the exact role, then cover the two most relevant review/community platforms and interviewer queries. Use about 12 to 18 queries by default. Stop when the core questions have enough independent evidence, when results repeat known lineage, or when access failures make further attempts low-value. Save context by opening only search results that can answer a defined research question.
