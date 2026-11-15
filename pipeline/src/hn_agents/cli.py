from __future__ import annotations

import argparse
import asyncio

from .util import resolve_snapshot


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="hn_agents")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="freeze Algolia + Firebase payloads for a new snapshot")
    fetch.add_argument("--snapshot-id")

    normalize = sub.add_parser("normalize", help="turn raw payloads into comments.jsonl")
    normalize.add_argument("--snapshot")

    harvest = sub.add_parser("taxonomy-harvest", help="collect tool-name candidates from comments")
    harvest.add_argument("--snapshot")
    harvest.add_argument("--model", default="z-ai/glm-5.3-flash")

    extract = sub.add_parser("extract", help="structured extraction per comment, two models")
    extract.add_argument("--snapshot")
    extract.add_argument("--model", default="z-ai/glm-5.3-flash")
    extract.add_argument("--second-model", default="deepseek/deepseek-v4.1-flash")
    extract.add_argument("--passes", choices=["both", "first", "second"], default="both")
    extract.add_argument("--limit", type=int)
    extract.add_argument("--batch-size", type=int, default=20)
    extract.add_argument("--concurrency", type=int, default=4)

    merge = sub.add_parser("merge", help="merge comment extractions into respondent profiles")
    merge.add_argument("--snapshot")

    aggregate = sub.add_parser("aggregate", help="build dashboard aggregates from respondents")
    aggregate.add_argument("--snapshot")

    evaluate = sub.add_parser("eval", help="score extraction against the gold set")
    evaluate.add_argument("--snapshot")

    dashboard = sub.add_parser("dashboard-data", help="copy the latest aggregates into the dashboard")
    dashboard.add_argument("--snapshot")

    args = parser.parse_args(argv)

    if args.command == "fetch":
        from .fetch import fetch_snapshot

        asyncio.run(fetch_snapshot(snapshot_id=args.snapshot_id))
        return

    if args.command == "normalize":
        from .normalize import normalize_snapshot

        normalize_snapshot(resolve_snapshot(args.snapshot))
        return

    if args.command == "taxonomy-harvest":
        from .taxonomy import harvest

        harvest(resolve_snapshot(args.snapshot), model=args.model)
        return

    if args.command == "extract":
        from .extract import extract_snapshot

        extract_snapshot(
            resolve_snapshot(args.snapshot),
            model=args.model,
            second_model=args.second_model,
            passes=args.passes,
            limit=args.limit,
            batch_size=args.batch_size,
            concurrency=args.concurrency,
        )
        return

    if args.command == "merge":
        from .merge import merge_snapshot

        merge_snapshot(resolve_snapshot(args.snapshot))
        return

    if args.command == "aggregate":
        from .aggregate import aggregate_snapshot

        aggregate_snapshot(resolve_snapshot(args.snapshot))
        return

    if args.command == "eval":
        from .validate import evaluate_snapshot

        evaluate_snapshot(resolve_snapshot(args.snapshot))
        return

    if args.command == "dashboard-data":
        from .dashboard import export_dashboard_data

        export_dashboard_data(resolve_snapshot(args.snapshot))
        return


if __name__ == "__main__":
    main()
