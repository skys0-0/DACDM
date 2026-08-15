from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PHASE_LABEL = "S1.3.13_PILOT_01_PREINFERENCE_TERMINATION_PACKAGE"
PACKAGE_VERSION = "1.0"
REPORT_TITLE = (
    "DACDM Pilot 01: Pre-Inference Termination under a Preregistered "
    "Contamination Criterion"
)


class TerminationPackageError(ValueError):
    """Raised when the Pilot 01 termination package cannot be built safely."""


def _load_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TerminationPackageError(f"expected JSON object: {path}")
    return raw


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_final_k4(summary: dict[str, Any], evaluation: dict[str, Any]) -> None:
    required_summary = {
        "formal_k4_status": "K4_TRIGGERED",
        "formal_k4_triggered": True,
        "termination_required_by_preregistered_k4": True,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "denominator_count": 1301,
        "excluded_count": 1165,
        "eligible_count": 132,
        "indeterminate_count": 4,
    }
    for key, expected in required_summary.items():
        if summary.get(key) != expected:
            raise TerminationPackageError(
                f"S1.3.12 summary mismatch for {key}: {summary.get(key)!r} != {expected!r}"
            )

    threshold = summary.get("k4_threshold")
    strict_fraction = summary.get("strict_known_exclusion_fraction")
    if not isinstance(threshold, (int, float)) or not isinstance(
        strict_fraction, (int, float)
    ):
        raise TerminationPackageError("K4 threshold/fraction must be numeric")
    if float(strict_fraction) <= float(threshold):
        raise TerminationPackageError("strict known exclusion fraction does not trigger K4")

    if evaluation.get("formal_k4_status") != "K4_TRIGGERED":
        raise TerminationPackageError("final evaluation does not report K4_TRIGGERED")
    if evaluation.get("model_results_inspected") is not False:
        raise TerminationPackageError("termination package requires zero inspected model results")
    if evaluation.get("paid_inference_permitted") is not False:
        raise TerminationPackageError("termination package requires paid inference to remain closed")
    if evaluation.get("oracle_insufficiency_counted_in_k4_numerator") is not False:
        raise TerminationPackageError("oracle insufficiency must not enter K4 numerator")


def _input_manifest(root: Path, relative_paths: list[str]) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for relative_path in relative_paths:
        path = root / relative_path
        if not path.is_file():
            raise TerminationPackageError(f"package input missing: {relative_path}")
        rows.append(
            {
                "path": relative_path,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _report_markdown(
    *,
    summary: dict[str, Any],
    s1_3_10_summary: dict[str, Any],
    model_set: dict[str, Any],
    source_commit: str,
) -> str:
    strict_pct = 100.0 * float(summary["strict_known_exclusion_fraction"])
    conservative_pct = 100.0 * float(summary["conservative_exclusion_fraction"])
    selected_models = "\n".join(
        f"- `{model_id}`" for model_id in model_set["selected_model_ids"]
    )
    if09_ready = s1_3_10_summary.get("if09_ready_task_count", "NA")
    if09_not_ready = s1_3_10_summary.get("if09_not_ready_task_count", "NA")

    return f"""# {REPORT_TITLE}

**Package version:** {PACKAGE_VERSION}  
**Phase:** `{PHASE_LABEL}`  
**Closure date:** 2026-08-15  
**Conceptual originator:** CHAU HUNG SAN / 辛秋雄  
**Research status:** Preregistered pre-inference termination / methodological result  
**Source commit used to generate this package:** `{source_commit}`

## Abstract

DACDM Pilot 01 was preregistered to test Complexity Migration (H2) and Compression Beyond
Hardware (H4) in code generation. Before confirmatory model inference, the research pipeline
applied the frozen contamination rule and the preregistered K4 kill criterion. The K4
denominator was frozen before the final decision as the pre-contamination registered task
universe: 164 HumanEval tasks, 974 MBPP tasks, and 163 LeetCode Weekly Contest Hard metadata
candidates, for 1,301 unique tasks. With the non-outcome-selected test-window anchor model set,
1,165 tasks were known contamination exclusions, 132 were eligible, and 4 remained
indeterminate because of month-precision cutoff boundaries. The strict known exclusion share
was {strict_pct:.4f}%, exceeding the frozen 30% K4 threshold without counting any indeterminate
task as excluded. Under the frozen protocol, K4 is therefore triggered and Pilot 01 must stop
before paid confirmatory inference. This is a protocol-defined falsification/termination of
Pilot 01. It is not a model-performance refutation of H2 or H4 because no confirmatory model
performance results were collected or inspected.

## 1. Governing preregistration

The frozen Pilot 01 protocol states that a task is excluded when its release date precedes the
training cutoff date of any model used in the test window. It also defines K4 as triggered when
more than 30% of tasks in the dataset are flagged for contamination and excluded. The protocol
states that the pilot is considered a falsification if any registered kill criterion is
observed, and expressly forbids post-hoc changes to the kill criteria or minimum-effect
threshold.

The protocol remains unchanged. This report records the consequence of applying it.

## 2. Pre-inference decision sequence

The implementation separated denominator definition from the final numeric K4 decision.
S1.3.11 froze the denominator as the pre-contamination registered task universe so that tasks
could not disappear from the denominator merely because they were contaminated or later failed
an oracle gate. S1.3.12 then froze every canonical model already present in the validated model
registry before that phase as the test-window anchor set. No model was added or removed based on
the K4 result.

S1.3.10 had previously completed task-level IF-09 oracle validation for the registered external
LeetCode suites: {if09_ready} tasks were task-level IF-09 ready and {if09_not_ready} were not.
Those oracle results do not alter the K4 denominator or numerator. Oracle insufficiency is not
counted as contamination.

## 3. Frozen test-window anchor model set

{selected_models}

Selection rule: `{model_set['selection_rule']}`.

The anchor set is sufficient for the K4 decision because the registered contamination rule uses
an ANY-model predicate. Once a task is excluded because of one selected model's cutoff, adding
another model cannot make that task eligible again. Therefore a strict exclusion share already
above 30% cannot be rescued by later tier expansion.

## 4. Final K4 result

| Quantity | Frozen result |
|---|---:|
| Denominator | {summary['denominator_count']} |
| Known excluded | {summary['excluded_count']} |
| Eligible | {summary['eligible_count']} |
| Indeterminate | {summary['indeterminate_count']} |
| Strict known exclusion share | {strict_pct:.4f}% |
| Conservative share incl. indeterminate | {conservative_pct:.4f}% |
| K4 threshold | {100.0 * float(summary['k4_threshold']):.2f}% |
| Formal K4 status | **K4_TRIGGERED** |

The four indeterminate tasks are not needed for the decision. The known-exclusion share alone
exceeds the registered threshold.

## 5. Scientific interpretation boundary

Two statements must be reported together.

First, **the frozen Pilot 01 protocol classifies this outcome as a falsification condition and
requires termination because K4 is triggered**. The project must not weaken or redefine K4 after
seeing this result.

Second, **this outcome is not an empirical model-performance test of H2 or H4**. No confirmatory
model performance results were inspected, K1-K3 were not evaluated, no registered fixed-effects
model was estimated, no confirmatory CCR was calculated, and no paid model inference was run.
The substantive mechanism therefore remains untested by Pilot 01 performance data.

This report uses the phrase **protocol-defined falsification / pre-inference termination** to
preserve both facts without converting a benchmark-admissibility failure into evidence about
model performance that was never observed.

## 6. Frozen protocol documentation defect

The mandatory contamination policy says that release dates **preceding** a model training cutoff
are excluded. The protocol Data Dictionary later contains the opposite sign in the short field
description for `exclude_contamination`. The implementation did not silently amend the frozen
protocol. S1.3.11 recorded the authority hierarchy and applied the mandatory policy together with
the SDD/Implementation Freeze precedence rule that the frozen protocol governs. The conflicting
Data Dictionary phrase is retained as a documented defect and does not change the K4 result.

## 7. Why Pilot 01 is not being rescued

No post-hoc denominator change is made. No contaminated task is removed before computing the
contamination share. No post-oracle survivor set is substituted for the registered task universe.
The 30% threshold is unchanged. The test-window anchor models were selected by a rule fixed
without reference to model outcomes, and the four cutoff-boundary indeterminate tasks are not
needed to trigger K4.

## 8. Research consequence

Pilot 01 closes at the pre-inference stage. Confirmatory model inference, K1-K3 evaluation,
registered regression, confirmatory CCR estimation, and H4 hardware-adjusted performance testing
are not performed under this pilot. The original DACDM Conceptual Framework and the frozen Pilot
01 Protocol remain preserved as historical research objects.

A future Pilot 02, if created, must be separately preregistered and should use a timestamped,
contamination-resistant task stream designed around contemporary/post-cutoff tasks. It must not
be represented as a continuation that retroactively changes Pilot 01.

## 9. Publication classification

Recommended classification: **methodological / negative research report**.

Recommended title: **{REPORT_TITLE}**.

This package is prepared for review and later independent Zenodo publication. Generating this
package does not itself publish a Zenodo record or assign a new DOI.

## 10. Reproducibility and provenance

Machine-readable closure status, K4 assessment, source hashes, model-set identity, and package
inputs are stored beside this report in the S1.3.13 publication package. The generator refuses
to build the package unless S1.3.12 reports `K4_TRIGGERED`, confirms that no model results were
inspected, and keeps paid inference disabled.
"""


def _readme_markdown(source_commit: str) -> str:
    return f"""# DACDM Pilot 01 — Pre-Inference Termination Package v{PACKAGE_VERSION}

This directory packages the preregistered Pilot 01 closure after K4 contamination exclusion was
formally triggered before confirmatory model inference.

Primary report: `DACDM_Pilot_01_PreInference_Termination_Report_v1.0.md`

Machine-readable files:

- `K4_FINAL_ASSESSMENT.json` — closure criterion and final counts.
- `REPRODUCIBILITY_MANIFEST.json` — source hashes and frozen provenance.
- `ZENODO_METADATA_DRAFT.json` — draft publication metadata; not an API submission record.
- `PACKAGE_STATUS.json` — explicit publication/readiness state.

The package is a methodological/negative result. It records a **protocol-defined falsification /
pre-inference termination** while explicitly stating that H2/H4 did not receive a confirmatory
model-performance test in Pilot 01.

Generated from source commit `{source_commit}`. No paid model inference is performed by this
package build, and no Zenodo publication is performed automatically.
"""


def build_termination_package(*, root: Path, output_root: Path, source_commit: str) -> dict[str, Any]:
    if len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit):
        raise TerminationPackageError("source_commit must be a 40-character lowercase Git SHA")

    summary_path = root / "backtest/s1_3_12/summary.json"
    evaluation_path = root / "backtest/s1_3_12/k4_final_evaluation.json"
    model_set_path = root / "registries/test_window_model_set_v1.json"
    s1_3_10_summary_path = root / "backtest/s1_3_10/summary.json"

    summary = _load_object(summary_path)
    evaluation = _load_object(evaluation_path)
    model_set = _load_object(model_set_path)
    s1_3_10_summary = _load_object(s1_3_10_summary_path)
    validate_final_k4(summary, evaluation)

    input_paths = [
        "../protocols/DACDM_Pilot_01_Protocol_v1.0.md",
        "DACDM_Pilot_01_Implementation_Freeze_v1.0.md",
        "DACDM_Pilot_01_SDD_v1.0.md",
        "registries/k4_denominator_interpretation.json",
        "registries/test_window_model_set_v1.json",
        "backtest/s1_3_10/summary.json",
        "backtest/s1_3_11/summary.json",
        "backtest/s1_3_12/summary.json",
        "backtest/s1_3_12/model_set_evaluation.json",
        "backtest/s1_3_12/k4_final_evaluation.json",
    ]
    inputs = _input_manifest(root, input_paths)

    strict_fraction = float(summary["strict_known_exclusion_fraction"])
    conservative_fraction = float(summary["conservative_exclusion_fraction"])
    assessment = {
        "phase_label": PHASE_LABEL,
        "package_version": PACKAGE_VERSION,
        "closure_date": "2026-08-15",
        "pilot": "DACDM Pilot 01 — Code Generation Complexity Compression",
        "protocol_defined_outcome": "FALSIFICATION_CONDITION_TRIGGERED_K4",
        "operational_outcome": "PREINFERENCE_TERMINATION_REQUIRED",
        "formal_k4_status": "K4_TRIGGERED",
        "k4_threshold": float(summary["k4_threshold"]),
        "denominator_semantics": "PRE_CONTAMINATION_REGISTERED_TASK_UNIVERSE",
        "denominator_count": int(summary["denominator_count"]),
        "excluded_count": int(summary["excluded_count"]),
        "eligible_count": int(summary["eligible_count"]),
        "indeterminate_count": int(summary["indeterminate_count"]),
        "strict_known_exclusion_fraction": strict_fraction,
        "conservative_fraction_counting_indeterminate_as_excluded": conservative_fraction,
        "indeterminate_tasks_needed_to_trigger": False,
        "model_set_id": str(summary["model_set_id"]),
        "selected_model_ids": model_set["selected_model_ids"],
        "k1_evaluated": False,
        "k2_evaluated": False,
        "k3_evaluated": False,
        "h2_model_performance_tested": False,
        "h4_model_performance_tested": False,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "interpretive_boundary": (
            "Protocol-defined Pilot 01 falsification/termination via K4; not an empirical "
            "model-performance refutation of H2 or H4."
        ),
    }

    manifest = {
        "phase_label": PHASE_LABEL,
        "package_version": PACKAGE_VERSION,
        "generated_from_commit": source_commit,
        "protocol_git_blob_sha1": "389901146b70684b6c952a8606a5063b972645d4",
        "s1_3_12_freeze_commit": "34b201ad1e00dec234d27771ce535545d99712a3",
        "input_files": inputs,
        "scientific_guards": {
            "protocol_amended": False,
            "k4_threshold_changed": False,
            "model_results_inspected": False,
            "paid_model_inference_run": False,
            "zenodo_publication_performed": False,
        },
    }

    zenodo_draft = {
        "metadata_draft_not_api_submission": True,
        "title": REPORT_TITLE,
        "creators": [{"name": "SAN, CHAU HUNG"}],
        "publication_date": "2026-08-15",
        "resource_type_recommendation": "publication / report",
        "version": PACKAGE_VERSION,
        "license_recommendation": "CC BY 4.0",
        "description": (
            "Preregistered methodological result from DACDM Pilot 01. The pilot terminated "
            "before confirmatory model inference because the frozen K4 contamination criterion "
            "was triggered: 1,165 of 1,301 registered tasks were known contamination exclusions "
            "(89.55%), above the preregistered 30% threshold. This is a protocol-defined "
            "falsification/termination of Pilot 01, not a model-performance refutation of H2/H4."
        ),
        "keywords": [
            "DACDM",
            "AI compute demand",
            "complexity migration",
            "benchmark contamination",
            "preregistration",
            "negative result",
            "code generation",
        ],
        "related_research_objects": [
            {
                "identifier": "10.5281/zenodo.21930795",
                "description": "Existing DACDM v1.0 working-paper package / version DOI",
            },
            {
                "identifier": "10.5281/zenodo.21930794",
                "description": "Existing DACDM concept DOI",
            },
        ],
        "publication_note": (
            "Create a separate Zenodo record after human review; do not overwrite the existing "
            "DACDM conceptual-framework record with this methodological result."
        ),
    }

    status = {
        "phase_label": PHASE_LABEL,
        "status": "PILOT01_TERMINATION_PACKAGE_FROZEN_READY_FOR_HUMAN_PUBLICATION_REVIEW",
        "formal_k4_status": "K4_TRIGGERED",
        "termination_required_by_preregistered_k4": True,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "zenodo_published": False,
        "next_gate": "HUMAN_REVIEW_THEN_INDEPENDENT_ZENODO_PUBLICATION_OR_PILOT02_DESIGN",
    }

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.md").write_text(
        _report_markdown(
            summary=summary,
            s1_3_10_summary=s1_3_10_summary,
            model_set=model_set,
            source_commit=source_commit,
        ),
        encoding="utf-8",
    )
    (output_root / "README.md").write_text(
        _readme_markdown(source_commit), encoding="utf-8"
    )
    _write_json(output_root / "K4_FINAL_ASSESSMENT.json", assessment)
    _write_json(output_root / "REPRODUCIBILITY_MANIFEST.json", manifest)
    _write_json(output_root / "ZENODO_METADATA_DRAFT.json", zenodo_draft)
    _write_json(output_root / "PACKAGE_STATUS.json", status)
    return status
