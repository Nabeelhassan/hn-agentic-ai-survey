# Methodology

## Data source

The thread is fetched from two free Hacker News APIs:

- **Algolia** (`hn.algolia.com/api/v1/search`) supplies comment text, author, parent, and timestamps in paged calls.
- **Firebase** (`hacker-news.firebaseio.com/v0/item/<id>.json`) supplies the authoritative reply tree, including comments Algolia does not index (dead or deleted).

Both payloads are frozen under `data/raw/<snapshot_id>/` and committed. Nothing downstream refetches HN.

At snapshot `2026-11-15T182416Z`: Algolia returned 716 comments, matching HN's `descendants` count. The Firebase tree contained 856 nodes, of which 140 were absent from Algolia — dead or deleted comments that are retained, marked, and excluded from setup counts because they have no text.

Comment scores are not exposed by either API for comments, so **nothing is weighted by points**.

## Unit of analysis

1. Every comment with text is extracted independently.
2. Records are merged per HN author into a **respondent**.
3. Only respondents with at least one substantive answer feed the setup charts.
4. Comments describing someone else's setup are marked `second_hand` and excluded from those counts.
5. When two comments by one author disagree, the latest statement wins for the aggregate, and the conflict is recorded on the respondent and flagged in the explorer.

This prevents one enthusiastic author from inflating a tool's share, and stops a reply about a colleague becoming a data point.

## Extraction

- Two models run the same prompt and taxonomy: `z-ai/glm-5.3-flash` and `deepseek/deepseek-v4.1-flash`, through the Command Code headless CLI (`cmd -p`) at low reasoning effort.
- Comments are batched 30 at a time; outputs are validated against a JSON schema and repaired once if malformed.
- Each record stores `model`, `prompt_hash`, `taxonomy_version`, `schema_version`, and the comment's `content_hash`.
- Records with confidence below 0.6, or where the two models disagree on the substance, go to `review.jsonl`.
- Actual token usage is recorded per run and priced into `meta.json`.

## Taxonomy

The canonical vocabulary is grown from the thread, not guessed:

1. An open-ended harvest pass lists every product mentioned, with raw forms.
2. Candidates are clustered by frequency and category.
3. `pipeline/taxonomy/v1.yml` is reviewed and approved before forced-choice extraction.
4. Extraction must pick a listed node id; anything unlisted becomes `other:<name>` so new tools stay visible instead of collapsing into "other".

Nodes may belong to more than one category: Cursor, Kiro, Amp, Warp, Devin, and CodeBuddy are both a harness and a paid plan.

## Aggregation rules

- Counts are unique respondents, not mentions.
- Every row carries `n_denominator` and `comment_ids`.
- `unstated` is always a row; it is never dropped to make percentages sum to 100.
- Below `n = 10`, the UI shows counts rather than percentages.
- Spend is only counted when the author stated a monthly figure; annual plans, credits, and per-token pricing are recorded as tier text and left out of the spend total.
- Migration arrows only appear for explicit "I switched from X" statements; silence is not a migration.

## Accuracy

`data/eval/gold_v1.jsonl` holds 40 hand-labelled comments, stratified by length and reply depth. `make eval` compares the primary model's extraction field by field and writes `data/eval/report.json`:

- classification accuracy for `answers_questions`
- precision, recall, and F1 per node field
- the mismatches themselves, with expected and predicted node ids

The report is rendered on the dashboard's Method tab. Low accuracy on a field is stated there rather than hidden.

## What this cannot tell you

- Whether someone uses a tool well, or at all beyond mentioning it.
- How much of their work is AI-assisted.
- Anything about people who did not comment, which is most of HN.
- Anything about the thread after the snapshot time; the thread is live.
