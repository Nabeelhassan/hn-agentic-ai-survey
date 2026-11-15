from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
EVAL_DIR = DATA_DIR / "eval"
PIPELINE_DIR = REPO_ROOT / "pipeline"
PROMPT_DIR = PIPELINE_DIR / "prompts"
TAXONOMY_DIR = PIPELINE_DIR / "taxonomy"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_snapshot_id(at: datetime | None = None) -> str:
    at = at or utc_now()
    return at.strftime("%Y-%m-%dT%H%M%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_json(path: Path, value: object) -> None:
    _atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    _atomic_write(path, "\n".join(lines) + ("\n" if lines else ""))
    return len(lines)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def list_snapshots() -> list[str]:
    ids: set[str] = set()
    for root in (RAW_DIR, SNAPSHOT_DIR):
        if root.exists():
            ids.update(p.name for p in root.iterdir() if p.is_dir())
    return sorted(ids)


def latest_snapshot() -> str:
    ids = list_snapshots()
    if not ids:
        raise SystemExit("no snapshots yet — run `make fetch && make normalize` first")
    return ids[-1]


def resolve_snapshot(value: str | None) -> str:
    if value in (None, "", "latest"):
        return latest_snapshot()
    return value


def snapshot_paths(snapshot_id: str) -> dict[str, Path]:
    root = SNAPSHOT_DIR / snapshot_id
    return {
        "root": root,
        "raw": RAW_DIR / snapshot_id,
        "comments": root / "comments.jsonl",
        "extractions": root / "extractions.jsonl",
        "respondents": root / "respondents.jsonl",
        "review": root / "review.jsonl",
        "aggregates": root / "aggregates",
        "meta": root / "meta.json",
    }
