from __future__ import annotations

import asyncio
from collections import Counter, defaultdict

import yaml

from .cmdrun import parse_json_object, run_cmd
from .util import PROMPT_DIR, TAXONOMY_DIR, read_jsonl, sha256_text, snapshot_paths, utc_now, write_json

CATEGORIES = ("subscription", "harness", "orchestration", "platform", "model-source", "model")
CATEGORY_TITLES = {
    "subscription": "subscription providers — q1",
    "harness": "harnesses — q3",
    "orchestration": "orchestration tools — q4",
    "platform": "platforms — q5",
    "model-source": "model routes — q2 (APIs, routers, local runtimes)",
    "model": "model families — q2 (named models)",
}


def taxonomy_path(version: str = "v1"):
    return TAXONOMY_DIR / f"{version}.yml"


def load_taxonomy(version: str = "v1") -> dict:
    path = taxonomy_path(version)
    if not path.exists():
        raise SystemExit(f"missing taxonomy {path}; run `make taxonomy` and approve the draft")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.setdefault("nodes", [])
    return data


def node_categories(node: dict) -> list[str]:
    categories = node.get("categories")
    if categories:
        return list(categories)
    return [node["category"]] if node.get("category") else []


def alias_index(taxonomy: dict, category: str | None = None) -> dict[str, str]:
    index: dict[str, str] = {}
    for node in taxonomy["nodes"]:
        if category is not None and category not in node_categories(node):
            continue
        index[node["id"].lower()] = node["id"]
        index[node["label"].lower()] = node["id"]
        for alias in node.get("aliases", []):
            index[str(alias).lower().strip()] = node["id"]
    return index


def render_for_prompt(taxonomy: dict) -> str:
    by_category: dict[str, list[dict]] = defaultdict(list)
    for node in taxonomy["nodes"]:
        for category in node_categories(node):
            by_category[category].append(node)
    lines = [f"Taxonomy version {taxonomy.get('version')}. Node ids in backticks:", ""]
    for category in CATEGORIES:
        nodes = by_category.get(category, [])
        if not nodes:
            continue
        lines.append(f"### {CATEGORY_TITLES[category]}")
        for node in nodes:
            alias_text = ""
            if node.get("aliases"):
                alias_text = " (aliases: " + ", ".join(node["aliases"][:6]) + ")"
            lines.append(f"- `{node['id']}` — {node['label']}{alias_text}")
        lines.append("")
    return "\n".join(lines)


def _comment_blocks(comments: list[dict], limit_chars: int = 6000) -> str:
    blocks = []
    for comment in comments:
        text = comment["text_md"][:limit_chars]
        blocks.append(
            f'<comment id="{comment["comment_id"]}" author="{comment["author"]}" depth="{comment["depth"]}">\n{text}\n</comment>'
        )
    return "\n\n".join(blocks)


async def _harvest_batch(batch: list[dict], model: str, semaphore: asyncio.Semaphore) -> list[dict]:
    template = (PROMPT_DIR / "harvest_v1.md").read_text(encoding="utf-8")
    prompt = template.replace("{{COMMENTS}}", _comment_blocks(batch))
    async with semaphore:
        run = await run_cmd(prompt, model, max_turns=2)
    payload = parse_json_object(run.final_text)
    mentions = payload.get("mentions", [])
    valid_ids = {c["comment_id"] for c in batch}
    for mention in mentions:
        if mention.get("comment_id") not in valid_ids:
            mention["comment_id"] = batch[0]["comment_id"]
    return mentions


def harvest(snapshot_id: str, model: str = "z-ai/glm-5.3-flash", batch_size: int = 40) -> None:
    comments = [c for c in read_jsonl(snapshot_paths(snapshot_id)["comments"]) if c["text_md"]]
    batches = [comments[i : i + batch_size] for i in range(0, len(comments), batch_size)]
    print(f"harvesting tool names from {len(comments)} comments in {len(batches)} batches via {model}")

    async def run_all() -> list[dict]:
        semaphore = asyncio.Semaphore(4)
        results = await asyncio.gather(
            *(_harvest_batch(batch, model, semaphore) for batch in batches), return_exceptions=True
        )
        mentions: list[dict] = []
        failures = 0
        for result in results:
            if isinstance(result, Exception):
                failures += 1
                print(f"  batch failed: {result}")
                continue
            mentions.extend(result)
        print(f"  batches failed: {failures}")
        return mentions

    mentions = asyncio.run(run_all())

    counts: Counter[str] = Counter()
    raws: dict[str, Counter[str]] = defaultdict(Counter)
    categories: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)
    for mention in mentions:
        normalized = str(mention.get("normalized", "")).strip().lower()
        if not normalized:
            continue
        counts[normalized] += 1
        raws[normalized][str(mention.get("raw", "")).strip()] += 1
        categories[normalized][str(mention.get("category", "unknown"))] += 1
        if len(examples[normalized]) < 5:
            examples[normalized].append(mention.get("comment_id"))

    candidates = [
        {
            "normalized": name,
            "count": counts[name],
            "raw_forms": dict(raws[name].most_common(8)),
            "categories": dict(categories[name].most_common()),
            "example_comment_ids": examples[name],
        }
        for name in counts
    ]
    candidates.sort(key=lambda c: (-c["count"], c["normalized"]))

    write_json(
        TAXONOMY_DIR / "candidates.json",
        {
            "snapshot_id": snapshot_id,
            "model": model,
            "generated_at": utc_now().isoformat(),
            "prompt_hash": sha256_text((PROMPT_DIR / "harvest_v1.md").read_text(encoding="utf-8")),
            "mentions": len(mentions),
            "candidates": candidates,
        },
    )
    print(f"wrote {len(candidates)} candidates to pipeline/taxonomy/candidates.json")
    for candidate in candidates[:40]:
        print(f"  {candidate['count']:>4}  {candidate['normalized']:<28} {next(iter(candidate['categories']))}")
