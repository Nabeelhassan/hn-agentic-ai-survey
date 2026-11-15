from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .cmdrun import estimate_cost, parse_json_object, run_cmd, token_counts
from .models import ExtractionBatch
from .taxonomy import load_taxonomy, render_for_prompt
from .util import PROMPT_DIR, read_json, read_jsonl, sha256_text, snapshot_paths, utc_now, write_json, write_jsonl

PROMPT_FILE = PROMPT_DIR / "extract_v1.md"


def prompt_hash(taxonomy: dict) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    return sha256_text(template + render_for_prompt(taxonomy))


def comment_blocks(comments: list[dict], limit_chars: int = 6000) -> str:
    blocks = []
    for comment in comments:
        text = comment["text_md"][:limit_chars]
        blocks.append(
            f'<comment id="{comment["comment_id"]}" author="{comment["author"]}" depth="{comment["depth"]}">\n{text}\n</comment>'
        )
    return "\n\n".join(blocks)


def build_prompt(comments: list[dict], taxonomy: dict) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    filled = template.replace("{{TAXONOMY}}", render_for_prompt(taxonomy))
    return filled.replace("{{COMMENTS}}", comment_blocks(comments))


@dataclass
class BatchOutcome:
    records: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    duration_ms: int = 0
    error: str | None = None


async def _run_batch(
    comments: list[dict],
    model: str,
    taxonomy: dict,
    semaphore: asyncio.Semaphore,
    run_id: str,
    phash: str,
) -> BatchOutcome:
    prompt = build_prompt(comments, taxonomy)
    expected = [c["comment_id"] for c in comments]
    by_id = {c["comment_id"]: c for c in comments}
    last_error: str | None = None

    for attempt in range(2):
        correction = ""
        if attempt == 1 and last_error:
            correction = (
                "\n\nYour previous reply was not valid JSON for the required schema "
                f"({last_error}). Reply again with only the corrected JSON object."
            )
        async with semaphore:
            try:
                run = await run_cmd(prompt + correction, model, max_turns=2)
            except RuntimeError as error:
                last_error = str(error)
                continue

        try:
            payload = parse_json_object(run.final_text)
            batch = ExtractionBatch.model_validate(payload)
        except Exception as error:  # noqa: BLE001 - any parse/validation failure triggers one repair
            last_error = f"{type(error).__name__}: {error}"
            continue

        parsed = {record.comment_id: record for record in batch.results}
        records: list[dict] = []
        for comment_id in expected:
            comment = by_id[comment_id]
            record = parsed.get(comment_id)
            base = {
                "comment_id": comment_id,
                "snapshot_id": comment["snapshot_id"],
                "author": comment["author"],
                "model": model,
                "run_id": run_id,
                "prompt_hash": phash,
                "taxonomy_version": taxonomy.get("version"),
                "schema_version": 1,
                "content_hash": comment["content_hash"],
                "extracted_at": utc_now().isoformat(),
                "status": "ok" if record else "missing",
            }
            if record is None:
                base.update(
                    {
                        "answers_questions": "none",
                        "q1_subscriptions": [],
                        "q1_multi_subscription": None,
                        "q2_outside": [],
                        "q3_harnesses": [],
                        "q4_orchestration": [],
                        "q5_platforms": [],
                        "spend_monthly_usd": None,
                        "second_hand": False,
                        "evidence": [],
                        "themes": [],
                        "confidence": 0.0,
                    }
                )
            else:
                base.update(record.model_dump())
            records.append(base)
        return BatchOutcome(records=records, usage=run.usage, duration_ms=run.duration_ms)

    return BatchOutcome(error=last_error or "unknown failure")


def _signature(record: dict) -> tuple:
    return (
        record.get("answers_questions"),
        tuple(sorted(item.get("node") for item in record.get("q1_subscriptions", []))),
        tuple(sorted(item.get("node") for item in record.get("q3_harnesses", []))),
        tuple(sorted(item.get("node") for item in record.get("q5_platforms", []))),
        bool(record.get("second_hand")),
    )


def _has_setup(record: dict) -> bool:
    return bool(
        record.get("q1_subscriptions") or record.get("q3_harnesses") or record.get("q2_outside")
        or record.get("q4_orchestration") or record.get("q5_platforms")
    )


def extract_snapshot(
    snapshot_id: str,
    *,
    model: str,
    second_model: str,
    passes: str = "both",
    limit: int | None = None,
    batch_size: int = 20,
    concurrency: int = 4,
    taxonomy_version: str = "v1",
) -> None:
    taxonomy = load_taxonomy(taxonomy_version)
    phash = prompt_hash(taxonomy)
    paths = snapshot_paths(snapshot_id)
    comments = [c for c in read_jsonl(paths["comments"]) if c["text_md"]]
    if limit:
        comments = comments[:limit]

    models = [model] if passes == "first" else [second_model] if passes == "second" else [model, second_model]

    existing = read_jsonl(paths["extractions"])
    done = {
        (r["comment_id"], r["model"], r.get("prompt_hash"), r.get("content_hash"))
        for r in existing
        if r.get("status") == "ok"
    }

    runs: list[dict] = []
    records_by_key = {(r["comment_id"], r["model"], r.get("prompt_hash"), r.get("content_hash")): r for r in existing}

    for current_model in models:
        pending = [
            c for c in comments if (c["comment_id"], current_model, phash, c["content_hash"]) not in done
        ]
        batches = [pending[i : i + batch_size] for i in range(0, len(pending), batch_size)]
        run_id = f"{snapshot_id}:{current_model}:{phash[:8]}"
        print(f"{current_model}: {len(pending)} comments in {len(batches)} batches (run {run_id})")
        if not batches:
            continue

        started = utc_now()

        async def run_all() -> list[BatchOutcome]:
            semaphore = asyncio.Semaphore(concurrency)
            return await asyncio.gather(
                *(
                    _run_batch(batch, current_model, taxonomy, semaphore, run_id, phash)
                    for batch in batches
                )
            )

        outcomes = asyncio.run(run_all())
        usage_totals = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
        failed = 0
        written = 0
        for outcome in outcomes:
            if outcome.error:
                failed += 1
                print(f"  batch failed: {outcome.error}")
                continue
            for record in outcome.records:
                records_by_key[(record["comment_id"], record["model"], record["prompt_hash"], record["content_hash"])] = record
                written += 1
            input_tokens, output_tokens, cache_read = token_counts(outcome.usage)
            usage_totals["input_tokens"] += input_tokens
            usage_totals["output_tokens"] += output_tokens
            usage_totals["cache_read_input_tokens"] += cache_read

        cost = 0.0
        for outcome in outcomes:
            if not outcome.error:
                cost += estimate_cost(outcome.usage, current_model)

        runs.append(
            {
                "model": current_model,
                "run_id": run_id,
                "prompt_hash": phash,
                "taxonomy_version": taxonomy.get("version"),
                "started_at": started.isoformat(),
                "finished_at": utc_now().isoformat(),
                "batches": len(batches),
                "batch_failures": failed,
                "records_written": written,
                "usage": usage_totals,
                "cost_usd": round(cost, 4),
            }
        )
        print(f"  wrote {written} records, {failed} failed batches, ~${cost:.4f}")

    records = sorted(records_by_key.values(), key=lambda r: (r["comment_id"], r["model"]))
    write_jsonl(paths["extractions"], records)

    by_comment: dict[str, dict[str, dict]] = {}
    for record in records:
        by_comment.setdefault(record["comment_id"], {})[record["model"]] = record

    review = []
    for comment_id, per_model in by_comment.items():
        flagged = []
        if len(per_model) == 2:
            signatures = [_signature(r) for r in per_model.values()]
            if signatures[0] != signatures[1] and any(_has_setup(r) for r in per_model.values()):
                flagged.append("model_disagreement")
        if any(r.get("confidence", 1.0) < 0.6 for r in per_model.values()):
            flagged.append("low_confidence")
        if any(r.get("status") != "ok" for r in per_model.values()):
            flagged.append("extraction_missing")
        if flagged:
            review.append(
                {
                    "comment_id": comment_id,
                    "reasons": flagged,
                    "models": {
                        model: {
                            "answers_questions": record.get("answers_questions"),
                            "confidence": record.get("confidence"),
                            "signature": list(_signature(record)),
                        }
                        for model, record in per_model.items()
                    },
                }
            )

    write_jsonl(paths["review"], review)
    meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
    meta.setdefault("snapshot_id", snapshot_id)
    meta["extraction"] = {
        "schema_version": 1,
        "taxonomy_version": taxonomy.get("version"),
        "runs": runs,
        "records": len(records),
        "comments_extracted": len({r["comment_id"] for r in records}),
        "review_items": len(review),
        "total_cost_usd": round(sum(run["cost_usd"] for run in runs), 4),
    }
    write_json(paths["meta"], meta)
    print(f"extraction done: {len(records)} records, {len(review)} review items")
