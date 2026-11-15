from __future__ import annotations

import shutil

from .util import REPO_ROOT, read_json, snapshot_paths, write_json

DASHBOARD_DATA = REPO_ROOT / "dashboard" / "public" / "data"


def export_dashboard_data(snapshot_id: str) -> None:
    paths = snapshot_paths(snapshot_id)
    aggregates = paths["aggregates"]
    if not aggregates.exists():
        raise SystemExit("no aggregates yet — run `make aggregate` first")

    if DASHBOARD_DATA.exists():
        shutil.rmtree(DASHBOARD_DATA)
    DASHBOARD_DATA.mkdir(parents=True)

    files = sorted(aggregates.glob("*.json"))
    for file in files:
        shutil.copy2(file, DASHBOARD_DATA / file.name)

    meta = read_json(paths["meta"]) if paths["meta"].exists() else {}
    write_json(
        DASHBOARD_DATA / "index.json",
        {
            "snapshot_id": snapshot_id,
            "snapshots": [paths["root"].name],
            "generated_at": meta.get("normalize", {}).get("normalized_at"),
            "files": [file.name for file in files],
        },
    )
    (DASHBOARD_DATA / "llms.txt").write_text(
        "# HN Agentic AI Survey — machine-readable data\n\n"
        "Story: https://news.ycombinator.com/item?id=50366117\n"
        f"Snapshot: {snapshot_id}\n\n"
        "Files (JSON): " + ", ".join(file.name for file in files) + "\n\n"
        "Every aggregate row carries count, n_denominator, and comment_ids. "
        "Comment permalinks: https://news.ycombinator.com/item?id=<comment_id>\n",
        encoding="utf-8",
    )
    print(f"copied {len(files)} aggregate files into dashboard/public/data")
