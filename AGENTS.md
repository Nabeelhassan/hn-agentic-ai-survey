# Agents

## Before touching the dashboard

- UI SDK is installed here. Before using `@ui-sdk/react`, read `dashboard/node_modules/@ui-sdk/react/docs/llms.txt`.
- To build a new primitive, search `dashboard/node_modules/@ui-sdk/react/docs/core.md` by heading, then read `rendering.md` next to it.
- Keep every UI SDK part behind `dashboard/src/components/ui/` adapters. The library is beta and APIs move.

## Vocabulary

`CONTEXT.md` is the glossary. Respondent, commenter, substantive answer, subscription, tier,
harness, platform, orchestration, second-hand report, snapshot, and extraction run have exact
meanings here. Use them.

## Rules

- Snapshots are immutable. Never rewrite a committed `data/snapshots/<id>/`; take a new one.
- Every aggregate must carry `n_denominator` and `comment_ids`.
- Below `n = 10`, show counts, not percentages.
- Never drop "unstated" from a breakdown.
- `data/raw/` holds the frozen source. Re-extraction reads it; it never refetches.
