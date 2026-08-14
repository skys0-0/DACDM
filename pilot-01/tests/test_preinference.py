from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from dacdm.preinference import audit_preinference_admissibility, contamination_status


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_month_precision_is_tri_state_without_inventing_day() -> None:
    evidence = {
        "cutoff_precision": "month",
        "claimed_cutoff_month": "2024-04",
    }
    assert contamination_status(date(2024, 3, 31), evidence)[0] == "EXCLUDED"
    assert contamination_status(date(2024, 4, 15), evidence)[0] == "INDETERMINATE"
    assert contamination_status(date(2024, 5, 1), evidence)[0] == "ELIGIBLE"


def test_preinference_audit_blocks_contaminated_sample(tmp_path: Path) -> None:
    tasks = [
        {
            "task_id": "humaneval:1",
            "benchmark": "humaneval",
            "release_date": "2021-07-07",
        }
    ]
    sample = [{"task_id": "humaneval:1"}]
    models = [
        {
            "model_id": "provider:model-2024",
            "public_launch_date": "2024-06-01",
            "training_cutoff_evidence_ids": ["cutoff-1"],
            "pricing_record_ids": ["price-in", "price-out"],
        }
    ]
    cutoffs = [
        {
            "evidence_id": "cutoff-1",
            "status": "supported",
            "cutoff_precision": "month",
            "claimed_cutoff_month": "2023-10",
        }
    ]
    snapshots = [
        {
            "model_id": "provider:model-2024",
            "observation_date": "2026-08-14",
            "availability_status": "callable_exact",
        }
    ]
    prices = [
        {
            "pricing_record_id": "price-in",
            "variation": "input",
            "effective_from": "2024-06-01",
            "effective_to": None,
        },
        {
            "pricing_record_id": "price-out",
            "variation": "output",
            "effective_from": "2024-06-01",
            "effective_to": None,
        },
    ]

    paths = {}
    for name, value in {
        "tasks": tasks,
        "sample": sample,
        "models": models,
        "cutoffs": cutoffs,
        "snapshots": snapshots,
        "pricing": prices,
    }.items():
        path = tmp_path / f"{name}.json"
        _write(path, value)
        paths[name] = path

    summary = audit_preinference_admissibility(
        tasks_path=paths["tasks"],
        sample_path=paths["sample"],
        models_path=paths["models"],
        cutoff_path=paths["cutoffs"],
        snapshot_path=paths["snapshots"],
        pricing_path=paths["pricing"],
        output_root=tmp_path / "out",
    )

    assert summary["sample_task_year_cells"] == 3
    assert summary["ready_for_paid_inference_cells"] == 0
    assert summary["paid_inference_gate"] == "BLOCKED"
    assert summary["detail_status_counts"] == {"CONTAMINATION_EXCLUDED": 3}
    assert (tmp_path / "out" / "microbacktest_admissibility.csv").exists()
