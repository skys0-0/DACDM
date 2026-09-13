from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .k4_universe import global_contamination_status


PHASE_LABEL = "S1.3.12_TEST_WINDOW_MODEL_SET_FREEZE_AND_FINAL_PREINFERENCE_K4_EVALUATION"
NEXT_GATE = "S1.3.13_PILOT_01_PREINFERENCE_TERMINATION_PACKAGE"


class K4FinalError(ValueError):
    """Raised when the S1.3.12 final K4 evaluation cannot be reproduced."""


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise K4FinalError(f"expected JSON array of objects: {path}")
    return raw


def _load_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise K4FinalError(f"expected JSON object: {path}")
    return raw


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def decide_k4_from_bounds(
    *, excluded_count: int, indeterminate_count: int, denominator_count: int, threshold: float
) -> tuple[str, bool | None, float, float]:
    """Decide K4 using strict and conservative exclusion bounds.

    A known exclusion share above the frozen threshold is sufficient to trigger K4 even
    when additional tasks remain indeterminate. Conversely, if even the conservative
    upper bound is at or below the threshold, K4 is not triggered. Only the interval
    crossing the threshold remains unresolved.
    """
    if denominator_count <= 0:
        raise K4FinalError("denominator_count must be positive")
    if excluded_count < 0 or indeterminate_count < 0:
        raise K4FinalError("K4 counts cannot be negative")
    if excluded_count + indeterminate_count > denominator_count:
        raise K4FinalError("excluded plus indeterminate exceeds denominator")
    if not 0 <= threshold <= 1:
        raise K4FinalError("threshold must be in [0, 1]")

    strict_fraction = excluded_count / denominator_count
    conservative_fraction = (excluded_count + indeterminate_count) / denominator_count
    if strict_fraction > threshold:
        return "K4_TRIGGERED", True, strict_fraction, conservative_fraction
    if conservative_fraction <= threshold:
        return "K4_NOT_TRIGGERED", False, strict_fraction, conservative_fraction
    return (
        "K4_UNRESOLVED_CONTAMINATION_INDETERMINATE",
        None,
        strict_fraction,
        conservative_fraction,
    )


def freeze_final_preinference_k4(
    *,
    model_set_path: Path,
    models_path: Path,
    cutoffs_path: Path,
    s1_3_11_task_universe_path: Path,
    s1_3_11_summary_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    model_set = _load_object(model_set_path)
    models = _load_array(models_path)
    cutoffs = _load_array(cutoffs_path)
    prior_universe = _load_object(s1_3_11_task_universe_path)
    prior_summary = _load_object(s1_3_11_summary_path)

    if prior_summary.get("phase_label") != "S1.3.11_GLOBAL_TASK_UNIVERSE_AND_K4_DENOMINATOR_FREEZE":
        raise K4FinalError("S1.3.11 summary phase is not the required predecessor")
    if prior_summary.get("model_results_inspected") is not False:
        raise K4FinalError("S1.3.12 must run before model results are inspected")
    if prior_summary.get("paid_inference_permitted") is not False:
        raise K4FinalError("S1.3.11 paid-inference gate was not closed")
    if prior_summary.get("formal_k4_status") != "K4_UNRESOLVED_MODEL_SET":
        raise K4FinalError("S1.3.11 did not leave K4 unresolved solely on model-set freeze")

    if model_set.get("model_results_inspected") is not False:
        raise K4FinalError("test-window model-set registry must be frozen before results")
    if model_set.get("paid_inference_permitted") is not False:
        raise K4FinalError("test-window model-set registry cannot permit paid inference")
    if model_set.get("selection_rule") != "ALL_CANONICAL_MODELS_PRESENT_BEFORE_S1_3_12":
        raise K4FinalError("unexpected S1.3.12 model selection rule")

    selected_raw = model_set.get("selected_model_ids")
    expected_model_count = model_set.get("expected_model_count")
    if not isinstance(selected_raw, list) or not all(isinstance(value, str) for value in selected_raw):
        raise K4FinalError("selected_model_ids must be a list of strings")
    if not isinstance(expected_model_count, int):
        raise K4FinalError("expected_model_count must be an integer")
    selected_ids = sorted(selected_raw)
    if len(selected_ids) != len(set(selected_ids)):
        raise K4FinalError("selected_model_ids contains duplicates")
    if len(selected_ids) != expected_model_count:
        raise K4FinalError("selected model count does not match frozen expectation")

    model_by_id = {str(row.get("model_id")): row for row in models}
    canonical_ids = sorted(model_by_id)
    if selected_ids != canonical_ids:
        raise K4FinalError(
            "S1.3.12 selection rule requires every canonical model present before freeze"
        )
    selected_models = [model_by_id[model_id] for model_id in selected_ids]

    cutoff_by_id = {str(row.get("evidence_id")): row for row in cutoffs}
    for model in selected_models:
        if model.get("training_cutoff_status") != "supported":
            raise K4FinalError(f"selected model lacks supported cutoff: {model.get('model_id')}")

    tasks_raw = prior_universe.get("tasks")
    denominator_count = prior_universe.get("denominator_count")
    if not isinstance(tasks_raw, list) or not all(isinstance(row, dict) for row in tasks_raw):
        raise K4FinalError("S1.3.11 task universe is malformed")
    if not isinstance(denominator_count, int):
        raise K4FinalError("S1.3.11 denominator count is malformed")
    if len(tasks_raw) != denominator_count:
        raise K4FinalError("S1.3.11 task universe count drift")

    counts: Counter[str] = Counter()
    task_statuses: list[dict[str, Any]] = []
    for row in tasks_raw:
        task_id = row.get("task_id")
        release_raw = row.get("release_date")
        source = row.get("source")
        if not isinstance(task_id, str) or not isinstance(release_raw, str):
            raise K4FinalError("task universe row lacks canonical id or release date")
        status = global_contamination_status(
            task_release_date=date.fromisoformat(release_raw),
            models=selected_models,
            cutoff_by_id=cutoff_by_id,
        )
        counts[status] += 1
        task_statuses.append(
            {
                "task_id": task_id,
                "source": source,
                "release_date": release_raw,
                "final_test_window_contamination_status": status,
            }
        )

    threshold_raw = model_set.get("k4_threshold")
    if not isinstance(threshold_raw, (int, float)):
        raise K4FinalError("frozen K4 threshold must be numeric")
    threshold = float(threshold_raw)
    prior_threshold = prior_summary.get("k4_threshold")
    if not isinstance(prior_threshold, (int, float)) or float(prior_threshold) != threshold:
        raise K4FinalError("K4 threshold drift between S1.3.11 and S1.3.12")

    k4_status, k4_triggered, strict_fraction, conservative_fraction = decide_k4_from_bounds(
        excluded_count=counts["EXCLUDED"],
        indeterminate_count=counts["INDETERMINATE"],
        denominator_count=denominator_count,
        threshold=threshold,
    )

    termination_required = k4_triggered is True
    model_set_evaluation = {
        "phase_label": PHASE_LABEL,
        "model_set_id": model_set.get("model_set_id"),
        "selection_rule": model_set.get("selection_rule"),
        "selected_model_ids": selected_ids,
        "selected_model_count": len(selected_models),
        "selection_matches_all_preexisting_canonical_models": selected_ids == canonical_ids,
        "model_set_expansion_monotonicity": (
            "Under the frozen global ANY-model contamination rule, adding another model can "
            "only preserve or increase the set of excluded tasks; it cannot make a task already "
            "excluded by a selected model eligible."
        ),
        "model_results_inspected": False,
        "paid_inference_permitted": False,
    }

    final_evaluation = {
        "phase_label": PHASE_LABEL,
        "model_set_id": model_set.get("model_set_id"),
        "denominator_semantics": prior_universe.get("denominator_semantics"),
        "denominator_count": denominator_count,
        "threshold": threshold,
        "excluded_count": counts["EXCLUDED"],
        "eligible_count": counts["ELIGIBLE"],
        "indeterminate_count": counts["INDETERMINATE"],
        "strict_known_exclusion_fraction": strict_fraction,
        "conservative_fraction_counting_indeterminate_as_excluded": conservative_fraction,
        "formal_k4_status": k4_status,
        "formal_k4_triggered": k4_triggered,
        "indeterminate_tasks_needed_to_trigger": False if k4_triggered else None,
        "oracle_insufficiency_counted_in_k4_numerator": False,
        "termination_required_by_preregistered_k4": termination_required,
        "interpretive_boundary": (
            "K4 is a preregistered Pilot 01 kill criterion based on contamination exclusion. "
            "This pre-inference termination is not a model-performance test of H2/H4."
        ),
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "task_statuses": sorted(task_statuses, key=lambda item: str(item["task_id"])),
    }

    if termination_required:
        status = "PILOT01_PREINFERENCE_TERMINATION_REQUIRED_K4_TRIGGERED"
        next_gate = NEXT_GATE
    elif k4_triggered is False:
        status = "K4_NOT_TRIGGERED_OTHER_GLOBAL_GATES_STILL_REQUIRED"
        next_gate = "S1.4_COMPLETE_MODEL_AND_EXECUTION_READINESS"
    else:
        status = "K4_UNRESOLVED_CONTAMINATION_INDETERMINATE"
        next_gate = "S1.3.12A_RESOLVE_CONTAMINATION_BOUNDARY_EVIDENCE"

    summary = {
        "phase_label": PHASE_LABEL,
        "status": status,
        "model_set_id": model_set.get("model_set_id"),
        "selected_model_count": len(selected_models),
        "denominator_count": denominator_count,
        "k4_threshold": threshold,
        "excluded_count": counts["EXCLUDED"],
        "eligible_count": counts["ELIGIBLE"],
        "indeterminate_count": counts["INDETERMINATE"],
        "strict_known_exclusion_fraction": strict_fraction,
        "conservative_exclusion_fraction": conservative_fraction,
        "formal_k4_status": k4_status,
        "formal_k4_triggered": k4_triggered,
        "termination_required_by_preregistered_k4": termination_required,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": next_gate,
    }

    _write_json(output_root / "model_set_evaluation.json", model_set_evaluation)
    _write_json(output_root / "k4_final_evaluation.json", final_evaluation)
    _write_json(output_root / "summary.json", summary)
    return summary
