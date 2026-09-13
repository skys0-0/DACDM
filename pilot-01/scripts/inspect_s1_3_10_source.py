from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            slug = str(row.get("task_id", "")).replace("_", "-")
            rows[slug] = row
    return rows


def shape(value: Any, depth: int = 0) -> Any:
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {str(key): shape(item, depth + 1) for key, item in sorted(value.items())}
    if isinstance(value, list):
        if not value:
            return {"type": "list", "len": 0}
        return {"type": "list", "len": len(value), "first": shape(value[0], depth + 1)}
    return type(value).__name__


def main() -> None:
    root = Path("../leetcode-dataset/data")
    rows = {}
    for name in (
        "LeetCodeDataset-v0.3.1-train.jsonl.gz",
        "LeetCodeDataset-v0.3.1-test.jsonl.gz",
    ):
        rows.update(load_rows(root / name))

    registry = json.loads(Path("registries/leetcode_oracle_registry.json").read_text())
    signatures: Counter[str] = Counter()
    field_counts: Counter[str] = Counter()
    details = []
    for record in registry:
        slug = record["problem_slug"]
        row = rows[slug]
        for key in row:
            field_counts[key] += 1
        signature = json.dumps(shape(row.get("input_output")), sort_keys=True)
        signatures[signature] += 1
        details.append(
            {
                "canonical_task_id": record["canonical_task_id"],
                "problem_slug": slug,
                "input_output_shape": shape(row.get("input_output")),
                "has_prompt": isinstance(row.get("prompt"), str),
                "prompt_length": len(row.get("prompt", "")) if isinstance(row.get("prompt"), str) else 0,
                "has_completion": isinstance(row.get("completion"), str),
                "completion_length": len(row.get("completion", "")) if isinstance(row.get("completion"), str) else 0,
                "has_test": isinstance(row.get("test"), str),
                "test_length": len(row.get("test", "")) if isinstance(row.get("test"), str) else 0,
                "has_problem_description": isinstance(row.get("problem_description"), str),
                "problem_description_length": len(row.get("problem_description", "")) if isinstance(row.get("problem_description"), str) else 0,
                "entry_point": row.get("entry_point"),
            }
        )

    out = {
        "registered_suite_count": len(registry),
        "field_presence_counts": dict(sorted(field_counts.items())),
        "input_output_shape_distribution": dict(sorted(signatures.items())),
        "details": details,
        "contains_test_values": False,
        "purpose": "schema inspection only; no model results and no paid inference",
    }
    path = Path("backtest/s1_3_10/source_schema_inspection.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
