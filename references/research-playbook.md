# Research playbook

## Evidence collection order

1. Company identity: official site, official careers page, official investor relations or filing page, and an official social profile.
2. Company state: latest official results or filing, recent credible news, workforce changes, and product changes.
3. Role: exact public posting first; then similar active and archived postings from the same employer.
4. **Mandatory employee/community experience:** after confirming company identity, attempt at least two distinct external platforms, preferably three. Open original publicly accessible posts and record search terms and outcomes. Separate claims by current or former employees where visible; employment claims remain unverified unless corroborated.
5. Interview experience: original posts with date, location, level, department, and interview stage. Prefer detailed contemporaneous accounts.
6. Compensation: level, location, currency, period, sample size, and date. Preserve missing sample size.
7. Role-level interview preparation: use accessible public accounts of interviews for the same role, location and level. Never identify or profile individual interviewers.

## Firsthand community search is required

Use `plan.community_targets` and platform-specific `community_platform` queries. Search distinct public communities and open original results where available. Examples:

```text
site:reddit.com "<company>" employee experience culture
site:zhihu.com "<company>" 员工 工作体验 加班
site:maimai.cn "<company>" 员工 评价
site:xiaohongshu.com "<company>" 离职 感受
site:openwork.jp "<company>" 社員 口コミ
site:blog.naver.com "<company>" 직원 후기
```

Look for positive, negative and mixed descriptions, exact role/team, relevant locale and recent dates. If an indexed result requires login or only exposes snippets, mark it inaccessible; **never reproduce a comment you did not actually read**. Continue with another platform until at least two have been tried.

In `research.coverage.community_attempts`, record each platform ID, **actual executed query**, outcome and verified evidence IDs for original accessible posts. A blocked platform still counts as an attempt, but provides no review evidence. If all original posts are inaccessible, state that no independently inspectable public employee review was found. A real URL verifies a post exists; it does not authenticate an anonymous poster's work history.

## Query pattern

Use English first:

```text
"<company>" "<role>" interview experience
"<company>" employee reviews salaries
site:reddit.com "<company>" "<role>" interview experience
```

Then localize the action terms from the country profile:

```text
"<company>" "<local role>" (<local terms>)
"<company>" "<local role>" (<local interview terms>)
```

Do not translate a company's registered or product name unless an official local-language name is found. Retain aliases with their source.

## Disambiguation

- Strong matches: supplied official domain, supplied job URL, headquarters and role location, exact product line, compatible employee size.
- Weak matches: similar brand, translated name, common founder name, regional subsidiary with unclear ownership.
- When strong identifiers conflict, label the entity `ambiguous`. Summarize the alternatives and stop employer-specific conclusions.
- Focus on company and job identity. Individual interviewers are outside the scope of this Skill.

## Sample and bias checks

- Note self-selection in review sites; dissatisfied or departing employees may be overrepresented.
- Separate one person posting many times from multiple independent employees.
- Treat duplicate text, screenshots, content-farm summaries, and syndicated articles as one origin.
- Compare country, city, department, role, and time window. A company-wide average can hide team-level differences.
- Interview accounts change over time. Prefer recent accounts and state the cut-off.

## Compensation honesty

Report only observed values and source labels. Show `样本量未披露` when absent. Do not create a percentile, midpoint, or range from one anecdote. Keep currency and annualization explicit.

## Search budget and stopping rule

Use enough queries to confirm identity and the exact job, then search **at least two independently targeted community platforms** (prefer three), usually within 12 to 18 queries. Do not stop after reading company marketing pages. If posts are inaccessible, record attempts and access failures. Do not infer sentiment from missing data. Save context by opening only search results that can answer a defined research question.
