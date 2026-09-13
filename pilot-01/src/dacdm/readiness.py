from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any


CALIBRATION_LABEL = "EXPLORATORY_PIPELINE_CALIBRATION_NOT_CONFIRMATORY_EVIDENCE"
YEARS = (2024, 2025, 2026)


class ReadinessError(ValueError):
    """Raised when S1.2.5 readiness inputs cannot be processed deterministically."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_humaneval_sample(tasks_path: Path, n: int = 10) -> list[dict[str, Any]]:
    raw = json.loads(tasks_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ReadinessError("tasks registry must be a JSON array")
    humaneval = [
        row
        for row in raw
        if isinstance(row, dict) and row.get("benchmark") == "humaneval"
    ]
    if len(humaneval) < n:
        raise ReadinessError(f"need at least {n} HumanEval tasks, found {len(humaneval)}")

    ranked: list[tuple[str, dict[str, Any]]] = []
    for row in humaneval:
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ReadinessError("HumanEval task missing string task_id")
        digest = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
        ranked.append((digest, row))

    ranked.sort(key=lambda item: (item[0], str(item[1]["task_id"])))
    return [
        {
            "task_id": row["task_id"],
            "content_hash": row.get("content_hash"),
            "selection_sha256": digest,
            "calibration_label": CALIBRATION_LABEL,
        }
        for digest, row in ranked[:n]
    ]


def build_microbacktest_matrix(sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": row["task_id"],
            "year": year,
            "status": "UNASSESSED_PENDING_S1_3",
            "reason": "MODEL_AND_HISTORICAL_SNAPSHOT_EVIDENCE_NOT_YET_POPULATED",
            "minimum_successful_cost_usd": "",
            "calibration_label": CALIBRATION_LABEL,
        }
        for row in sample
        for year in YEARS
    ]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ReadinessError(f"CSV has no header: {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def filter_ai_price_history(path: Path) -> list[dict[str, str]]:
    fields, rows = _read_csv(path)
    required = {
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
        "source_url",
    }
    missing = sorted(required.difference(fields))
    if missing:
        raise ReadinessError(f"AI price CSV missing columns: {', '.join(missing)}")

    start = date(2024, 1, 1)
    end = date(2027, 1, 1)
    selected: list[dict[str, str]] = []
    for row in rows:
        if row["provider"].strip().lower() not in {"openai", "anthropic"}:
            continue
        if row["variation"].strip().lower() not in {"input", "output"}:
            continue
        try:
            effective_from = date.fromisoformat(row["effective_from"].strip())
            effective_to = (
                date.fromisoformat(row["effective_to"].strip())
                if row["effective_to"].strip()
                else None
            )
        except ValueError as exc:
            raise ReadinessError(
                f"invalid AI price validity date for {row['model_id']}"
            ) from exc
        if effective_from >= end:
            continue
        if effective_to is not None and effective_to <= start:
            continue
        selected.append(row)

    if not selected:
        raise ReadinessError("no OpenAI/Anthropic price rows overlap 2024–2026")
    return selected


def _normalise_header(value: str) -> str:
    cleaned = value.lower().replace("_", " ").replace("-", " ")
    return " ".join(cleaned.split())


def _find_header(fields: Iterable[str], candidates: tuple[str, ...]) -> str:
    normalised = {_normalise_header(field): field for field in fields}
    for candidate in candidates:
        normalised_candidate = _normalise_header(candidate)
        if normalised_candidate in normalised:
            return normalised[normalised_candidate]
    raise ReadinessError(f"hardware CSV missing required column; tried {candidates}")


def _find_header_terms(
    fields: Iterable[str],
    required_terms: tuple[str, ...],
    preferred_terms: tuple[str, ...] = (),
) -> str:
    matches: list[tuple[int, str]] = []
    for field in fields:
        normalised = _normalise_header(field)
        if all(term in normalised for term in required_terms):
            score = sum(term in normalised for term in preferred_terms)
            matches.append((score, field))
    if not matches:
        raise ReadinessError(
            "hardware CSV missing required column containing terms: "
            + ", ".join(required_terms)
        )
    matches.sort(key=lambda item: (-item[0], item[1]))
    return matches[0][1]


def _parse_float(value: str) -> float | None:
    stripped = value.strip().replace(",", "").replace("$", "")
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _resolve_epoch_performance_column(fields: list[str]) -> str:
    preferred = (
        "Tensor-FP16/BF16 performance (FLOP/s)",
        "ML OP/s",
        "Max performance",
        "Machine learning performance (TOP/s)",
    )
    try:
        return _find_header(fields, preferred)
    except ReadinessError:
        return _find_header_terms(
            fields,
            ("performance",),
            ("tensor", "bf16", "machine learning", "ml", "top/s", "tops"),
        )


def _resolve_epoch_price_column(fields: list[str]) -> tuple[str, str]:
    try:
        adjusted = _find_header(fields, ("Release price (2024 USD)",))
        return adjusted, "SOURCE_PROVIDED_2024_USD_PREVIEW"
    except ReadinessError:
        nominal = _find_header(fields, ("Release price (USD)",))
        return nominal, "NOMINAL_RELEASE_USD_PREVIEW_NOT_FINAL_IF_07_DEFLATOR"


def hardware_efficiency_preview(path: Path) -> list[dict[str, Any]]:
    fields, rows = _read_csv(path)
    release_col = _find_header_terms(fields, ("release", "date"))
    perf_col = _resolve_epoch_performance_column(fields)
    price_col, price_basis = _resolve_epoch_price_column(fields)

    type_col: str | None = None
    try:
        type_col = _find_header(fields, ("type", "hardware type"))
    except ReadinessError:
        pass

    observations: list[tuple[date, float]] = []
    for row in rows:
        if type_col is not None and "gpu" not in row.get(type_col, "").strip().lower():
            continue
        raw_date = row.get(release_col, "").strip()
        try:
            released = date.fromisoformat(raw_date[:10])
        except ValueError:
            continue
        perf = _parse_float(row.get(perf_col, ""))
        price = _parse_float(row.get(price_col, ""))
        if perf is None or price is None or perf <= 0 or price <= 0:
            continue
        observations.append((released, perf / price))

    if not observations:
        raise ReadinessError(
            "no usable GPU performance/price observations in Epoch snapshot; "
            f"resolved columns release={release_col!r}, performance={perf_col!r}, "
            f"price={price_col!r}, type={type_col!r}"
        )

    monthly: list[tuple[date, float]] = []
    for year in YEARS:
        for month in range(1, 13):
            anchor = date(year, month, 1)
            eligible = [ratio for released, ratio in observations if released <= anchor]
            if eligible:
                monthly.append((anchor, max(eligible)))

    baseline = next(
        (value for anchor, value in monthly if anchor == date(2024, 1, 1)), None
    )
    if baseline is None or baseline <= 0:
        raise ReadinessError("cannot construct 2024-01 hardware efficiency baseline")

    return [
        {
            "month": anchor.isoformat()[:7],
            "frontier_performance_per_price_usd": ratio,
            "index_2024_01": ratio / baseline,
            "performance_column": perf_col,
            "price_column": price_col,
            "price_basis": price_basis,
            "calibration_label": CALIBRATION_LABEL,
        }
        for anchor, ratio in monthly
    ]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ReadinessError(f"refusing to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def prepare_readiness(
    tasks_path: Path,
    ai_price_csv: Path,
    epoch_hardware_csv: Path,
    output_root: Path,
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    sample = deterministic_humaneval_sample(tasks_path)
    matrix = build_microbacktest_matrix(sample)
    prices = filter_ai_price_history(ai_price_csv)
    hardware = hardware_efficiency_preview(epoch_hardware_csv)

    _write_json(output_root / "microbacktest_tasks.json", sample)
    _write_csv(output_root / "microbacktest_matrix.csv", matrix)
    _write_csv(output_root / "openai_anthropic_price_history.csv", prices)
    _write_csv(output_root / "hardware_efficiency_preview.csv", hardware)

    manifest = {
        "calibration_label": CALIBRATION_LABEL,
        "task_count": len(sample),
        "task_year_cells": len(matrix),
        "price_rows": len(prices),
        "hardware_months": len(hardware),
        "hardware_preview_price_basis": hardware[0]["price_basis"],
        "inputs": {
            "tasks_registry_sha256": sha256_file(tasks_path),
            "ai_price_index_sha256": sha256_file(ai_price_csv),
            "epoch_ml_hardware_sha256": sha256_file(epoch_hardware_csv),
        },
        "sources": source_metadata,
    }
    _write_json(output_root / "snapshot_metadata.json", manifest)

    gap_report = """# S1.2.5 Schema Gap Report

Status: GENERATED BEFORE S1.3 POPULATION

## Pricing registry gaps

Current S1.1 pricing records are insufficient for historical backtesting because point-in-time evidence needs `variation`, `effective_from`, `effective_to`, `source_kind`, `confidence`, `last_validated_at`, and first-party `source_url` in addition to token price. S1.3 should model these explicitly rather than collapsing a model to one current price record.

## Model/evidence registry gaps

S1.3 needs model public launch date plus an explicit historical snapshot availability/evidence status so that IF-01 can distinguish callable exact snapshots, archived observations, and `HISTORICAL_SNAPSHOT_UNAVAILABLE`. No successor/current-model substitution is allowed.

## External snapshot provenance gaps

External datasets require immutable revision/hash metadata. Hugging Face revision SHA can be pinned directly. Epoch's live CSV is mutable, so DACDM freezes exact bytes with retrieval time and SHA-256.

## Hardware registry gaps

The frozen Epoch live CSV exposes nominal `Release price (USD)` but does not expose the inflation-adjusted release-price series used in Epoch's published price-performance trend. Therefore the actual S1.2.5 Epoch snapshot is intentionally only a nominal-price readiness preview. The final IF-07 hardware deflator must separately encode its price-deflation method, source series, formula version, normalization month, interpolation method, and supported date bounds. S1.2.5 must not silently treat nominal release USD as constant 2024 USD.

## Confirmatory boundary

No S1.2.5 output may modify registered hypotheses, thresholds, kill criteria, contamination rules, bootstrap specification, model-tier rules, or the frozen Pilot 01 protocol.
"""
    (output_root / "schema_gap_report.md").write_text(gap_report, encoding="utf-8")
    return manifest
