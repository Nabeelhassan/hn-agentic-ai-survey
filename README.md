# HN agentic AI survey

A tracked snapshot of the Ask HN thread ["What's your current AI agentic setup?"](https://news.ycombinator.com/item?id=50366117): what people pay for, which models they use outside those subscriptions, which harnesses they drive, what orchestration they run, and which agent platforms they actually use.

**Dashboard:** https://nabeelhassan.github.io/hn-agentic-ai-survey/

Docs: [architecture](docs/ARCHITECTURE.md) · [methodology](docs/METHODOLOGY.md) · [current status](docs/STATUS.md) · [glossary](CONTEXT.md)

## What makes this different from a thread summary

- **Counted per respondent, not per comment.** One author often spreads a setup across several comments and replies often describe a colleague's setup. Comments are extracted individually, merged per HN account, and second-hand reports are excluded from setup counts.
- **Every number is traceable.** Each aggregate row carries its denominator and the comment ids behind it, linked to the HN permalink.
- **Immutable snapshots.** `data/raw/<snapshot_id>/` is frozen. Re-analysis reads it; it never refetches. Corrections produce a new snapshot.
- **Accuracy is measured.** A hand-labelled gold set scores the extraction, and the result is published rather than implied.

## Layout

```
pipeline/            Python 3.13 + uv: fetch, normalize, extract, merge, aggregate
  prompts/           versioned extraction and harvest prompts
  taxonomy/          versioned canonical vocabulary + harvested candidates
dashboard/           Vite + React 19 + TypeScript, UI SDK + ECharts
data/raw/            frozen Algolia and Firebase payloads
data/snapshots/      comments, extractions, respondents, aggregates per snapshot
data/eval/           gold labels and the accuracy report
docs/                methodology and ADRs
```

## Commands

```bash
make fetch          # freeze a new snapshot from Algolia + Firebase
make normalize      # HTML -> text, depth, content hashes
make taxonomy       # harvest tool-name candidates (open-ended LLM pass)
make extract        # two-model structured extraction + review queue
make eval           # score against data/eval/gold_v1.jsonl
make aggregate      # respondents -> dashboard JSON
make dashboard-data # copy aggregates into dashboard/public/data
make dev            # dashboard at localhost:5173
make build          # static build in dashboard/dist
```

Extraction requires the `cmd` CLI authenticated (`cmd login`). Raw snapshots and derived data are committed, so a clone can rebuild the dashboard without any model calls.

## Snapshot policy

The thread is live. Snapshot `2026-11-15T182416Z` is the first fetch: 716 Algolia comments, 856 Firebase nodes including dead and deleted comments, 500 top-level. A second snapshot is taken once the thread goes cold, and the two are compared rather than one overwriting the other.

## Limitations

- Comment scores are not exposed by the HN API, so nothing is weighted by points.
- Counts are per HN account; one person with two accounts counts twice.
- Employer-provided seats are excluded unless the author chose the plan and pays for it themselves.
- Spend is only counted when a monthly figure was stated; currencies are not converted.
- Below `n = 10`, tables show counts instead of percentages, and "unstated" is always a visible row.
