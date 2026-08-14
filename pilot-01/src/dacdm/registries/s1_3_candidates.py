from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class CandidateExtractionError(ValueError):
    """Raised when S1.3 candidate extraction cannot be completed deterministically."""


def extract_model_candidates(price_csv: Path) -> list[dict[str, Any]]:
    with price_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise CandidateExtractionError("price CSV has no header")
        required = {"provider", "model_id", "effective_from", "effective_to"}
        missing = sorted(required.difference(reader.fieldnames))
        if missing:
            raise CandidateExtractionError(
                "price CSV missing required columns: " + ", ".join(missing)
            )
        rows = [dict(row) for row in reader]

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        provider = row["provider"].strip()
        if provider.lower() not in {"openai", "anthropic"}:
            continue
        model_id = row["model_id"].strip()
        if not model_id:
            continue
        grouped[(provider, model_id)].append(row)

    candidates: list[dict[str, Any]] = []
    for (provider, model_id), model_rows in grouped.items():
        starts = sorted(
            value
            for value in (row["effective_from"].strip() for row in model_rows)
            if value
        )
        ends = sorted(
            value
            for value in (row["effective_to"].strip() for row in model_rows)
            if value
        )
        candidates.append(
            {
                "provider": provider,
                "source_model_id": model_id,
                "first_price_effective_from": starts[0] if starts else None,
                "last_closed_price_effective_to": ends[-1] if ends else None,
                "price_row_count": len(model_rows),
                "identity_status": "CANDIDATE_PENDING_FIRST_PARTY_IDENTITY_EVIDENCE",
                "launch_date_status": "UNVERIFIED",
                "training_cutoff_status": "UNVERIFIED",
                "historical_snapshot_status": "UNVERIFIED",
            }
        )

    candidates.sort(key=lambda row: (str(row["provider"]).lower(), str(row["source_model_id"])))
    if not candidates:
        raise CandidateExtractionError("no OpenAI/Anthropic model candidates found")
    return candidates


def write_model_candidates(price_csv: Path, output: Path) -> list[dict[str, Any]]:
    records = extract_model_candidates(price_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return records
