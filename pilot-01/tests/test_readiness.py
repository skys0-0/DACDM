from __future__ import annotations

import csv
import json
from pathlib import Path

from dacdm.readiness import (
    CALIBRATION_LABEL,
    build_microbacktest_matrix,
    deterministic_humaneval_sample,
    filter_ai_price_history,
    hardware_efficiency_preview,
)


def test_deterministic_humaneval_sample(tmp_path: Path) -> None:
    tasks = [
        {
            "task_id": f"humaneval:{index}",
            "benchmark": "humaneval",
            "content_hash": "sha256:" + f"{index:064x}",
        }
        for index in range(20)
    ]
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(tasks), encoding="utf-8")
    first = deterministic_humaneval_sample(path)
    second = deterministic_humaneval_sample(path)
    assert first == second
    assert len(first) == 10
    assert all(row["calibration_label"] == CALIBRATION_LABEL for row in first)


def test_microbacktest_matrix_is_10_by_3(tmp_path: Path) -> None:
    tasks = [
        {
            "task_id": f"humaneval:{index}",
            "benchmark": "humaneval",
            "content_hash": "sha256:" + f"{index:064x}",
        }
        for index in range(10)
    ]
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(tasks), encoding="utf-8")
    sample = deterministic_humaneval_sample(path)
    matrix = build_microbacktest_matrix(sample)
    assert len(matrix) == 30
    assert {row["year"] for row in matrix} == {2024, 2025, 2026}
    assert {row["status"] for row in matrix} == {"UNASSESSED_PENDING_S1_3"}


def test_price_history_filters_provider_and_window(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    fields = [
        "provider",
        "model_id",
        "variation",
        "unit",
        "price_usd",
        "effective_from",
        "effective_to",
        "last_validated_at",
        "source_kind",
        "confidence",
        "aliases",
        "source_url",
        "notes",
    ]
    rows = [
        ["openai", "a", "input", "usd_per_mtok", "1", "2024-01-01", "", "2026-01-01", "provider_live", "verified", "", "https://example.test", ""],
        ["anthropic", "b", "output", "usd_per_mtok", "2", "2025-01-01", "", "2026-01-01", "provider_live", "verified", "", "https://example.test", ""],
        ["google", "c", "input", "usd_per_mtok", "3", "2025-01-01", "", "2026-01-01", "provider_live", "verified", "", "https://example.test", ""],
        ["openai", "old", "input", "usd_per_mtok", "4", "2023-01-01", "2023-12-31", "2023-12-31", "provider_live", "verified", "", "https://example.test", ""],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)
    selected = filter_ai_price_history(path)
    assert [(row["provider"], row["model_id"]) for row in selected] == [
        ("openai", "a"),
        ("anthropic", "b"),
    ]


def test_hardware_efficiency_preview_normalizes_2024_01(tmp_path: Path) -> None:
    path = tmp_path / "hardware.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "Release date",
            "Machine learning performance (TOP/s)",
            "Release price (2024 USD)",
            "Type",
        ])
        writer.writerow(["2023-01-01", "100", "1000", "GPU"])
        writer.writerow(["2024-06-01", "200", "1000", "GPU"])
        writer.writerow(["2024-01-01", "999", "1", "TPU"])
    preview = hardware_efficiency_preview(path)
    january = next(row for row in preview if row["month"] == "2024-01")
    july = next(row for row in preview if row["month"] == "2024-07")
    assert january["index_2024_01"] == 1.0
    assert july["index_2024_01"] == 2.0
