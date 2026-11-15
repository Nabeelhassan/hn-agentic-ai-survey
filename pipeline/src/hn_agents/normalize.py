from __future__ import annotations

import html
import re

from .util import RAW_DIR, read_json, sha256_text, snapshot_paths, utc_now, write_json, write_jsonl

STORY_ID = 50366117

ANCHOR_RE = re.compile(r'<a\b[^>]*?href="([^"]*)"[^>]*?>(.*?)</a>', re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
BLANK_LINES_RE = re.compile(r"\n{3,}")
SPACES_RE = re.compile(r"[ \t]{2,}")


def html_to_markdown(raw: str) -> str:
    text = html.unescape(raw or "")

    def anchor(match: re.Match) -> str:
        url, label = match.group(1), TAG_RE.sub("", match.group(2)).strip()
        if not label or label == url:
            return url
        return f"{label} ({url})"

    text = ANCHOR_RE.sub(anchor, text)
    text = re.sub(r"<pre><code>", "\n```\n", text, flags=re.I)
    text = re.sub(r"</code></pre>", "\n```\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</?p>", "\n\n", text, flags=re.I)
    text = re.sub(r"</?(i|em)>", "_", text, flags=re.I)
    text = TAG_RE.sub("", text)
    text = text.replace("\xa0", " ")
    text = SPACES_RE.sub(" ", text)
    text = BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def _depths(records: dict[str, dict]) -> dict[str, int]:
    depths: dict[str, int] = {}

    def resolve(comment_id: str, guard: set[str]) -> int:
        if comment_id in depths:
            return depths[comment_id]
        record = records.get(comment_id)
        if record is None:
            return 0
        if record["is_top_level"] or comment_id in guard:
            depths[comment_id] = 0
            return 0
        parent_id = record.get("parent_id")
        if parent_id is None or str(parent_id) not in records:
            depths[comment_id] = 0
            return 0
        guard.add(comment_id)
        depths[comment_id] = resolve(str(parent_id), guard) + 1
        return depths[comment_id]

    for comment_id in records:
        resolve(comment_id, set())
    return depths


def build_comments(snapshot_id: str) -> list[dict]:
    algolia = read_json(RAW_DIR / snapshot_id / "algolia.json")
    firebase = read_json(RAW_DIR / snapshot_id / "firebase-comments.json")

    records: dict[str, dict] = {}
    for hit in algolia:
        comment_id = str(hit["objectID"])
        raw_text = hit.get("comment_text") or ""
        records[comment_id] = {
            "comment_id": comment_id,
            "snapshot_id": snapshot_id,
            "parent_id": str(hit["parent_id"]) if hit.get("parent_id") else None,
            "story_id": str(hit.get("story_id") or STORY_ID),
            "author": hit.get("author") or "[deleted]",
            "text_raw": raw_text,
            "text_md": html_to_markdown(raw_text),
            "created_at": hit.get("created_at"),
            "created_at_i": hit.get("created_at_i"),
            "updated_at": hit.get("updated_at"),
            "points": None,
            "deleted": False,
            "dead": False,
            "is_top_level": False,
            "label": "algolia",
        }

    for key, item in firebase.items():
        comment_id = str(key)
        if comment_id in records:
            record = records[comment_id]
            record["deleted"] = bool(item.get("deleted"))
            record["dead"] = bool(item.get("dead"))
            record["points"] = item.get("score")
            record["label"] = "both"
            continue
        raw_text = item.get("text") or ""
        records[comment_id] = {
            "comment_id": comment_id,
            "snapshot_id": snapshot_id,
            "parent_id": str(item["parent"]) if item.get("parent") else None,
            "story_id": str(STORY_ID),
            "author": item.get("by") or "[deleted]",
            "text_raw": raw_text,
            "text_md": html_to_markdown(raw_text),
            "created_at": _iso(item.get("time")),
            "created_at_i": item.get("time"),
            "updated_at": None,
            "points": item.get("score"),
            "deleted": bool(item.get("deleted")),
            "dead": bool(item.get("dead")),
            "is_top_level": False,
            "label": "firebase_only",
        }

    for record in records.values():
        record["is_top_level"] = record["parent_id"] == str(STORY_ID)
        record["content_hash"] = sha256_text(record["text_md"])
        record["text_chars"] = len(record["text_md"])

    depths = _depths(records)
    for comment_id, record in records.items():
        record["depth"] = depths[comment_id]

    return sorted(records.values(), key=lambda r: (r["created_at_i"] or 0, r["comment_id"]))


def _iso(epoch: int | None) -> str | None:
    if not epoch:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def normalize_snapshot(snapshot_id: str) -> list[dict]:
    comments = build_comments(snapshot_id)
    paths = snapshot_paths(snapshot_id)
    written = write_jsonl(paths["comments"], comments)

    authors = {c["author"] for c in comments if c["author"] != "[deleted]"}
    stats = {
        "snapshot_id": snapshot_id,
        "normalized_at": utc_now().isoformat(),
        "comments": written,
        "top_level": sum(1 for c in comments if c["is_top_level"]),
        "deleted": sum(1 for c in comments if c["deleted"]),
        "dead": sum(1 for c in comments if c["dead"]),
        "empty_text": sum(1 for c in comments if not c["text_md"]),
        "authors": len(authors),
        "max_depth": max((c["depth"] for c in comments), default=0),
        "source_labels": {
            "algolia_only": sum(1 for c in comments if c["label"] == "algolia"),
            "both": sum(1 for c in comments if c["label"] == "both"),
            "firebase_only": sum(1 for c in comments if c["label"] == "firebase_only"),
        },
    }
    meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
    meta.setdefault("snapshot_id", snapshot_id)
    meta["normalize"] = stats
    write_json(paths["meta"], meta)
    print(f"normalized {written} comments from {stats['authors']} authors (max depth {stats['max_depth']})")
    return comments
