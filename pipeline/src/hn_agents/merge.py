from __future__ import annotations

from .canonicalize import canonicalize_record
from .taxonomy import load_taxonomy
from .util import read_json, read_jsonl, snapshot_paths, utc_now, write_json, write_jsonl

PRIMARY_ORDER = ["deepseek/deepseek-v4.1-flash", "z-ai/glm-5.3-flash"]


def _rank_model(model: str) -> int:
    try:
        return PRIMARY_ORDER.index(model)
    except ValueError:
        return len(PRIMARY_ORDER)


def choose_record(records: list[dict]) -> dict | None:
    if not records:
        return None
    ok = [record for record in records if record.get("status") == "ok"]
    if not ok:
        return sorted(records, key=lambda r: _rank_model(r["model"]))[0]
    return sorted(ok, key=lambda r: (-(r.get("confidence") or 0), _rank_model(r["model"])))[0]


def _add_unique(target: list[dict], item: dict, key: str) -> None:
    if any(existing[key] == item[key] for existing in target):
        return
    target.append(item)


def merge_snapshot(snapshot_id: str) -> None:
    paths = snapshot_paths(snapshot_id)
    taxonomy = load_taxonomy()
    comments = {c["comment_id"]: c for c in read_jsonl(paths["comments"])}
    extractions = read_jsonl(paths["extractions"])
    by_comment: dict[str, list[dict]] = {}
    for record in extractions:
        by_comment.setdefault(record["comment_id"], []).append(record)

    by_author: dict[str, list[dict]] = {}
    for comment_id, records in by_comment.items():
        comment = comments.get(comment_id)
        if not comment or comment["author"] == "[deleted]" or not comment["text_md"]:
            continue
        chosen = choose_record(records)
        if chosen is None:
            continue
        merged = canonicalize_record(chosen, taxonomy)
        merged["_created_at_i"] = comment["created_at_i"] or 0
        merged["_depth"] = comment["depth"]
        by_author.setdefault(comment["author"], []).append(merged)

    respondents: list[dict] = []
    for author, records in sorted(by_author.items()):
        records.sort(key=lambda r: r["_created_at_i"])
        substantive = [
            record
            for record in records
            if record["answers_questions"] in ("full", "partial") and not record.get("second_hand")
        ]

        subscriptions: list[dict] = []
        outside: list[dict] = []
        harnesses: list[dict] = []
        orchestration: list[dict] = []
        platforms: list[dict] = []
        themes: list[str] = []
        theme_sources: dict[str, list[str]] = {}
        evidence: list[dict] = []
        conflicts: list[dict] = []
        multi_value: bool | None = None
        multi_ids: list[str] = []
        spend_value: float | None = None
        spend_ids: list[str] = []
        answers = {"full": 0, "partial": 0}

        for record in substantive:
            comment_id = record["comment_id"]
            answers[record["answers_questions"]] += 1

            for item in record.get("q1_subscriptions", []):
                match = next((s for s in subscriptions if s["node"] == item["node"]), None)
                if match is None:
                    subscriptions.append(
                        {
                            "node": item["node"],
                            "tier_raw": item.get("tier_raw"),
                            "count": item.get("count", 1),
                            "comment_ids": [comment_id],
                        }
                    )
                else:
                    match["comment_ids"].append(comment_id)
                    match["count"] = max(match["count"], item.get("count", 1))
                    if item.get("tier_raw") and match.get("tier_raw") and item["tier_raw"] != match["tier_raw"]:
                        conflicts.append(
                            {
                                "field": "subscriptions",
                                "node": item["node"],
                                "values": [match["tier_raw"], item["tier_raw"]],
                                "comment_ids": sorted({match["comment_ids"][0], comment_id}),
                            }
                        )
                    elif item.get("tier_raw") and not match.get("tier_raw"):
                        match["tier_raw"] = item["tier_raw"]

            if record.get("q1_multi_subscription") is not None:
                multi_value = record["q1_multi_subscription"]
                multi_ids.append(comment_id)

            for item in record.get("q2_outside", []):
                _add_unique(
                    outside,
                    {
                        "node": item["node"],
                        "access": item.get("access", "other"),
                        "purpose": item.get("purpose"),
                        "comment_ids": [comment_id],
                    },
                    "node",
                )

            for item in record.get("q3_harnesses", []):
                match = next((h for h in harnesses if h["node"] == item["node"]), None)
                if match is None:
                    harnesses.append(
                        {
                            "node": item["node"],
                            "role": item.get("role", "primary"),
                            "switched_from": item.get("switched_from"),
                            "switch_reason": item.get("switch_reason"),
                            "comment_ids": [comment_id],
                        }
                    )
                else:
                    match["comment_ids"].append(comment_id)
                    if item.get("role") == "primary":
                        match["role"] = "primary"
                    if item.get("switched_from") and not match.get("switched_from"):
                        match["switched_from"] = item["switched_from"]
                    if item.get("switch_reason") and not match.get("switch_reason"):
                        match["switch_reason"] = item["switch_reason"]

            for item in record.get("q4_orchestration", []):
                _add_unique(
                    orchestration,
                    {"node": item["node"], "description": item.get("description"), "comment_ids": [comment_id]},
                    "node",
                )

            for item in record.get("q5_platforms", []):
                existing = next((p for p in platforms if p["node"] == item["node"]), None)
                if existing is None:
                    platforms.append(
                        {
                            "node": item["node"],
                            "use_cases": list(item.get("use_cases", [])),
                            "comment_ids": [comment_id],
                        }
                    )
                else:
                    existing["comment_ids"].append(comment_id)
                    for use_case in item.get("use_cases", []):
                        if use_case not in existing["use_cases"]:
                            existing["use_cases"].append(use_case)

            for theme in record.get("themes", []):
                if theme not in themes:
                    themes.append(theme)
                theme_sources.setdefault(theme, [])
                if comment_id not in theme_sources[theme]:
                    theme_sources[theme].append(comment_id)

            for item in record.get("evidence", []):
                evidence.append(
                    {"field": item.get("field"), "quote": item.get("quote"), "comment_id": comment_id}
                )

            if record.get("spend_monthly_usd") is not None:
                spend_value = float(record["spend_monthly_usd"])
                spend_ids.append(comment_id)

        respondents.append(
            {
                "author": author,
                "comment_ids": [record["comment_id"] for record in records],
                "n_comments": len(records),
                "n_substantive": len(substantive),
                "answers": answers,
                "has_setup": bool(substantive),
                "second_hand_only": not substantive and any(record.get("second_hand") for record in records),
                "subscriptions": subscriptions,
                "multi_subscription": {"value": multi_value, "comment_ids": multi_ids} if multi_ids else None,
                "outside_models": outside,
                "harnesses": harnesses,
                "orchestration": orchestration,
                "platforms": platforms,
                "spend_monthly_usd": {"value": spend_value, "comment_ids": spend_ids} if spend_ids else None,
                "themes": themes,
                "theme_sources": theme_sources,
                "conflicts": conflicts,
                "evidence": evidence,
            }
        )

    written = write_jsonl(paths["respondents"], respondents)
    meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
    meta.setdefault("snapshot_id", snapshot_id)
    meta["merge"] = {
        "merged_at": utc_now().isoformat(),
        "respondents": written,
        "with_setup": sum(1 for r in respondents if r["has_setup"]),
        "second_hand_only": sum(1 for r in respondents if r["second_hand_only"]),
        "with_conflicts": sum(1 for r in respondents if r["conflicts"]),
        "commenters": len({c["author"] for c in comments.values() if c["author"] != "[deleted]"}),
    }
    write_json(paths["meta"], meta)
    print(f"merged {written} author profiles ({meta['merge']['with_setup']} with a stated setup)")
