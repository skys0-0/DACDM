from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .preinference import contamination_status
from .research import contamination_eligible


PHASE_LABEL = "S1.3.11_GLOBAL_TASK_UNIVERSE_AND_K4_DENOMINATOR_FREEZE"
NEXT_GATE = "S1.3.12_TEST_WINDOW_MODEL_SET_FREEZE_AND_FINAL_PREINFERENCE_K4_EVALUATION"


class K4UniverseError(ValueError):
    """Raised when the S1.3.11 universe cannot be frozen deterministically."""


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise K4UniverseError(f"expected JSON array of objects: {path}")
    return raw


def _load_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise K4UniverseError(f"expected JSON object: {path}")
    return raw


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git object identity


def _verify_authority(root: Path, interpretation: dict[str, Any]) -> list[dict[str, str]]:
    raw_evidence = interpretation.get("authority_evidence")
    if not isinstance(raw_evidence, list):
        raise K4UniverseError("interpretation authority_evidence must be a list")

    verified: list[dict[str, str]] = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            raise K4UniverseError("authority evidence entries must be objects")
        raw_path = item.get("path")
        expected_sha = item.get("git_blob_sha1")
        required_phrases = item.get("required_phrases")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            raise K4UniverseError("authority evidence path/SHA is malformed")
        if not isinstance(required_phrases, list) or not all(
            isinstance(value, str) for value in required_phrases
        ):
            raise K4UniverseError(f"authority required_phrases malformed: {raw_path}")

        path = root / raw_path
        if not path.is_file():
            raise K4UniverseError(f"authority source missing: {path}")
        actual_sha = _git_blob_sha1(path)
        if actual_sha != expected_sha:
            raise K4UniverseError(
                f"authority source blob drift: {raw_path}: {actual_sha} != {expected_sha}"
            )
        text = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in text:
                raise K4UniverseError(f"authority phrase missing from {raw_path}: {phrase}")
        verified.append({"path": raw_path, "git_blob_sha1": actual_sha})
    return verified


def _supported_cutoff(
    model: dict[str, Any], cutoff_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    evidence_ids = model.get("training_cutoff_evidence_ids")
    if not isinstance(evidence_ids, list):
        return None
    supported: list[dict[str, Any]] = []
    for raw_id in evidence_ids:
        evidence = cutoff_by_id.get(str(raw_id))
        if evidence is not None and evidence.get("status") == "supported":
            supported.append(evidence)
    if len(supported) > 1:
        raise K4UniverseError(f"multiple supported cutoffs for {model.get('model_id')}")
    return supported[0] if supported else None


def model_contamination_status(
    *,
    task_release_date: date,
    model: dict[str, Any],
    cutoff_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    cutoff = _supported_cutoff(model, cutoff_by_id)
    if cutoff is not None and cutoff.get("cutoff_precision") in {"day", "month"}:
        return contamination_status(task_release_date, cutoff)

    raw_launch = model.get("public_launch_date")
    if not isinstance(raw_launch, str):
        return "INDETERMINATE", "MODEL_LAUNCH_DATE_MISSING_FOR_UNKNOWN_CUTOFF_FALLBACK"
    eligible, reason = contamination_eligible(
        task_release_date=task_release_date,
        training_cutoff_date=None,
        model_launch_date=date.fromisoformat(raw_launch),
    )
    return ("ELIGIBLE" if eligible else "EXCLUDED"), reason


def global_contamination_status(
    *,
    task_release_date: date,
    models: list[dict[str, Any]],
    cutoff_by_id: dict[str, dict[str, Any]],
) -> str:
    if not models:
        return "UNRESOLVED_MODEL_SET"
    statuses = [
        model_contamination_status(
            task_release_date=task_release_date,
            model=model,
            cutoff_by_id=cutoff_by_id,
        )[0]
        for model in models
    ]
    if "EXCLUDED" in statuses:
        return "EXCLUDED"
    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if all(status == "ELIGIBLE" for status in statuses):
        return "ELIGIBLE"
    raise K4UniverseError(f"unexpected per-model contamination statuses: {statuses}")


def _component_expected_counts(interpretation: dict[str, Any]) -> dict[str, int]:
    raw_components = interpretation.get("denominator_components")
    if not isinstance(raw_components, list):
        raise K4UniverseError("denominator_components must be a list")
    result: dict[str, int] = {}
    for item in raw_components:
        if not isinstance(item, dict):
            raise K4UniverseError("denominator component must be an object")
        source = item.get("source")
        expected_count = item.get("expected_count")
        if not isinstance(source, str) or not isinstance(expected_count, int):
            raise K4UniverseError("denominator component source/count malformed")
        result[source] = expected_count
    return result


def freeze_k4_universe(
    *,
    root: Path,
    interpretation_path: Path,
    static_tasks_path: Path,
    leetcode_candidates_path: Path,
    models_path: Path,
    cutoffs_path: Path,
    s1_3_10_summary_path: Path,
    s1_3_10_validation_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    interpretation = _load_object(interpretation_path)
    authority_verified = _verify_authority(root, interpretation)
    static_tasks = _load_array(static_tasks_path)
    leetcode_candidates = _load_array(leetcode_candidates_path)
    models = _load_array(models_path)
    cutoffs = _load_array(cutoffs_path)
    prior_summary = _load_object(s1_3_10_summary_path)
    prior_validation = _load_array(s1_3_10_validation_path)

    if prior_summary.get("model_results_inspected") is not False:
        raise K4UniverseError("S1.3.11 must run before model results are inspected")
    if prior_summary.get("paid_inference_permitted") is not False:
        raise K4UniverseError("S1.3.10 paid-inference gate was not closed")
    if any(row.get("model_results_inspected") is not False for row in prior_validation):
        raise K4UniverseError("S1.3.10 task validation contains inspected model results")

    static_selected = [
        row for row in static_tasks if row.get("benchmark") in {"humaneval", "mbpp"}
    ]
    static_counts = Counter(str(row.get("benchmark")) for row in static_selected)
    hard_candidates = [row for row in leetcode_candidates if row.get("difficulty") == "Hard"]

    actual_components = {
        "humaneval": static_counts["humaneval"],
        "mbpp": static_counts["mbpp"],
        "leetcode_weekly_hard": len(hard_candidates),
    }
    expected_components = _component_expected_counts(interpretation)
    if actual_components != expected_components:
        raise K4UniverseError(
            f"denominator component drift: actual={actual_components}, expected={expected_components}"
        )

    expected_denominator = interpretation.get("expected_denominator_count")
    if not isinstance(expected_denominator, int):
        raise K4UniverseError("expected_denominator_count must be an integer")

    raw_task_rows: list[dict[str, Any]] = []
    for row in static_selected:
        task_id = row.get("task_id")
        release_date = row.get("release_date")
        benchmark = row.get("benchmark")
        if not all(isinstance(value, str) for value in (task_id, release_date, benchmark)):
            raise K4UniverseError("static task lacks canonical id/release date/benchmark")
        raw_task_rows.append(
            {
                "task_id": task_id,
                "source": benchmark,
                "release_date": release_date,
                "oracle_status_at_s1_3_11": "BENCHMARK_CANONICAL_ORACLE",
            }
        )

    validation_by_id = {
        str(row.get("canonical_task_id")): row for row in prior_validation
    }
    for row in hard_candidates:
        task_id = row.get("canonical_task_id")
        release_date = row.get("release_date")
        if not isinstance(task_id, str) or not isinstance(release_date, str):
            raise K4UniverseError("LeetCode candidate lacks canonical id/release date")
        validation = validation_by_id.get(task_id)
        raw_task_rows.append(
            {
                "task_id": task_id,
                "source": "leetcode_weekly_hard",
                "release_date": release_date,
                "oracle_status_at_s1_3_11": (
                    str(validation.get("if09_status"))
                    if validation is not None
                    else "NOT_REGISTERED_FOR_S1_3_10_ORACLE_VALIDATION"
                ),
            }
        )

    task_ids = [str(row["task_id"]) for row in raw_task_rows]
    if len(task_ids) != len(set(task_ids)):
        raise K4UniverseError("K4 denominator contains duplicate canonical task ids")
    if len(task_ids) != expected_denominator:
        raise K4UniverseError(
            f"K4 denominator count drift: {len(task_ids)} != {expected_denominator}"
        )

    cutoff_by_id = {str(row.get("evidence_id")): row for row in cutoffs}
    if not models:
        raise K4UniverseError("model evidence registry is empty")
    enabled_models = [row for row in models if row.get("enabled_for_pilot") is True]

    current_counts: Counter[str] = Counter()
    formal_counts: Counter[str] = Counter()
    universe_rows: list[dict[str, Any]] = []
    for row in raw_task_rows:
        release = date.fromisoformat(str(row["release_date"]))
        current_status = global_contamination_status(
            task_release_date=release,
            models=models,
            cutoff_by_id=cutoff_by_id,
        )
        formal_status = global_contamination_status(
            task_release_date=release,
            models=enabled_models,
            cutoff_by_id=cutoff_by_id,
        )
        current_counts[current_status] += 1
        formal_counts[formal_status] += 1
        universe_rows.append(
            {
                **row,
                "denominator_role": "K4_PRE_CONTAMINATION_REGISTERED_TASK_UNIVERSE",
                "current_evidence_registry_contamination_status": current_status,
                "formal_test_window_contamination_status": formal_status,
            }
        )

    universe_rows.sort(key=lambda row: str(row["task_id"]))
    threshold_raw = interpretation.get("k4_threshold")
    if not isinstance(threshold_raw, (int, float)):
        raise K4UniverseError("k4_threshold must be numeric")
    threshold = float(threshold_raw)

    current_excluded = current_counts["EXCLUDED"]
    current_indeterminate = current_counts["INDETERMINATE"]
    current_fraction = current_excluded / expected_denominator
    conservative_current_fraction = (
        current_excluded + current_indeterminate
    ) / expected_denominator
    static_current_excluded = sum(
        1
        for row in universe_rows
        if row["source"] in {"humaneval", "mbpp"}
        and row["current_evidence_registry_contamination_status"] == "EXCLUDED"
    )
    static_best_case_fraction = static_current_excluded / expected_denominator

    if not enabled_models:
        formal_k4_status = "K4_UNRESOLVED_MODEL_SET"
        formal_excluded: int | None = None
        formal_indeterminate: int | None = None
        formal_fraction: float | None = None
        formal_triggered: bool | None = None
    else:
        formal_excluded = formal_counts["EXCLUDED"]
        formal_indeterminate = formal_counts["INDETERMINATE"]
        formal_fraction = formal_excluded / expected_denominator
        if formal_indeterminate:
            formal_k4_status = "K4_UNRESOLVED_CONTAMINATION_INDETERMINATE"
            formal_triggered = None
        else:
            formal_triggered = formal_fraction > threshold
            formal_k4_status = "K4_TRIGGERED" if formal_triggered else "K4_NOT_TRIGGERED"

    universe_output = {
        "phase_label": PHASE_LABEL,
        "interpretation_id": interpretation.get("interpretation_id"),
        "denominator_semantics": interpretation["selected_interpretation"][
            "denominator_semantics"
        ],
        "denominator_count": expected_denominator,
        "component_counts": actual_components,
        "authority_verified": authority_verified,
        "tasks": universe_rows,
    }

    evaluation = {
        "phase_label": PHASE_LABEL,
        "interpretation_id": interpretation.get("interpretation_id"),
        "threshold": threshold,
        "denominator_count": expected_denominator,
        "denominator_semantics": interpretation["selected_interpretation"][
            "denominator_semantics"
        ],
        "global_contamination_semantics": interpretation["selected_interpretation"][
            "contamination_scope"
        ],
        "enabled_test_window_model_ids": sorted(
            str(row.get("model_id")) for row in enabled_models
        ),
        "formal_k4_status": formal_k4_status,
        "formal_excluded_count": formal_excluded,
        "formal_indeterminate_count": formal_indeterminate,
        "formal_excluded_fraction": formal_fraction,
        "formal_k4_triggered": formal_triggered,
        "current_evidence_registry_sensitivity": {
            "model_ids": sorted(str(row.get("model_id")) for row in models),
            "excluded_count": current_excluded,
            "eligible_count": current_counts["ELIGIBLE"],
            "indeterminate_count": current_indeterminate,
            "excluded_fraction": current_fraction,
            "conservative_fraction_counting_indeterminate_as_excluded": (
                conservative_current_fraction
            ),
            "would_trigger_k4_if_this_model_set_were_frozen": current_fraction > threshold,
            "static_humaneval_mbpp_excluded_count": static_current_excluded,
            "best_case_fraction_if_all_leetcode_candidates_were_clean": (
                static_best_case_fraction
            ),
        },
        "oracle_insufficiency_counted_in_k4_numerator": False,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": NEXT_GATE,
    }

    summary = {
        "phase_label": PHASE_LABEL,
        "status": "K4_DENOMINATOR_FROZEN_FORMAL_K4_UNRESOLVED_MODEL_SET",
        "interpretation_id": interpretation.get("interpretation_id"),
        "denominator_semantics": interpretation["selected_interpretation"][
            "denominator_semantics"
        ],
        "denominator_count": expected_denominator,
        "component_counts": actual_components,
        "k4_threshold": threshold,
        "enabled_test_window_model_count": len(enabled_models),
        "formal_k4_status": formal_k4_status,
        "current_evidence_model_count": len(models),
        "current_evidence_excluded_count": current_excluded,
        "current_evidence_eligible_count": current_counts["ELIGIBLE"],
        "current_evidence_indeterminate_count": current_indeterminate,
        "current_evidence_excluded_fraction": current_fraction,
        "current_evidence_would_trigger_k4": current_fraction > threshold,
        "best_case_fraction_if_all_leetcode_candidates_were_clean": static_best_case_fraction,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": NEXT_GATE,
    }

    _write_json(output_root / "task_universe.json", universe_output)
    _write_json(output_root / "k4_evaluation.json", evaluation)
    _write_json(output_root / "summary.json", summary)
    return summary
