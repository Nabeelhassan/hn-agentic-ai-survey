# Status — 2026-11-15

First snapshot of the thread is built, verified in a browser, and deployed from `main`.

- Repo: https://github.com/Nabeelhassan/hn-agentic-ai-survey
- Dashboard: https://nabeelhassan.github.io/hn-agentic-ai-survey/
- Snapshot: `2026-11-15T182416Z`

## What exists

| Layer | State |
| --- | --- |
| Fetch | 716 Algolia comments, 856 Firebase nodes (140 dead/deleted), 500 top-level, frozen under `data/raw/` |
| Normalize | 833 comments with text, depth resolved, content hashed |
| Taxonomy | v1, 100 nodes across subscriptions, harnesses, orchestration, platforms, model routes, named models |
| Extraction | 2 models × 833 comments = 1,666 records, 242 review items, **$0.59** actual spend |
| Merge | 413 respondents with a stated setup out of 659 commenters |
| Aggregates | 9 files, every row carrying `n_denominator` and `comment_ids` |
| Pricing catalog | v1: 21 providers, 62 plans, 55 with a price, 249 of 385 tier strings resolved |
| Dashboard | 7 views, all render; explorer virtualized with keyboard-focusable rows and a detail dialog |
| Accuracy | 40-comment gold set: 0.90 classification; F1 0.99 / 0.75 / 0.78 / 0.54 / 0.89 |
| Deploy | GitHub Actions → Pages, `base` set to `/hn-agentic-ai-survey/` |

## What it found

Snapshot `2026-11-15T182416Z` — 856 comments, 833 with text, 413 respondents.

- **Subscriptions:** Anthropic 172 (41.6%), OpenAI 113, OpenCode Go 21, Google 19, Cursor 14, xAI 13. 124 pay for two or more.
- **Harnesses:** Claude Code 152, Codex CLI 70, Pi 65, OpenCode 58.
- **Models outside subscriptions:** DeepSeek 65, OpenRouter 52, Qwen 50. Local hosting is real but smaller than APIs.
- **Orchestration:** 62 custom setups, Herdr 24. **Platforms:** Hermes Agent 27, Grok Bot 12, OpenClaw 11.
- **Plans:** Anthropic Ultra 52, Pro 45, Max 41; OpenAI Plus 32 and Pro 28 (OpenAI prices were not exposed by its page). Free tiers are listed with zero respondents.
- **Migrations:** 42 stated moves, netted into an acyclic Sankey; the full from→to table sits underneath.
- **Themes:** 25 clustered labels from 1,252 raw phrases, led by tool opinions, subscription value, and DIY harnesses.

## Known weaknesses, stated rather than hidden

- **Orchestration is the weakest field** (F1 0.54). The model and the gold set disagree on where a custom harness ends and orchestration begins.
- Models and harnesses score 0.75–0.78; the long tail lands in `other:<name>` by design.
- 49 theme phrases stayed unclustered instead of being forced into a bucket.
- Eleven providers have pricing gaps: six without any verified price (CodeBuddy, Z.ai, Kimi, MiniMax, Perplexity, Muse Code) and five partial (OpenAI, xAI, Amp, Mistral, Synthetic). Catalog prices are list prices, not what anyone paid.
- 136 tier assignments did not resolve to a plan, 67 of which stated no tier at all.
- Comment scores are unavailable from the HN API, so nothing is weighted by points.
- The thread is live; comments after the snapshot are not included.

## Next

1. Take snapshot #2 once the thread goes cold, and diff the two.
2. Improve the orchestration boundary in `taxonomy/v1.yml` and the extraction prompt together, then re-score.
3. Fill catalog gaps and add missing alias forms (`$100` for OpenAI, `Pro 200`), then re-aggregate.
4. UI design pass; the current layout is functional, not styled.
5. Consider code-splitting the dashboard bundle (ECharts is most of the 973 kB).
