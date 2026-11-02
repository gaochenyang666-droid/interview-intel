# Input schema

The CLI accepts UTF-8 JSON. Only `company.name` and `role.title` are required.

```json
{
  "company": {
    "name": "Example Corporation",
    "website": "https://example.com",
    "industry": "Enterprise software"
  },
  "role": {
    "title": "Senior Product Manager",
    "url": "https://example.com/jobs/123",
    "description": "Paste a public JD only. Remove candidate data.",
    "level": "Senior"
  },
  "location": {
    "country": "US",
    "city": "Seattle"
  },
  "interviewers": [
    {
      "name": "Public Name",
      "title": "Director of Product",
      "department": "Platform",
      "profile_url": "https://www.linkedin.com/in/example"
    }
  ],
  "candidate": {
    "summary": "Eight years in B2B product; enterprise platform and API experience.",
    "skills": ["product discovery", "platform strategy", "SQL"],
    "preferences": ["hybrid work", "learning opportunities"]
  },
  "focus": ["organization health", "system design", "salary negotiation"],
  "research": {
    "max_queries": 18,
    "recency_months": 18,
    "languages": ["en"]
  }
}
```

## Field behavior

- `company.website` and `role.url` are strong entity clues, not proof that the search results concern the correct employer.
- `location.country` accepts a two-letter ISO-style code, English country name, or common Chinese name. Unknown values produce a warning and fall back to global English research.
- `research.languages` adds languages to the country route. The planner still runs English first.
- `candidate.summary` must contain role-relevant information only. The tool does not log or persist it separately.
- Interviewer names are identity leads. A name alone never establishes an identity.

## Research plan output

`plan` returns:

- normalized input and inferred or supplied country;
- entity resolution status and questions that genuinely block attribution;
- ordered query tasks with language, category, priority, and candidate domains;
- a ranked source shortlist;
- network state and capability limits;
- the required research JSON skeleton.

- `candidate.preferences` is optional and is used only for the contextual preference-match score. If the user does not disclose preferences, this factor remains **unscored**. See [scoring-rubric.md](scoring-rubric.md).
