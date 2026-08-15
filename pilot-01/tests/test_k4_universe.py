from datetime import date
from typing import Any

from dacdm.k4_universe import global_contamination_status, model_contamination_status


def _month_cutoff(evidence_id: str, model_id: str, month: str) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "model_id": model_id,
        "status": "supported",
        "cutoff_precision": "month",
        "claimed_cutoff_date": None,
        "claimed_cutoff_month": month,
    }


def _model(model_id: str, cutoff_id: str, launch_date: str = "2024-07-18") -> dict[str, Any]:
    return {
        "model_id": model_id,
        "public_launch_date": launch_date,
        "training_cutoff_evidence_ids": [cutoff_id],
        "enabled_for_pilot": False,
    }


def test_month_precision_preserves_indeterminate_boundary() -> None:
    cutoff = _month_cutoff("cutoff:a", "model:a", "2024-04")
    model = _model("model:a", "cutoff:a")
    cutoff_by_id = {"cutoff:a": cutoff}

    assert model_contamination_status(
        task_release_date=date(2024, 3, 31), model=model, cutoff_by_id=cutoff_by_id
    )[0] == "EXCLUDED"
    assert model_contamination_status(
        task_release_date=date(2024, 4, 15), model=model, cutoff_by_id=cutoff_by_id
    )[0] == "INDETERMINATE"
    assert model_contamination_status(
        task_release_date=date(2024, 5, 1), model=model, cutoff_by_id=cutoff_by_id
    )[0] == "ELIGIBLE"


def test_unknown_cutoff_uses_exact_six_calendar_month_fallback() -> None:
    model: dict[str, Any] = {
        "model_id": "model:unknown",
        "public_launch_date": "2024-08-31",
        "training_cutoff_evidence_ids": [],
        "enabled_for_pilot": False,
    }

    boundary_status, _ = model_contamination_status(
        task_release_date=date(2024, 2, 29), model=model, cutoff_by_id={}
    )
    older_status, _ = model_contamination_status(
        task_release_date=date(2024, 2, 28), model=model, cutoff_by_id={}
    )

    assert boundary_status == "ELIGIBLE"
    assert older_status == "EXCLUDED"


def test_global_contamination_uses_any_model_exclusion() -> None:
    cutoffs = {
        "cutoff:early": _month_cutoff("cutoff:early", "model:early", "2023-10"),
        "cutoff:late": _month_cutoff("cutoff:late", "model:late", "2024-04"),
    }
    models = [
        _model("model:early", "cutoff:early"),
        _model("model:late", "cutoff:late"),
    ]

    status = global_contamination_status(
        task_release_date=date(2024, 1, 7), models=models, cutoff_by_id=cutoffs
    )

    assert status == "EXCLUDED"


def test_global_contamination_preserves_indeterminate_when_no_model_excludes() -> None:
    cutoffs = {
        "cutoff:a": _month_cutoff("cutoff:a", "model:a", "2024-04"),
        "cutoff:b": _month_cutoff("cutoff:b", "model:b", "2024-03"),
    }
    models = [_model("model:a", "cutoff:a"), _model("model:b", "cutoff:b")]

    status = global_contamination_status(
        task_release_date=date(2024, 4, 15), models=models, cutoff_by_id=cutoffs
    )

    assert status == "INDETERMINATE"


def test_empty_test_window_model_set_is_unresolved() -> None:
    assert (
        global_contamination_status(
            task_release_date=date(2024, 1, 1), models=[], cutoff_by_id={}
        )
        == "UNRESOLVED_MODEL_SET"
    )
