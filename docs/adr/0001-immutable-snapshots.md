# Snapshots are immutable

Every fetch writes `data/raw/<snapshot_id>/` and `data/snapshots/<snapshot_id>/` and never
touches an earlier one. The thread is live and gets edited, so reproducing a number means
re-running the pipeline over a frozen raw payload, not refetching HN. Derived files carry the
extraction model, prompt hash, and taxonomy version because "usage changed" and "our prompt
changed" look identical in an aggregate otherwise.
