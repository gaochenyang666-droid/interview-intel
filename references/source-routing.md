# Dynamic source routing

`source-catalog.json` is a discovery catalog, not a claim that every source is universally reachable. Routing combines:

1. supplied country and city;
2. company entity and industry;
3. role family;
4. requested languages;
5. source `regions` and `use`;
6. runtime search reach and access limitations.

Global sources provide breadth. Country sources provide linguistic and workplace context. A platform is only selected when it can answer a current research question.

## Extending coverage

Add a source entry with:

```json
{
  "id": "unique-id",
  "name": "Public name",
  "home_url": "https://public.example/",
  "regions": ["XX"],
  "status": "active",
  "use": ["jobs", "reviews", "interview", "professional", "salary", "community"],
  "access": ["search_index", "public_web", "official_api", "user_provided"],
  "login_gated": true,
  "search_domains": ["public.example"]
}
```

Then add the ID to the relevant profile in `country-profiles.json`. Use a real public URL, describe login-gated behavior honestly, and do not add undocumented endpoints.

If a domain changes ownership or no longer represents the intended platform, set `status` to `retired`. Retired entries remain as an audit trail but are excluded from routing.

## Runtime fallback

- If a country is unknown, use the global profile and English.
- If local platforms are unreachable, keep the failed attempts in coverage and rely on accessible official or global sources.
- If no external tools exist, stop after emitting the plan.
- If a site only exposes search snippets, use those solely for discovery and mark them `snippet_only`.
