from __future__ import annotations

from hn_agents.catalog import load_catalog
from hn_agents.pricing import aggregate_plans, resolve_provider
from hn_agents.taxonomy import load_taxonomy

CATALOG = load_catalog()
TAXONOMY = load_taxonomy()


def _respondent(author: str, subscriptions: list[tuple[str, str, list[str]]]) -> dict:
    return {
        "author": author,
        "subscriptions": [
            {"node": node, "tier_raw": raw, "comment_ids": comment_ids}
            for node, raw, comment_ids in subscriptions
        ],
    }


def _plans(section: dict, provider_id: str) -> dict[str, dict]:
    provider = next(p for p in section["providers"] if p["provider"] == provider_id)
    return {plan["plan_id"]: plan for plan in provider["plans"]}


def test_plan_aggregate_counts_unique_respondents_and_keeps_free_rows():
    respondents = [
        _respondent(
            "a",
            [
                ("anthropic", "$20/mo", ["1"]),
                ("anthropic", "Max 20x", ["2"]),
                ("openai", "unspecified", ["3"]),
            ],
        ),
        _respondent("b", [("anthropic", "$20", ["4"])]),
    ]
    section = aggregate_plans(respondents, CATALOG, TAXONOMY, denominator=413)
    anthropic = _plans(section, "anthropic")

    assert anthropic["free"]["count"] == 0
    assert anthropic["free"]["price_monthly"] == 0
    assert anthropic["pro"]["count"] == 2
    assert anthropic["pro"]["comment_ids"] == ["1", "4"]
    assert anthropic["ultra"]["count"] == 1
    assert anthropic["pro"]["pct_of_provider"] == 100.0

    assert section["matching"]["matched_assignments"] == 3
    assert section["matching"]["unmatched_assignments"] == 1
    assert any(row["tier_raw"] == "unspecified" for row in section["unmatched_tiers"])


def test_ambiguous_and_unknown_stay_unmatched():
    respondents = [
        _respondent("a", [("kiro", "$20.00", ["1"])]),
        _respondent("b", [("other:charm-hyper", "$10", ["2"])]),
    ]
    section = aggregate_plans(respondents, CATALOG, TAXONOMY, denominator=413)
    methods = {row["method"] for row in section["unmatched_tiers"]}
    assert "ambiguous_price" in methods
    assert "unknown_provider" in methods
    assert section["matching"]["matched_assignments"] == 0


def test_provider_resolution_handles_other_prefix_and_taxonomy_aliases():
    assert resolve_provider("anthropic", TAXONOMY, CATALOG) == "anthropic"
    assert resolve_provider("other:opencode-go", TAXONOMY, CATALOG) == "opencode"
    assert resolve_provider("other:charm-hyper", TAXONOMY, CATALOG) is None
