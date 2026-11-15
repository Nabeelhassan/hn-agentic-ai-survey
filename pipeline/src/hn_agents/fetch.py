from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .util import RAW_DIR, make_snapshot_id, utc_now, write_json

STORY_ID = 50366117
ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
FIREBASE_ITEM = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
USER_AGENT = "hn-agentic-ai-survey/0.1 (+https://github.com/Nabeelhassan/hn-agentic-ai-survey)"
RETRY_STATUS = {429, 500, 502, 503, 504}


async def _get(client: httpx.AsyncClient, url: str, *, params: dict | None = None, attempts: int = 4) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as error:
            last_error = error
            await asyncio.sleep(1.5 * 2**attempt)
            continue
        if response.status_code in RETRY_STATUS:
            last_error = RuntimeError(f"{response.status_code} from {response.request.url}")
            await asyncio.sleep(1.5 * 2**attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"giving up on {url}: {last_error}")


async def fetch_algolia(client: httpx.AsyncClient, story_id: int = STORY_ID) -> list[dict]:
    hits: list[dict] = []
    page = 0
    while True:
        payload = await _get(
            client,
            ALGOLIA_URL,
            params={"tags": f"comment,story_{story_id}", "hitsPerPage": 1000, "page": page},
        )
        hits.extend(payload.get("hits", []))
        total_pages = payload.get("nbPages", 1)
        page += 1
        if page >= total_pages:
            return hits


async def fetch_firebase(client: httpx.AsyncClient, story_id: int = STORY_ID) -> tuple[dict, dict[int, dict]]:
    story = await _get(client, FIREBASE_ITEM.format(item_id=story_id))
    items: dict[int, dict] = {story_id: story}
    semaphore = asyncio.Semaphore(16)

    async def fetch_one(item_id: int) -> dict | None:
        async with semaphore:
            return await _get(client, FIREBASE_ITEM.format(item_id=item_id))

    frontier = [int(kid) for kid in story.get("kids", [])]
    while frontier:
        results = await asyncio.gather(*(fetch_one(item_id) for item_id in frontier))
        frontier = []
        for item in results:
            if not item:
                continue
            item_id = int(item["id"])
            items[item_id] = item
            frontier.extend(int(kid) for kid in item.get("kids", []) if int(kid) not in items)
    items.pop(story_id, None)
    return story, items


async def fetch_snapshot(story_id: int = STORY_ID, snapshot_id: str | None = None) -> str:
    snapshot_id = snapshot_id or make_snapshot_id()
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0), headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        (story, firebase_items), algolia_hits = await asyncio.gather(
            fetch_firebase(client, story_id), fetch_algolia(client, story_id)
        )

    raw_dir = RAW_DIR / snapshot_id
    write_json(raw_dir / "story.json", story)
    write_json(raw_dir / "firebase-comments.json", firebase_items)
    write_json(raw_dir / "algolia.json", algolia_hits)
    write_json(
        raw_dir / "fetch-meta.json",
        {
            "snapshot_id": snapshot_id,
            "story_id": story_id,
            "fetched_at": utc_now().isoformat(),
            "algolia_hits": len(algolia_hits),
            "firebase_comments": len(firebase_items),
            "story_descendants": story.get("descendants"),
            "story_score": story.get("score"),
            "story_title": story.get("title"),
        },
    )
    print(
        f"snapshot {snapshot_id}: algolia={len(algolia_hits)} firebase={len(firebase_items)} "
        f"hn_descendants={story.get('descendants')}"
    )
    return snapshot_id
