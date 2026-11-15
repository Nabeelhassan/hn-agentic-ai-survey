from __future__ import annotations

from .taxonomy import alias_index

FIELD_CATEGORIES: dict[str, tuple[str, ...]] = {
    "q1_subscriptions": ("subscription",),
    "q2_outside": ("model-source", "model"),
    "q3_harnesses": ("harness",),
    "q4_orchestration": ("orchestration",),
    "q5_platforms": ("platform",),
}

_INDEX_CACHE: dict[tuple[int, str], dict[str, str]] = {}


def _index(taxonomy: dict, category: str) -> dict[str, str]:
    key = (id(taxonomy), category)
    if key not in _INDEX_CACHE:
        _INDEX_CACHE[key] = alias_index(taxonomy, category)
    return _INDEX_CACHE[key]


def canonicalize_node(raw: str, taxonomy: dict, categories: tuple[str, ...]) -> str:
    key = (raw or "").strip().lower()
    if not key:
        return ""
    if key.startswith("other:"):
        key = key[len("other:") :]
    for category in categories:
        match = _index(taxonomy, category).get(key)
        if match:
            return match
    return f"other:{key}"


def canonicalize_record(record: dict, taxonomy: dict) -> dict:
    canonical = dict(record)
    for field, categories in FIELD_CATEGORIES.items():
        items = []
        seen: set[str] = set()
        for item in record.get(field, []) or []:
            node = canonicalize_node(str(item.get("node", "")), taxonomy, categories)
            if not node or node in seen:
                continue
            seen.add(node)
            items.append({**item, "node": node})
        canonical[field] = items
    return canonical
