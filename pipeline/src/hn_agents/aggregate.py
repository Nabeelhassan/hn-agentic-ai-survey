from __future__ import annotations

from collections import Counter, defaultdict

from .taxonomy import load_taxonomy
from .util import read_json, read_jsonl, snapshot_paths, utc_now, write_json

HN_ITEM = "https://news.ycombinator.com/item?id={}"


def _labels(taxonomy: dict) -> dict[str, str]:
    labels = {"unstated": "Unstated"}
    for node in taxonomy.get("nodes", []):
        labels[node["id"]] = node.get("label", node["id"])
    return labels


def _category_map(taxonomy: dict) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for node in taxonomy.get("nodes", []):
        categories = node.get("categories") or ([node["category"]] if node.get("category") else [])
        mapping[node["id"]] = set(categories)
    return mapping


def _row(node: str, authors: set[str], comment_ids: set[str], denominator: int, labels: dict) -> dict:
    count = len(authors)
    return {
        "node": node,
        "label": labels.get(node, node.replace("other:", "")),
        "count": count,
        "pct": round(100 * count / denominator, 1) if denominator else None,
        "n_denominator": denominator,
        "comment_ids": sorted(comment_ids),
    }


def _breakdown(
    node_authors: dict[str, set[str]],
    node_comments: dict[str, set[str]],
    denominator: int,
    labels: dict,
    *,
    include_unstated: bool = True,
) -> list[dict]:
    rows = [
        _row(node, authors, node_comments.get(node, set()), denominator, labels)
        for node, authors in node_authors.items()
    ]
    rows.sort(key=lambda r: (-r["count"], r["label"].lower()))
    if include_unstated:
        covered = set().union(*node_authors.values()) if node_authors else set()
        unstated = max(denominator - len(covered), 0)
        if unstated:
            rows.append(
                {
                    "node": "unstated",
                    "label": "Unstated",
                    "count": unstated,
                    "pct": round(100 * unstated / denominator, 1),
                    "n_denominator": denominator,
                    "comment_ids": [],
                }
            )
    return rows


def _collect(
    respondents: list[dict], field: str, node_of
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    node_authors: dict[str, set[str]] = defaultdict(set)
    node_comments: dict[str, set[str]] = defaultdict(set)
    for respondent in respondents:
        for item in respondent.get(field) or []:
            node = node_of(item)
            if not node:
                continue
            node_authors[node].add(respondent["author"])
            node_comments[node].update(item.get("comment_ids", []))
    return node_authors, node_comments


def aggregate_snapshot(snapshot_id: str) -> None:
    paths = snapshot_paths(snapshot_id)
    taxonomy = load_taxonomy()
    labels = _labels(taxonomy)
    respondents = [r for r in read_jsonl(paths["respondents"]) if r["has_setup"]]
    comments = read_jsonl(paths["comments"])
    extractions = read_jsonl(paths["extractions"])
    meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
    denominator = len(respondents)

    primary_model = "deepseek/deepseek-v4.1-flash"
    chosen: dict[str, dict] = {}
    for record in extractions:
        if record["model"] != primary_model:
            continue
        if record["comment_id"] not in chosen or record.get("status") == "ok":
            chosen[record["comment_id"]] = record
    answer_counts = Counter(record["answers_questions"] for record in chosen.values())
    answer_ids: dict[str, set[str]] = defaultdict(set)
    for comment_id, record in chosen.items():
        answer_ids[record["answers_questions"]].add(comment_id)
    second_hand = sum(1 for record in chosen.values() if record.get("second_hand"))

    aggregates = paths["aggregates"]
    aggregates.mkdir(parents=True, exist_ok=True)

    write_json(
        aggregates / "overview.json",
        {
            "snapshot_id": snapshot_id,
            "generated_at": utc_now().isoformat(),
            "story": read_json(paths["raw"] / "story.json") if (paths["raw"] / "story.json").exists() else None,
            "comments": len(comments),
            "comments_with_text": sum(1 for c in comments if c["text_md"]),
            "top_level_comments": sum(1 for c in comments if c["is_top_level"]),
            "commenters": len({c["author"] for c in comments if c["author"] != "[deleted]"}),
            "deleted": sum(1 for c in comments if c["deleted"]),
            "dead": sum(1 for c in comments if c["dead"]),
            "respondents": denominator,
            "second_hand_comments": second_hand,
            "answer_distribution": [
                {
                    "label": label,
                    "count": answer_counts.get(label, 0),
                    "pct": round(100 * answer_counts.get(label, 0) / max(sum(answer_counts.values()), 1), 1),
                    "n_denominator": sum(answer_counts.values()),
                    "comment_ids": sorted(answer_ids.get(label, set())),
                }
                for label in ("full", "partial", "none", "meta", "off_topic")
            ],
            "notes": [
                "Comment scores are not exposed by the HN API, so nothing is weighted by points.",
                "Comments are counted by HN account; one person with two accounts counts twice.",
            ],
        },
    )

    subs_authors, subs_comments = _collect(respondents, "subscriptions", lambda item: item["node"])
    with_subs = len({a for authors in subs_authors.values() for a in authors})
    write_json(
        aggregates / "subscriptions.json",
        {
            "n_denominator": denominator,
            "n_with_subscription": with_subs,
            "providers": _breakdown(subs_authors, subs_comments, denominator, labels),
            "tiers": _tier_breakdown(respondents, labels),
            "multi_subscription": _multi_breakdown(respondents, denominator),
            "spend": _spend_breakdown(respondents),
        },
    )

    outside_authors, outside_comments = _collect(respondents, "outside_models", lambda item: item["node"])
    category_of = _category_map(taxonomy)
    source_authors = {n: a for n, a in outside_authors.items() if "model-source" in category_of.get(n, set())}
    source_comments = {n: c for n, c in outside_comments.items() if n in source_authors}
    model_authors = {n: a for n, a in outside_authors.items() if "model" in category_of.get(n, set())}
    model_comments = {n: c for n, c in outside_comments.items() if n in model_authors}
    access_rows = _access_breakdown(respondents)
    write_json(
        aggregates / "models.json",
        {
            "n_denominator": denominator,
            "sources": _breakdown(source_authors, source_comments, denominator, labels),
            "models": _breakdown(model_authors, model_comments, denominator, labels, include_unstated=False),
            "access": access_rows,
            "local_share": next((row for row in access_rows if row["node"] == "local"), None),
        },
    )

    harness_authors, harness_comments = _collect(respondents, "harnesses", lambda item: item["node"])
    primary_authors: dict[str, set[str]] = defaultdict(set)
    primary_comments: dict[str, set[str]] = defaultdict(set)
    migrations = []
    reasons: list[dict] = []
    for respondent in respondents:
        for harness in respondent.get("harnesses") or []:
            if harness.get("role") == "primary":
                primary_authors[harness["node"]].add(respondent["author"])
                primary_comments[harness["node"]].update(harness.get("comment_ids", []))
            if harness.get("switched_from"):
                migrations.append(
                    {
                        "from": harness["switched_from"],
                        "from_label": labels.get(harness["switched_from"], harness["switched_from"]),
                        "to": harness["node"],
                        "to_label": labels.get(harness["node"], harness["node"]),
                        "author": respondent["author"],
                        "comment_ids": harness.get("comment_ids", []),
                    }
                )
            if harness.get("switch_reason"):
                reasons.append(
                    {
                        "node": harness["node"],
                        "reason": harness["switch_reason"],
                        "author": respondent["author"],
                        "comment_ids": harness.get("comment_ids", []),
                    }
                )
    migration_edges, suppressed_edges = _migration_edges(migrations, labels)
    migration_pairs: dict[tuple[str, str], dict] = {}
    for migration in migrations:
        key = (migration["from"], migration["to"])
        pair = migration_pairs.setdefault(
            key,
            {
                "from": migration["from"],
                "from_label": migration["from_label"],
                "to": migration["to"],
                "to_label": migration["to_label"],
                "count": 0,
                "comment_ids": [],
                "authors": [],
            },
        )
        pair["count"] += 1
        pair["authors"].append(migration["author"])
        for comment_id in migration["comment_ids"]:
            if comment_id not in pair["comment_ids"]:
                pair["comment_ids"].append(comment_id)
    write_json(
        aggregates / "harnesses.json",
        {
            "n_denominator": denominator,
            "adoption": _breakdown(harness_authors, harness_comments, denominator, labels),
            "primary": _breakdown(primary_authors, primary_comments, denominator, labels, include_unstated=False),
            "migrations": migrations,
            "migration_edges": migration_edges,
            "migration_pairs": sorted(
                migration_pairs.values(), key=lambda pair: (-pair["count"], pair["from_label"], pair["to_label"])
            ),
            "suppressed_migration_edges": suppressed_edges,
            "switch_reasons": reasons,
        },
    )

    orch_authors, orch_comments = _collect(respondents, "orchestration", lambda item: item["node"])
    platform_authors, platform_comments = _collect(respondents, "platforms", lambda item: item["node"])
    use_cases: dict[str, set[str]] = defaultdict(set)
    for respondent in respondents:
        for platform in respondent.get("platforms") or []:
            for use_case in platform.get("use_cases") or []:
                use_cases[platform["node"]].add(use_case.lower().strip())
    write_json(
        aggregates / "orchestration.json",
        {
            "n_denominator": denominator,
            "orchestration": _breakdown(orch_authors, orch_comments, denominator, labels),
            "platforms": _breakdown(platform_authors, platform_comments, denominator, labels),
            "platform_use_cases": {
                node: sorted(cases) for node, cases in sorted(use_cases.items(), key=lambda kv: -len(kv[1]))
            },
            "orchestration_users": sorted({a for authors in orch_authors.values() for a in authors}),
        },
    )

    theme_counts: dict[str, set[str]] = defaultdict(set)
    theme_comments: dict[str, set[str]] = defaultdict(set)
    theme_variants: dict[str, set[str]] = defaultdict(set)
    theme_map_path = paths["root"] / "theme-map.json"
    mapping = read_json(theme_map_path).get("mapping", {}) if theme_map_path.exists() else {}
    for respondent in respondents:
        for theme, sources in (respondent.get("theme_sources") or {}).items():
            cleaned = " ".join(str(theme).split()).strip().lower()
            label = mapping.get(cleaned, cleaned)
            theme_counts[label].add(respondent["author"])
            theme_comments[label].update(sources)
            theme_variants[label].add(cleaned)
    write_json(
        aggregates / "themes.json",
        {
            "n_denominator": denominator,
            "clustered": bool(mapping),
            "themes": sorted(
                (
                    {
                        "theme": theme,
                        "count": len(authors),
                        "variants": len(theme_variants[theme]),
                        "n_denominator": denominator,
                        "comment_ids": sorted(theme_comments[theme]),
                    }
                    for theme, authors in theme_counts.items()
                    if len(authors) >= 3
                ),
                key=lambda row: -row["count"],
            )[:30],
        },
    )

    write_json(aggregates / "cooccurrence.json", _cooccurrence(respondents, labels))

    rows = []
    for respondent in respondents:
        rows.append(
            {
                "author": respondent["author"],
                "n_comments": respondent["n_comments"],
                "answers": respondent["answers"],
                "subscriptions": [
                    {
                        "node": item["node"],
                        "label": labels.get(item["node"], item["node"].replace("other:", "")),
                        "tier_raw": item.get("tier_raw"),
                        "comment_ids": item.get("comment_ids", []),
                    }
                    for item in respondent.get("subscriptions") or []
                ],
                "outside": [
                    {"node": item["node"], "label": labels.get(item["node"], item["node"].replace("other:", "")), "access": item.get("access")}
                    for item in respondent.get("outside_models") or []
                ],
                "harnesses": [
                    {"node": item["node"], "label": labels.get(item["node"], item["node"].replace("other:", "")), "role": item.get("role")}
                    for item in respondent.get("harnesses") or []
                ],
                "orchestration": [
                    {"node": item["node"], "label": labels.get(item["node"], item["node"].replace("other:", ""))}
                    for item in respondent.get("orchestration") or []
                ],
                "platforms": [
                    {"node": item["node"], "label": labels.get(item["node"], item["node"].replace("other:", ""))}
                    for item in respondent.get("platforms") or []
                ],
                "spend_monthly_usd": (respondent.get("spend_monthly_usd") or {}).get("value"),
                "comment_ids": respondent["comment_ids"],
                "first_comment_url": HN_ITEM.format(respondent["comment_ids"][0]) if respondent["comment_ids"] else None,
                "has_conflict": bool(respondent.get("conflicts")),
            }
        )
    write_json(aggregates / "explorer.json", {"rows": rows, "n_denominator": denominator})

    eval_path = paths["root"] / "eval.json"
    write_json(
        aggregates / "methodology.json",
        {
            "snapshot_id": snapshot_id,
            "generated_at": utc_now().isoformat(),
            "story_url": "https://news.ycombinator.com/item?id=50366117",
            "taxonomy": {"version": taxonomy.get("version"), "nodes": taxonomy.get("nodes", [])},
            "extraction": meta.get("extraction"),
            "normalize": meta.get("normalize"),
            "merge": meta.get("merge"),
            "eval": read_json(eval_path) if eval_path.exists() else None,
            "conventions": [
                "Counts are unique HN accounts, not comments.",
                "Second-hand reports are excluded from respondent counts.",
                "Unstated is always a visible row, never dropped.",
                "Below n = 10 the dashboard shows counts, not percentages.",
            ],
        },
    )
    print(f"aggregated {denominator} respondents into {len(list(aggregates.glob('*.json')))} files")


def _migration_edges(migrations: list[dict], labels: dict) -> tuple[list[dict], int]:
    counts: Counter[tuple[str, str]] = Counter(
        (migration["from"], migration["to"]) for migration in migrations
    )

    for left, right in list(counts):
        if (right, left) in counts and left < right:
            net = counts[(left, right)] - counts[(right, left)]
            del counts[(right, left)]
            if net > 0:
                counts[(left, right)] = net
            else:
                del counts[(left, right)]

    edges = [(left, right, count) for (left, right), count in counts.items()]
    suppressed = 0

    def acyclic(candidate: list[tuple[str, str, int]]) -> bool:
        nodes = {node for left, right, _ in candidate for node in (left, right)}
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = Counter({node: 0 for node in nodes})
        for left, right, _ in candidate:
            adjacency[left].append(right)
            indegree[right] += 1
        queue = [node for node in nodes if indegree[node] == 0]
        visited = 0
        while queue:
            node = queue.pop()
            visited += 1
            for neighbour in adjacency[node]:
                indegree[neighbour] -= 1
                if indegree[neighbour] == 0:
                    queue.append(neighbour)
        return visited == len(nodes)

    while not acyclic(edges):
        weakest = sorted(edges, key=lambda edge: (edge[2], edge[0], edge[1]))[0]
        edges = [edge for edge in edges if edge != weakest]
        suppressed += weakest[2]

    return (
        [
            {
                "from": left,
                "from_label": labels.get(left, left),
                "to": right,
                "to_label": labels.get(right, right),
                "count": count,
            }
            for left, right, count in sorted(edges, key=lambda edge: -edge[2])
        ],
        suppressed,
    )


def _tier_breakdown(respondents: list[dict], labels: dict) -> list[dict]:
    authors: dict[str, set[str]] = defaultdict(set)
    comments: dict[str, set[str]] = defaultdict(set)
    for respondent in respondents:
        for item in respondent.get("subscriptions") or []:
            tier = (item.get("tier_raw") or "unspecified").strip()
            key = f"{item['node']}|{tier}"
            authors[key].add(respondent["author"])
            comments[key].update(item.get("comment_ids", []))
    rows = []
    for key, value in authors.items():
        node, tier = key.split("|", 1)
        rows.append(
            {
                "node": node,
                "label": labels.get(node, node),
                "tier_raw": tier,
                "count": len(value),
                "n_denominator": len(respondents),
                "comment_ids": sorted(comments[key]),
            }
        )
    return sorted(rows, key=lambda row: (-row["count"], row["label"], row["tier_raw"]))


def _multi_breakdown(respondents: list[dict], denominator: int) -> list[dict]:
    counts = Counter()
    comment_ids: dict[str, set[str]] = defaultdict(set)
    for respondent in respondents:
        multi = respondent.get("multi_subscription")
        label = "unstated" if not multi or multi.get("value") is None else str(bool(multi["value"])).lower()
        counts[label] += 1
        if multi:
            comment_ids[label].update(multi.get("comment_ids", []))
    order = ["true", "false", "unstated"]
    return [
        {
            "node": label,
            "label": {"true": "Two or more", "false": "One", "unstated": "Unstated"}[label],
            "count": counts.get(label, 0),
            "pct": round(100 * counts.get(label, 0) / denominator, 1) if denominator else None,
            "n_denominator": denominator,
            "comment_ids": sorted(comment_ids.get(label, set())),
        }
        for label in order
    ]


def _spend_breakdown(respondents: list[dict]) -> dict:
    values = [
        (r["author"], r["spend_monthly_usd"]["value"], r["spend_monthly_usd"]["comment_ids"])
        for r in respondents
        if r.get("spend_monthly_usd") and r["spend_monthly_usd"].get("value") is not None
    ]
    buckets = [(0, 20), (20, 50), (50, 100), (100, 200), (200, 500), (500, None)]
    rows = []
    for low, high in buckets:
        members = [
            (author, value, ids)
            for author, value, ids in values
            if value >= low and (high is None or value < high)
        ]
        label = f"${low}+" if high is None else f"${low}–{high}"
        rows.append(
            {
                "label": label,
                "count": len(members),
                "n_denominator": len(values),
                "comment_ids": sorted({cid for _, _, ids in members for cid in ids}),
            }
        )
    return {
        "stated": len(values),
        "values": [
            {"author": author, "usd": value, "comment_ids": ids} for author, value, ids in sorted(values, key=lambda v: -v[1])
        ],
        "buckets": rows,
    }


def _access_breakdown(respondents: list[dict]) -> list[dict]:
    authors: dict[str, set[str]] = defaultdict(set)
    comments: dict[str, set[str]] = defaultdict(set)
    for respondent in respondents:
        for item in respondent.get("outside_models") or []:
            access = item.get("access", "other")
            authors[access].add(respondent["author"])
            comments[access].update(item.get("comment_ids", []))
    denominator = len(respondents)
    rows = [
        {
            "node": access,
            "label": access,
            "count": len(value),
            "pct": round(100 * len(value) / denominator, 1) if denominator else None,
            "n_denominator": denominator,
            "comment_ids": sorted(comments[access]),
        }
        for access, value in sorted(authors.items(), key=lambda kv: -len(kv[1]))
    ]
    covered = {author for value in authors.values() for author in value}
    if denominator - len(covered) > 0:
        rows.append(
            {
                "node": "unstated",
                "label": "Unstated",
                "count": denominator - len(covered),
                "pct": round(100 * (denominator - len(covered)) / denominator, 1),
                "n_denominator": denominator,
                "comment_ids": [],
            }
        )
    return rows


def _cooccurrence(respondents: list[dict], labels: dict) -> dict:
    pairs: Counter[tuple[str, str]] = Counter()
    pair_comments: dict[tuple[str, str], set[str]] = defaultdict(set)
    totals: Counter[str] = Counter()
    for respondent in respondents:
        nodes = sorted(
            {
                item["node"]
                for field in ("subscriptions", "harnesses", "platforms", "outside_models")
                for item in respondent.get(field) or []
            }
        )
        for node in nodes:
            totals[node] += 1
        for i, left in enumerate(nodes):
            for right in nodes[i + 1 :]:
                pairs[(left, right)] += 1
                pair_comments[(left, right)].update(respondent["comment_ids"][:1])
    edges = [
        {
            "a": left,
            "a_label": labels.get(left, left),
            "b": right,
            "b_label": labels.get(right, right),
            "count": count,
            "comment_ids": sorted(pair_comments[(left, right)]),
        }
        for (left, right), count in pairs.most_common(40)
        if count >= 2
    ]
    return {
        "nodes": [
            {"node": node, "label": labels.get(node, node), "count": count}
            for node, count in totals.most_common(40)
        ],
        "edges": edges,
    }
