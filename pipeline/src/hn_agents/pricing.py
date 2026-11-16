from __future__ import annotations

from collections import Counter, defaultdict

from .catalog import match_plan
from .taxonomy import alias_index

def _key(value: str) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


def resolve_provider(node: str, taxonomy: dict, catalog: dict) -> str | None:
    provider_ids = {provider["id"] for provider in catalog["providers"]}
    by_key = {_key(provider_id): provider_id for provider_id in provider_ids}
    key = _key(str(node).removeprefix("other:"))
    if key in by_key:
        return by_key[key]
    aliases = {_key(alias): node_id for alias, node_id in alias_index(taxonomy, "subscription").items()}
    resolved = aliases.get(key)
    if resolved in provider_ids:
        return resolved
    return None


def aggregate_plans(
    respondents: list[dict],
    catalog: dict,
    taxonomy: dict,
    denominator: int,
) -> dict:
    observed: dict[tuple[str, str], dict] = {}
    unmatched: dict[tuple[str, str], dict] = {}
    provider_authors: dict[str, set[str]] = defaultdict(set)
    methods: Counter[str] = Counter()
    matched_authors: set[str] = set()
    matched_assignments = 0
    unmatched_assignments = 0

    for respondent in respondents:
        author = respondent["author"]
        for item in respondent.get("subscriptions") or []:
            raw = " ".join(str(item.get("tier_raw") or "unspecified").split()).strip() or "unspecified"
            provider_id = resolve_provider(item["node"], taxonomy, catalog)
            if provider_id is None:
                bucket = unmatched.setdefault(
                    ("unknown-provider", str(item["node"])),
                    {
                        "provider": None,
                        "provider_label": str(item["node"]).removeprefix("other:"),
                        "tier_raw": raw,
                        "authors": set(),
                        "comment_ids": set(),
                        "method": "unknown_provider",
                    },
                )
                bucket["authors"].add(author)
                bucket["comment_ids"].update(item.get("comment_ids", []))
                continue

            provider_authors[provider_id].add(author)
            match = match_plan(provider_id, raw, catalog)
            if match.plan_id is None:
                bucket = unmatched.setdefault(
                    (provider_id, raw),
                    {
                        "provider": provider_id,
                        "provider_label": provider_id,
                        "tier_raw": raw,
                        "authors": set(),
                        "comment_ids": set(),
                        "method": match.method,
                    },
                )
                bucket["authors"].add(author)
                bucket["comment_ids"].update(item.get("comment_ids", []))
                methods[match.method] += 1
                unmatched_assignments += 1
                continue

            key = (provider_id, match.plan_id)
            bucket = observed.setdefault(
                key,
                {
                    "authors": set(),
                    "comment_ids": set(),
                    "methods": Counter(),
                    "variants": Counter(),
                },
            )
            bucket["authors"].add(author)
            bucket["comment_ids"].update(item.get("comment_ids", []))
            bucket["methods"][match.method] += 1
            bucket["variants"][raw] += 1
            methods[match.method] += 1
            matched_assignments += 1
            matched_authors.add(author)

    providers = []
    plans_seen = 0
    plans_priced = 0
    for provider in catalog["providers"]:
        provider_id = provider["id"]
        provider_denominator = len(provider_authors.get(provider_id, set()))
        rows = []
        for plan in provider.get("plans", []):
            plans_seen += 1
            bucket = observed.get((provider_id, plan["id"]))
            count = len(bucket["authors"]) if bucket else 0
            if plan.get("price_monthly") is not None:
                plans_priced += 1
            rows.append(
                {
                    "provider": provider_id,
                    "provider_label": provider["label"],
                    "plan_id": plan["id"],
                    "plan_label": plan["label"],
                    "audience": plan.get("audience", "individual"),
                    "price_monthly": plan.get("price_monthly"),
                    "price_annual": plan.get("price_annual"),
                    "annual_monthly": plan.get("annual_monthly"),
                    "list_price_monthly": plan.get("list_price_monthly"),
                    "currency": provider.get("currency", "USD"),
                    "count": count,
                    "pct_of_provider": round(100 * count / provider_denominator, 1) if provider_denominator else None,
                    "n_provider_denominator": provider_denominator,
                    "pct_of_respondents": round(100 * count / denominator, 1) if denominator else None,
                    "n_denominator": denominator,
                    "match_methods": dict(bucket["methods"]) if bucket else {},
                    "raw_variants": (
                        [{"tier_raw": raw, "count": count} for raw, count in bucket["variants"].most_common()]
                        if bucket
                        else []
                    ),
                    "comment_ids": sorted(bucket["comment_ids"]) if bucket else [],
                    "note": plan.get("note"),
                }
            )
        providers.append(
            {
                "provider": provider_id,
                "provider_label": provider["label"],
                "verification": provider.get("verification", "unknown"),
                "currency": provider.get("currency", "USD"),
                "source_url": provider.get("source_url"),
                "retrieved_at": catalog.get("retrieved_at"),
                "notes": provider.get("notes"),
                "n_provider_denominator": provider_denominator,
                "plans": rows,
            }
        )

    unmatched_rows = sorted(
        (
            {
                "provider": bucket["provider"],
                "provider_label": bucket["provider_label"],
                "tier_raw": bucket["tier_raw"],
                "count": len(bucket["authors"]),
                "n_provider_denominator": len(provider_authors.get(bucket["provider"], set())),
                "comment_ids": sorted(bucket["comment_ids"]),
                "method": bucket["method"],
            }
            for bucket in unmatched.values()
        ),
        key=lambda row: (-row["count"], row["provider_label"], row["tier_raw"]),
    )

    return {
        "catalog_version": catalog.get("version"),
        "retrieved_at": catalog.get("retrieved_at"),
        "providers": providers,
        "unmatched_tiers": unmatched_rows,
        "matching": {
            "assignments": matched_assignments + unmatched_assignments,
            "matched_assignments": matched_assignments,
            "unmatched_assignments": unmatched_assignments,
            "matched_respondents": len(matched_authors),
            "unmatched_tiers": len(unmatched_rows),
            "methods": dict(methods),
            "plans_in_catalog": plans_seen,
            "plans_with_price": plans_priced,
        },
    }
