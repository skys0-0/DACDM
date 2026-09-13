from __future__ import annotations

import pytest

from dacdm.termination_package import TerminationPackageError, validate_final_k4


def _summary() -> dict[str, object]:
    return {
        "formal_k4_status": "K4_TRIGGERED",
        "formal_k4_triggered": True,
        "termination_required_by_preregistered_k4": True,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "denominator_count": 1301,
        "excluded_count": 1165,
        "eligible_count": 132,
        "indeterminate_count": 4,
        "k4_threshold": 0.30,
        "strict_known_exclusion_fraction": 1165 / 1301,
    }


def _evaluation() -> dict[str, object]:
    return {
        "formal_k4_status": "K4_TRIGGERED",
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "oracle_insufficiency_counted_in_k4_numerator": False,
    }


def test_accepts_frozen_preinference_k4_termination() -> None:
    validate_final_k4(_summary(), _evaluation())


def test_rejects_package_if_model_results_were_inspected() -> None:
    summary = _summary()
    summary["model_results_inspected"] = True
    with pytest.raises(TerminationPackageError, match="model_results_inspected"):
        validate_final_k4(summary, _evaluation())


def test_rejects_package_if_k4_does_not_exceed_threshold() -> None:
    summary = _summary()
    summary["strict_known_exclusion_fraction"] = 0.30
    with pytest.raises(TerminationPackageError, match="does not trigger K4"):
        validate_final_k4(summary, _evaluation())


def test_rejects_oracle_failure_in_k4_numerator() -> None:
    evaluation = _evaluation()
    evaluation["oracle_insufficiency_counted_in_k4_numerator"] = True
    with pytest.raises(TerminationPackageError, match="oracle insufficiency"):
        validate_final_k4(_summary(), evaluation)
