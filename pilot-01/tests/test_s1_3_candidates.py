from __future__ import annotations

import csv
from pathlib import Path

import pytest

from dacdm.registries.s1_3_candidates import (
    CandidateExtractionError,
    extract_model_candidates,
)


def test_extract_model_candidates_groups_openai_and_anthropic(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["provider", "model_id", "effective_from", "effective_to"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "provider": "OpenAI",
                    "model_id": "gpt-test",
                    "effective_from": "2024-01-01",
                    "effective_to": "2024-06-01",
                },
                {
                    "provider": "OpenAI",
                    "model_id": "gpt-test",
                    "effective_from": "2024-06-01",
                    "effective_to": "",
                },
                {
                    "provider": "Anthropic",
                    "model_id": "claude-test",
                    "effective_from": "2024-02-01",
                    "effective_to": "",
                },
                {
                    "provider": "Other",
                    "model_id": "ignored",
                    "effective_from": "2024-01-01",
                    "effective_to": "",
                },
            ]
        )

    records = extract_model_candidates(path)
    assert [row["source_model_id"] for row in records] == ["claude-test", "gpt-test"]
    gpt = records[1]
    assert gpt["first_price_effective_from"] == "2024-01-01"
    assert gpt["last_closed_price_effective_to"] == "2024-06-01"
    assert gpt["price_row_count"] == 2
    assert gpt["launch_date_status"] == "UNVERIFIED"


def test_extract_model_candidates_rejects_missing_required_columns(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text("provider,model_id\nOpenAI,gpt-test\n", encoding="utf-8")
    with pytest.raises(CandidateExtractionError):
        extract_model_candidates(path)
