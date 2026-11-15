from __future__ import annotations

import asyncio
from collections import Counter

from .cmdrun import parse_json_object, run_cmd
from .util import PROMPT_DIR, read_jsonl, snapshot_paths, utc_now, write_json


async def _run(prompt: str, model: str) -> dict:
    run = await run_cmd(prompt, model, max_turns=2)
    return parse_json_object(run.final_text)


def cluster_themes(snapshot_id: str, model: str = "z-ai/glm-5.3-flash") -> None:
    paths = snapshot_paths(snapshot_id)
    respondents = read_jsonl(paths["respondents"])
    counts: Counter[str] = Counter()
    for respondent in respondents:
        for theme in respondent.get("themes") or []:
            cleaned = " ".join(str(theme).split()).strip().lower()
            if cleaned:
                counts[cleaned] += 1

    phrases = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    lines = [f"{count}\t{phrase}" for phrase, count in phrases]
    template = (PROMPT_DIR / "themes_v1.md").read_text(encoding="utf-8")
    prompt = template.replace("{{PHRASES}}", "\n".join(lines))

    print(f"clustering {len(phrases)} theme phrases via {model}")
    payload = asyncio.run(_run(prompt, model))

    mapping: dict[str, str] = {}
    labels: list[dict] = []
    for group in payload.get("themes", []):
        label = " ".join(str(group.get("label", "")).split()).strip().lower()
        if not label:
            continue
        members = [" ".join(str(p).split()).strip().lower() for p in group.get("phrases", [])]
        labels.append({"label": label, "phrases": members})
        for phrase in members:
            mapping[phrase] = label

    unmapped = [phrase for phrase, _ in phrases if phrase not in mapping]
    write_json(
        paths["root"] / "theme-map.json",
        {
            "snapshot_id": snapshot_id,
            "model": model,
            "generated_at": utc_now().isoformat(),
            "labels": labels,
            "mapping": mapping,
            "unmapped": unmapped,
            "phrases": len(phrases),
        },
    )
    print(f"clustered into {len(labels)} themes, {len(unmapped)} phrases left unmapped")
