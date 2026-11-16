from __future__ import annotations

from hn_agents.catalog import load_catalog, match_plan, normalize, parse_price

CATALOG = load_catalog()


def test_parse_price_formats():
    assert parse_price("$20/mo") == parse_price("$20 / month")
    bare = parse_price("$20")
    monthly = parse_price("$20/month")
    assert bare is not None and monthly is not None
    assert (bare.amount, bare.currency) == (monthly.amount, monthly.currency) == (20, "USD")
    assert bare.period == "unknown" and monthly.period == "month"
    assert parse_price("20$").amount == 20
    assert parse_price("Pro 20$/mo").currency == "USD"
    assert parse_price("180 euro / month").currency == "EUR"
    assert parse_price("£90/month").currency == "GBP"
    assert parse_price("Pro") is None


def test_anthropic_tier_variants_resolve():
    cases = {
        "$20": "pro",
        "$20/mo": "pro",
        "$20/month": "pro",
        "20$": "pro",
        "Pro": "pro",
        "pro": "pro",
        "Claude Pro": "pro",
        "Pro ($20/mo)": "pro",
        "$100": "max",
        "Max 5x": "max",
        "Max ($100)": "max",
        "Ultra (aka Max 20x)": "ultra",
        "Max 20x": "ultra",
        "~$200/month": "ultra",
        "max 200": "ultra",
    }
    for raw, expected in cases.items():
        match = match_plan("anthropic", raw, CATALOG)
        assert match.plan_id == expected, f"{raw!r} -> {match}"


def test_price_only_match_when_no_keyword():
    match = match_plan("openai", "$20", CATALOG)
    assert match.plan_id == "plus"
    assert match.method in {"alias", "alias_contained"}


def test_unspecified_and_unknown_do_not_guess():
    assert match_plan("anthropic", "unspecified", CATALOG).plan_id is None
    assert match_plan("anthropic", "", CATALOG).plan_id is None
    assert match_plan("not-a-provider", "$20", CATALOG).plan_id is None
    assert match_plan("anthropic", "some new thing", CATALOG).plan_id is None


def test_ambiguous_price_stays_unmatched():
    match = match_plan("kiro", "$20.00", CATALOG)
    assert match.plan_id is None
    assert match.method == "ambiguous_price"


def test_aliases_are_unique_per_provider():
    for provider in CATALOG["providers"]:
        seen: dict[str, str] = {}
        for plan in provider["plans"]:
            aliases = [plan["id"], plan.get("label", "")] + list(plan.get("aliases", []))
            for alias in aliases:
                key = normalize(alias)
                if not key:
                    continue
                assert seen.get(key, plan["id"]) == plan["id"], (
                    f"{provider['id']}: {key!r} maps to both {seen[key]} and {plan['id']}"
                )
                seen[key] = plan["id"]


def test_every_plan_price_is_number_or_null():
    for provider in CATALOG["providers"]:
        for plan in provider["plans"]:
            value = plan.get("price_monthly")
            assert value is None or isinstance(value, (int, float)), (provider["id"], plan["id"])
