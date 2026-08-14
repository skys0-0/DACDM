from __future__ import annotations

import csv
import json
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


CALIBRATION_LABEL = "EXPLORATORY_PIPELINE_CALIBRATION_NOT_CONFIRMATORY_EVIDENCE"
YEARS = (2024, 2025, 2026)


class PreInferenceAuditError(ValueError):
    """Raised when the S1.3.6 audit cannot be completed deterministically."""


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise PreInferenceAuditError(f"expected JSON array of objects: {path}")
    return raw


def _month_bounds(value: str) -> tuple[date, date]:
    try:
        year_text, month_text = value.split("-", maxsplit=1)
        year = int(year_text)
        month = int(month_text)
        last_day = monthrange(year, month)[1]
    except (ValueError, TypeError) as exc:
        raise PreInferenceAuditError(f"invalid cutoff month: {value!r}") from exc
    return date(year, month, 1), date(year, month, last_day)


def contamination_status(
    task_release_date: date, cutoff_evidence: dict[str, Any]
) -> tuple[str, str]:
    """Return a tri-state contamination result without inventing cutoff precision."""
    precision = cutoff_evidence.get("cutoff_precision")
    if precision == "day":
        raw_date = cutoff_evidence.get("claimed_cutoff_date")
        if not isinstance(raw_date, str):
            return "INDETERMINATE", "CUTOFF_DATE_MISSING"
        cutoff = date.fromisoformat(raw_date)
        if task_release_date < cutoff:
            return "EXCLUDED", "TASK_PRECEDES_TRAINING_CUTOFF"
        return "ELIGIBLE", "TASK_ON_OR_AFTER_TRAINING_CUTOFF"

    if precision == "month":
        raw_month = cutoff_evidence.get("claimed_cutoff_month")
        if not isinstance(raw_month, str):
            return "INDETERMINATE", "CUTOFF_MONTH_MISSING"
        first_day, last_day = _month_bounds(raw_month)
        if task_release_date < first_day:
            return "EXCLUDED", "TASK_PRECEDES_TRAINING_CUTOFF_MONTH"
        if task_release_date > last_day:
            return "ELIGIBLE", "TASK_AFTER_TRAINING_CUTOFF_MONTH"
        return "INDETERMINATE", "TASK_WITHIN_CUTOFF_MONTH_PRECISION_BOUNDARY"

    return "INDETERMINATE", "CUTOFF_PRECISION_UNKNOWN"


def _price_pair_overlaps_year(
    price_rows: list[dict[str, Any]], year: int, launch_date: date
) -> bool:
    year_start = max(date(year, 1, 1), launch_date)
    year_end_exclusive = date(year + 1, 1, 1)
    if year_start >= year_end_exclusive:
        return False

    by_variation: dict[str, list[tuple[date, date | None]]] = defaultdict(list)
    for row in price_rows:
        variation = row.get("variation")
        if variation not in {"input", "output"}:
            continue
        effective_from = date.fromisoformat(str(row["effective_from"]))
        effective_to = (
            date.fromisoformat(str(row["effective_to"]))
            if row.get("effective_to") is not None
            else None
        )
        by_variation[variation].append((effective_from, effective_to))

    for input_from, input_to in by_variation["input"]:
        for output_from, output_to in by_variation["output"]:
            start = max(year_start, input_from, output_from)
            ends = [year_end_exclusive]
            if input_to is not None:
                ends.append(input_to)
            if output_to is not None:
                ends.append(output_to)
            if start < min(ends):
                return True
    return False


def _snapshot_status(
    snapshot_rows: list[dict[str, Any]], model_id: str
) -> tuple[str, bool]:
    matches = [row for row in snapshot_rows if row.get("model_id") == model_id]
    if not matches:
        return "NO_SNAPSHOT_EVIDENCE", False
    matches.sort(key=lambda row: str(row.get("observation_date", "")), reverse=True)
    status = str(matches[0].get("availability_status", "unknown"))
    return status, status in {"callable_exact", "archived_observation"}


def _cutoff_for_model(
    model: dict[str, Any], cutoff_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    supported: list[dict[str, Any]] = []
    for evidence_id in model.get("training_cutoff_evidence_ids", []):
        evidence = cutoff_by_id.get(str(evidence_id))
        if evidence is not None and evidence.get("status") == "supported":
            supported.append(evidence)
    if len(supported) != 1:
        return None
    return supported[0]


def audit_preinference_admissibility(
    *,
    tasks_path: Path,
    sample_path: Path,
    models_path: Path,
    cutoff_path: Path,
    snapshot_path: Path,
    pricing_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    tasks = _load_json_array(tasks_path)
    sample = _load_json_array(sample_path)
    models = _load_json_array(models_path)
    cutoffs = _load_json_array(cutoff_path)
    snapshots = _load_json_array(snapshot_path)
    prices = _load_json_array(pricing_path)

    task_by_id = {str(row.get("task_id")): row for row in tasks}
    cutoff_by_id = {str(row.get("evidence_id")): row for row in cutoffs}
    price_by_id = {str(row.get("pricing_record_id")): row for row in prices}

    sample_ids = [str(row.get("task_id")) for row in sample]
    if len(sample_ids) != len(set(sample_ids)):
        raise PreInferenceAuditError("microbacktest sample contains duplicate task_id")
    missing_tasks = sorted(task_id for task_id in sample_ids if task_id not in task_by_id)
    if missing_tasks:
        raise PreInferenceAuditError(f"sample tasks missing from registry: {missing_tasks}")
    if not models:
        raise PreInferenceAuditError("canonical model registry is empty")

    detail_rows: list[dict[str, Any]] = []
    task_year_candidates: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)

    for task_id in sample_ids:
        task = task_by_id[task_id]
        raw_release = task.get("release_date")
        if not isinstance(raw_release, str):
            raise PreInferenceAuditError(f"task {task_id} has no exact release date")
        task_release = date.fromisoformat(raw_release)

        for model in models:
            model_id = str(model["model_id"])
            raw_launch = model.get("public_launch_date")
            if not isinstance(raw_launch, str):
                raise PreInferenceAuditError(f"model {model_id} has no public launch date")
            launch_date = date.fromisoformat(raw_launch)
            cutoff = _cutoff_for_model(model, cutoff_by_id)
            if cutoff is None:
                contamination, contamination_reason = (
                    "INDETERMINATE",
                    "SUPPORTED_CUTOFF_NOT_UNIQUELY_RESOLVED",
                )
            else:
                contamination, contamination_reason = contamination_status(
                    task_release, cutoff
                )

            snapshot_status, if01_available = _snapshot_status(snapshots, model_id)
            model_prices = [
                price_by_id[str(price_id)]
                for price_id in model.get("pricing_record_ids", [])
                if str(price_id) in price_by_id
            ]

            for year in YEARS:
                launch_overlaps_year = launch_date < date(year + 1, 1, 1)
                price_pair_available = _price_pair_overlaps_year(
                    model_prices, year, launch_date
                )
                admissible = (
                    contamination == "ELIGIBLE"
                    and launch_overlaps_year
                    and if01_available
                    and price_pair_available
                )

                if contamination == "EXCLUDED":
                    status = "CONTAMINATION_EXCLUDED"
                    reason = contamination_reason
                elif contamination == "INDETERMINATE":
                    status = "CONTAMINATION_INDETERMINATE"
                    reason = contamination_reason
                elif not launch_overlaps_year:
                    status = "MODEL_NOT_LAUNCHED_IN_YEAR"
                    reason = "PUBLIC_LAUNCH_AFTER_YEAR_END"
                elif not if01_available:
                    status = "IF01_HISTORICAL_SNAPSHOT_UNAVAILABLE"
                    reason = snapshot_status
                elif not price_pair_available:
                    status = "POINT_IN_TIME_PRICE_UNAVAILABLE"
                    reason = "NO_INPUT_OUTPUT_PRICE_PAIR_OVERLAPS_YEAR"
                else:
                    status = "ADMISSIBLE_FOR_INFERENCE"
                    reason = "ALL_PREINFERENCE_GATES_PASSED"

                row = {
                    "task_id": task_id,
                    "benchmark": task.get("benchmark"),
                    "task_release_date": task_release.isoformat(),
                    "year": year,
                    "model_id": model_id,
                    "model_launch_date": launch_date.isoformat(),
                    "contamination_status": contamination,
                    "contamination_reason": contamination_reason,
                    "if01_snapshot_status": snapshot_status,
                    "if01_available": if01_available,
                    "point_in_time_price_pair_available": price_pair_available,
                    "status": status,
                    "reason": reason,
                    "admissible": admissible,
                    "calibration_label": CALIBRATION_LABEL,
                }
                detail_rows.append(row)
                task_year_candidates[(task_id, year)].append(row)

    cell_rows: list[dict[str, Any]] = []
    for task_id in sample_ids:
        for year in YEARS:
            candidates = task_year_candidates[(task_id, year)]
            admissible_models = sorted(
                str(row["model_id"]) for row in candidates if row["admissible"]
            )
            all_contamination_excluded = all(
                row["status"] == "CONTAMINATION_EXCLUDED" for row in candidates
            )
            if admissible_models:
                status = "READY_FOR_PAID_INFERENCE"
                reason = "AT_LEAST_ONE_CANONICAL_MODEL_PASSES_ALL_GATES"
            elif all_contamination_excluded:
                status = "BLOCKED_CONTAMINATION_CURRENT_MODEL_REGISTRY"
                reason = "ALL_CANONICAL_MODELS_EXCLUDE_TASK_FOR_CONTAMINATION"
            else:
                status = "BLOCKED_NO_ADMISSIBLE_MODEL"
                reason = "NO_CANONICAL_MODEL_PASSES_ALL_PREINFERENCE_GATES"
            cell_rows.append(
                {
                    "task_id": task_id,
                    "year": year,
                    "status": status,
                    "reason": reason,
                    "admissible_model_count": len(admissible_models),
                    "admissible_models": ";".join(admissible_models),
                    "minimum_successful_cost_usd": "",
                    "calibration_label": CALIBRATION_LABEL,
                }
            )

    static_rows: list[dict[str, Any]] = []
    tasks_by_benchmark: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        tasks_by_benchmark[str(task.get("benchmark"))].append(task)

    for benchmark, benchmark_tasks in sorted(tasks_by_benchmark.items()):
        for model in models:
            model_id = str(model["model_id"])
            cutoff = _cutoff_for_model(model, cutoff_by_id)
            counts: Counter[str] = Counter()
            for task in benchmark_tasks:
                raw_release = task.get("release_date")
                if not isinstance(raw_release, str) or cutoff is None:
                    counts["INDETERMINATE"] += 1
                    continue
                result, _ = contamination_status(date.fromisoformat(raw_release), cutoff)
                counts[result] += 1
            total = len(benchmark_tasks)
            static_rows.append(
                {
                    "benchmark": benchmark,
                    "model_id": model_id,
                    "task_count": total,
                    "contamination_excluded": counts["EXCLUDED"],
                    "contamination_eligible": counts["ELIGIBLE"],
                    "contamination_indeterminate": counts["INDETERMINATE"],
                    "excluded_fraction": counts["EXCLUDED"] / total if total else 0.0,
                    "calibration_label": CALIBRATION_LABEL,
                }
            )

    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "model_task_year_admissibility.csv", detail_rows)
    _write_csv(output_root / "microbacktest_admissibility.csv", cell_rows)
    _write_csv(output_root / "static_task_contamination_summary.csv", static_rows)

    detail_counts = Counter(str(row["status"]) for row in detail_rows)
    cell_counts = Counter(str(row["status"]) for row in cell_rows)
    summary = {
        "calibration_label": CALIBRATION_LABEL,
        "model_count": len(models),
        "sample_task_count": len(sample_ids),
        "sample_task_year_cells": len(cell_rows),
        "model_task_year_pairs": len(detail_rows),
        "admissible_model_task_year_pairs": sum(bool(row["admissible"]) for row in detail_rows),
        "ready_for_paid_inference_cells": cell_counts["READY_FOR_PAID_INFERENCE"],
        "paid_inference_gate": (
            "OPEN" if cell_counts["READY_FOR_PAID_INFERENCE"] else "BLOCKED"
        ),
        "detail_status_counts": dict(sorted(detail_counts.items())),
        "cell_status_counts": dict(sorted(cell_counts.items())),
        "k4_status": "NOT_FORMALLY_EVALUATED_PREINFERENCE_AUDIT_ONLY",
        "k4_risk_note": (
            "The current static HumanEval/MBPP registry shows contamination exclusion "
            "against the currently verified model cutoffs. This is a pre-inference risk "
            "signal, not the registered final K4 decision because the protocol task universe "
            "also requires the timestamp-filtered LeetCode Hard set and the model registry "
            "is not yet complete."
        ),
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise PreInferenceAuditError(f"refusing to write empty audit CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
