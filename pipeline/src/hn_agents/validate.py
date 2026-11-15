from __future__ import annotations

import json
from pathlib import Path

from .util import EVAL_DIR, read_json, read_jsonl, snapshot_paths, utc_now, write_json

NODE_FIELDS = {
    "q1_subscriptions": "subscriptions",
    "q2_outside": "outside models",
    "q3_harnesses": "harnesses",
    "q4_orchestration": "orchestration",
    "q5_platforms": "platforms",
}


def _nodes(record: dict, field: str) -> set[str]:
    return {item.get("node") for item in record.get(field, []) if item.get("node")}


def _prf(true_positive: int, predicted: int, actual: int) -> dict:
    precision = true_positive / predicted if predicted else None
    recall = true_positive / actual if actual else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
    }


def evaluate_snapshot(snapshot_id: str, gold_path: Path | None = None, model: str = "z-ai/glm-5.3-flash") -> None:
    gold_path = gold_path or EVAL_DIR / "gold_v1.jsonl"
    gold = read_jsonl(gold_path)
    if not gold:
        raise SystemExit(f"no gold labels at {gold_path}")

    paths = snapshot_paths(snapshot_id)
    records = {
        r["comment_id"]: r
        for r in read_jsonl(paths["extractions"])
        if r["model"] == model and r.get("status") == "ok"
    }

    answer_correct = 0
    answer_total = 0
    per_field: dict[str, dict] = {
        field: {"tp": 0, "predicted": 0, "actual": 0} for field in NODE_FIELDS
    }
    misses: list[dict] = []

    for case in gold:
        comment_id = case["comment_id"]
        expected = case["expected"]
        predicted = records.get(comment_id)
        if predicted is None:
            continue
        answer_total += 1
        if predicted.get("answers_questions") == expected.get("answers_questions"):
            answer_correct += 1
        for field in NODE_FIELDS:
            actual_nodes = set(expected.get(field, []))
            predicted_nodes = _nodes(predicted, field)
            per_field[field]["tp"] += len(actual_nodes & predicted_nodes)
            per_field[field]["predicted"] += len(predicted_nodes)
            per_field[field]["actual"] += len(actual_nodes)
            if actual_nodes != predicted_nodes:
                misses.append(
                    {
                        "comment_id": comment_id,
                        "field": field,
                        "expected": sorted(actual_nodes),
                        "predicted": sorted(predicted_nodes),
                    }
                )

    report = {
        "snapshot_id": snapshot_id,
        "generated_at": utc_now().isoformat(),
        "model": model,
        "gold_cases": len(gold),
        "evaluated": answer_total,
        "answers_questions_accuracy": round(answer_correct / answer_total, 3) if answer_total else None,
        "fields": {
            field: {
                "label": label,
                **_prf(
                    per_field[field]["tp"], per_field[field]["predicted"], per_field[field]["actual"]
                ),
            }
            for field, label in NODE_FIELDS.items()
        },
        "misses": misses[:200],
    }
    write_json(paths["root"] / "eval.json", report)
    write_json(EVAL_DIR / "report.json", report)
    print(
        f"eval: {answer_total} labelled comments, answers_questions accuracy "
        f"{report['answers_questions_accuracy']}, misses {len(misses)}"
    )


def write_gold(rows: list[dict], path: Path | None = None) -> None:
    path = path or EVAL_DIR / "gold_v1.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} gold cases to {path}")
