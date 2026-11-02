# Chinese report specification

For the legacy/complete input, the renderer keeps the following sections in order. For `quick_mode: true`, numbered sections that depend on a skipped `0` field are omitted: no company skips company/reviews, no role skips role/preparation, and no interviewer skips interviewer information. The summary and source section remain.

1. `一页式摘要`
2. `1. 公司概况与综合评价`
3. `2. 员工及社交媒体评价`
4. `3. 岗位评价`
5. `4. HR / 面试官公开情报`
6. `5. 面试预测与准备`
7. `6. 来源与可信度`

## Language and evidence style

- Write in Simplified Chinese. Preserve a source title's original language in the source appendix.
- Only use the optional, evidence-validated opportunity scoring rubric in [scoring-rubric.md](scoring-rubric.md). Insert the breakdown within the one-page summary. If evidence is missing or an identity is unconfirmed, withhold the overall score. Never present the result as an objective employer ranking or hiring probability.
- Use `事实`, `本人公开表述`, `第三方评价`, `分析推断`, `面试预测`, `信息缺口`, and `准备建议` labels consistently.
- Put evidence IDs next to every evidence-dependent bullet. Put clickable original URLs in the appendix.
- Summaries must be traceable to finding IDs. Do not add facts in the summary that are absent from traceable findings.
- Distinguish `未找到可靠公开证据` from `未检索` and from `页面无法访问`.
- Mention search date, intended languages, actual languages attempted, and inaccessible sources.

## Candidate-specific preparation

- Use only the candidate information supplied by the user.
- If candidate context is missing, give a role-based checklist and explicitly mark personal fit as unavailable.
- Each mock question needs a basis and an answer outline. Mix technical or role-specific prompts with behavioral prompts.
- STAR suggestions should identify what metric, tradeoff, conflict, or outcome the answer must expose.
- Negotiation advice should reference only sourced compensation observations and explain uncertainty.

## Quality gate

Before presenting the report, confirm:

- Company identity is confirmed or clearly marked unresolved.
- An unconfirmed interviewer has no attributed career details.
- Each fact-like conclusion has an eligible evidence record.
- Every URL came from an actually inspected page or a user-provided public URL.
- Source dates and sample limitations are honest.
- Reposted material is not counted as independent corroboration.
- Search snippets and inaccessible pages are not presented as verified facts.

## Optional opportunity-scoring block

Inside `一页式摘要`, a separate `### 面试机会评分` block displays an experimental opportunity index (only if eligible), dimension scores, coverage percentages, source-quality grades, fixed weights and finding citations. It does not create a seventh numbered report section. If ratings were not supplied, show `暂未评分`. The 0–100 values are weighted conversions of 1–5 coded judgments; they are not probabilities.
