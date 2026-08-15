from __future__ import annotations

import pytest

from dacdm.k4_final import K4FinalError, decide_k4_from_bounds


def test_known_exclusion_lower_bound_triggers_even_with_indeterminate() -> None:
    status, triggered, strict_fraction, conservative_fraction = decide_k4_from_bounds(
        excluded_count=40,
        indeterminate_count=10,
        denominator_count=100,
        threshold=0.30,
    )
    assert status == "K4_TRIGGERED"
    assert triggered is True
    assert strict_fraction == 0.40
    assert conservative_fraction == 0.50


def test_conservative_upper_bound_can_establish_not_triggered() -> None:
    status, triggered, strict_fraction, conservative_fraction = decide_k4_from_bounds(
        excluded_count=20,
        indeterminate_count=5,
        denominator_count=100,
        threshold=0.30,
    )
    assert status == "K4_NOT_TRIGGERED"
    assert triggered is False
    assert strict_fraction == 0.20
    assert conservative_fraction == 0.25


def test_crossing_threshold_remains_unresolved() -> None:
    status, triggered, strict_fraction, conservative_fraction = decide_k4_from_bounds(
        excluded_count=25,
        indeterminate_count=10,
        denominator_count=100,
        threshold=0.30,
    )
    assert status == "K4_UNRESOLVED_CONTAMINATION_INDETERMINATE"
    assert triggered is None
    assert strict_fraction == 0.25
    assert conservative_fraction == 0.35


def test_k4_threshold_is_strictly_more_than_30_percent() -> None:
    status, triggered, _, _ = decide_k4_from_bounds(
        excluded_count=30,
        indeterminate_count=0,
        denominator_count=100,
        threshold=0.30,
    )
    assert status == "K4_NOT_TRIGGERED"
    assert triggered is False


def test_invalid_counts_rejected() -> None:
    with pytest.raises(K4FinalError):
        decide_k4_from_bounds(
            excluded_count=90,
            indeterminate_count=20,
            denominator_count=100,
            threshold=0.30,
        )
