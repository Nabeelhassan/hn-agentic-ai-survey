from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CATALOG_DIR = Path(__file__).resolve().parents[2] / "catalog"
REPO_ROOT = Path(__file__).resolve().parents[3]
CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}
CURRENCY_CODES = {"usd": "USD", "eur": "EUR", "gbp": "GBP", "euro": "EUR", "dollars": "USD"}
AMOUNT_SYMBOL_FIRST = re.compile(r"([$€£])\s?(\d+(?:[.,]\d+)?)")
AMOUNT_SYMBOL_LAST = re.compile(r"(\d+(?:[.,]\d+)?)\s?([$€£]|usd|eur|gbp|euro|dollars)(?=$|\s|[^\w])", re.I)
MONTHLY = re.compile(r"/\s?(mo|month)|per\s+month|monthly", re.I)
ANNUAL = re.compile(r"/\s?(yr|year)|per\s+year|annual|yearly", re.I)


def load_catalog(version: str = "v1") -> dict:
    path = CATALOG_DIR / f"{version}.yml"
    if not path.exists():
        raise SystemExit(f"missing catalog {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.setdefault("providers", [])
    return data


def provider_by_id(catalog: dict, provider_id: str) -> dict | None:
    return next((p for p in catalog["providers"] if p["id"] == provider_id), None)


def plans(catalog: dict):
    for provider in catalog["providers"]:
        for plan in provider.get("plans", []):
            yield provider, plan


def normalize(raw: str) -> str:
    return " ".join(str(raw or "").lower().replace("∕", "/").split())


@dataclass
class Price:
    amount: float
    currency: str
    period: str  # month | year | unknown


def parse_price(raw: str) -> Price | None:
    text = normalize(raw)
    match = AMOUNT_SYMBOL_FIRST.search(text)
    currency = None
    amount_text = None
    if match:
        currency = CURRENCY_SYMBOLS[match.group(1)]
        amount_text = match.group(2)
    else:
        match = AMOUNT_SYMBOL_LAST.search(text)
        if match:
            amount_text = match.group(1)
            token = match.group(2).lower()
            currency = CURRENCY_SYMBOLS.get(token) or CURRENCY_CODES.get(token)
    if not amount_text or not currency:
        return None
    amount = float(amount_text.replace(",", "."))
    if ANNUAL.search(text):
        period = "year"
    elif MONTHLY.search(text):
        period = "month"
    else:
        period = "unknown"
    return Price(amount=amount, currency=currency, period=period)


def alias_index(provider: dict) -> dict[str, str]:
    index: dict[str, str] = {}
    for plan in provider.get("plans", []):
        for alias in [plan["id"], plan.get("label", "")] + list(plan.get("aliases", [])):
            key = normalize(alias)
            if key:
                index[key] = plan["id"]
    return index


@dataclass
class Match:
    provider_id: str
    raw: str
    plan_id: str | None
    method: str
    confidence: float


def match_plan(provider_id: str, raw: str, catalog: dict) -> Match:
    provider = provider_by_id(catalog, provider_id)
    if provider is None:
        return Match(provider_id, raw, None, "unknown_provider", 0.0)
    text = normalize(raw)
    if not text or text in {"unspecified", "unknown", "n/a", "none", "other"}:
        return Match(provider_id, raw, None, "unspecified", 0.0)

    index = alias_index(provider)
    if text in index:
        return Match(provider_id, raw, index[text], "alias", 1.0)

    contained = [(alias, plan_id) for alias, plan_id in index.items() if alias and alias in text]
    if contained:
        alias, plan_id = max(contained, key=lambda pair: len(pair[0]))
        return Match(provider_id, raw, plan_id, "alias_contained", 0.85)

    price = parse_price(raw)
    if price is not None:
        field = "price_annual" if price.period == "year" else "price_monthly"
        candidates = [
            plan
            for plan in provider.get("plans", [])
            if plan.get(field) is not None
            and abs(float(plan[field]) - price.amount) < 0.01
            and provider.get("currency", "USD") == price.currency
        ]
        if len(candidates) == 1:
            return Match(provider_id, raw, candidates[0]["id"], "price", 0.7)
        if len(candidates) > 1:
            return Match(provider_id, raw, None, "ambiguous_price", 0.0)

    return Match(provider_id, raw, None, "no_match", 0.0)


def _money(provider: dict, plan: dict, field: str) -> str:
    amount = plan.get(field)
    if amount is None:
        return "—"
    symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(provider.get("currency", "USD"), "")
    formatted = f"{amount:,.2f}".rstrip("0").rstrip(".")
    return f"{symbol}{formatted}"


def render_markdown(catalog: dict) -> str:
    lines = [
        "# Subscription catalog",
        "",
        f"List prices captured on **{catalog.get('retrieved_at')}** from vendor pages. "
        "No currency conversion; EUR and GBP stay in their own currency. "
        "Only individual paid plans feed spend comparisons.",
        "",
        "| Provider | Plans | Verified | Source |",
        "| --- | --- | --- | --- |",
    ]
    for provider in catalog["providers"]:
        source = provider.get("source_url")
        source_cell = f"[link]({source})" if source else "—"
        lines.append(
            f"| {provider['label']} | {len(provider.get('plans', []))} | "
            f"{provider.get('verification', 'unknown')} | {source_cell} |"
        )

    gaps: list[str] = []
    for provider in catalog["providers"]:
        if provider.get("verification") != "verified":
            gaps.append(f"{provider['label']} ({provider.get('verification')})")
        lines += ["", f"## {provider['label']}", ""]
        if provider.get("notes"):
            lines += [provider["notes"].strip(), ""]
        if not provider.get("plans"):
            lines.append("_No verified plans captured._")
            continue
        lines += [
            "| Plan | Audience | Monthly | Annual | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
        for plan in provider["plans"]:
            annual = _money(provider, plan, "price_annual")
            if annual == "—" and plan.get("annual_monthly") is not None:
                annual = f"{_money(provider, plan, 'annual_monthly')}/mo"
            note = plan.get("note", "")
            lines.append(
                f"| {plan['label']} | {plan.get('audience', 'individual')} | "
                f"{_money(provider, plan, 'price_monthly')} | {annual} | {note} |"
            )
        for plan in provider["plans"]:
            if plan.get("price_monthly") is None and plan.get("audience") == "individual":
                gaps.append(f"{provider['label']} · {plan['label']}")

    lines += [
        "",
        "## Gaps",
        "",
        "Prices the vendor pages did not expose. These are intentionally left blank rather "
        "than estimated.",
        "",
    ]
    lines += [f"- {gap}" for gap in gaps] or ["- None."]
    lines += [
        "",
        "## Matching rules",
        "",
        "1. Exact alias or plan id wins.",
        "2. Otherwise the longest alias contained in the string wins (`Ultra (aka Max 20x)` → Ultra).",
        "3. Otherwise a unique monthly price in the provider's currency wins (`$20/mo` → the $20 plan).",
        "4. Ambiguous prices and unknown names stay unmatched and are reported, never guessed.",
        "",
    ]
    return "\n".join(lines)


def write_docs(catalog: dict, path: Path | None = None) -> Path:
    path = path or REPO_ROOT / "docs" / "CATALOG.md"
    path.write_text(render_markdown(catalog), encoding="utf-8")
    return path
