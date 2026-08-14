from datetime import date

import pytest

from dacdm.research import agent_overhead_alpha, contamination_eligible, downward_transition, kill_criteria, minimum_cost


def test_known_cutoff_excludes_older_task() -> None:
    eligible, reason = contamination_eligible(
        task_release_date=date(2024, 1, 1),
        training_cutoff_date=date(2024, 6, 1),
        model_launch_date=date(2024, 8, 1),
    )
    assert eligible is False
    assert reason == "TASK_PRECEDES_TRAINING_CUTOFF"


def test_unknown_cutoff_uses_conservative_window() -> None:
    eligible, _ = contamination_eligible(
        task_release_date=date(2024, 1, 1),
        training_cutoff_date=None,
        model_launch_date=date(2025, 1, 1),
    )
    assert eligible is False


def test_agent_overhead_is_observed_ratio() -> None:
    assert agent_overhead_alpha(c_base=2.0, c_sub=1.0, c_tool=0.5) == pytest.approx(0.75)
    assert agent_overhead_alpha(c_base=0, c_sub=1, c_tool=0) is None


def test_minimum_cost_only_uses_threshold_clearing_paths() -> None:
    assert minimum_cost([(0.01, False), (0.05, True), (0.03, True)]) == pytest.approx(0.03)
    assert minimum_cost([(0.01, False)]) is None


def test_only_downward_tier_moves_count_as_compression() -> None:
    assert downward_transition(3, 2)
    assert not downward_transition(2, 2)
    assert not downward_transition(1, 2)


def test_k4_is_strictly_more_than_30_percent() -> None:
    assert kill_criteria(beta1=-1, p_value=0.01, two_year_hardware_not_beaten=False,
                         frontier_share_declined=True, contamination_fraction=0.30)["K4"] is False
    assert kill_criteria(beta1=-1, p_value=0.01, two_year_hardware_not_beaten=False,
                         frontier_share_declined=True, contamination_fraction=0.301)["K4"] is True
