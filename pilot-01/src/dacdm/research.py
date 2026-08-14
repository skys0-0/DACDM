from __future__ import annotations

from datetime import date


def contamination_eligible(
    *, task_release_date: date, training_cutoff_date: date | None, model_launch_date: date
) -> tuple[bool, str]:
    """Apply the frozen Pilot 01 contamination policy without guessing missing cutoffs."""
    if training_cutoff_date is not None:
        if task_release_date < training_cutoff_date:
            return False, "TASK_PRECEDES_TRAINING_CUTOFF"
        return True, "TASK_ON_OR_AFTER_TRAINING_CUTOFF"

    # Unknown cutoff: exclude tasks released >6 months before public launch.
    # Six calendar months are represented conservatively as 183 days for S0.
    delta_days = (model_launch_date - task_release_date).days
    if delta_days > 183:
        return False, "UNKNOWN_CUTOFF_CONSERVATIVE_EXCLUSION"
    return True, "UNKNOWN_CUTOFF_WITHIN_SIX_MONTH_WINDOW"


def agent_overhead_alpha(*, c_base: float, c_sub: float, c_tool: float) -> float | None:
    if min(c_base, c_sub, c_tool) < 0:
        raise ValueError("costs cannot be negative")
    if c_base == 0:
        return None
    return (c_sub + c_tool) / c_base


def minimum_cost(costs: list[tuple[float, bool]]) -> float | None:
    eligible = [cost for cost, meets_threshold in costs if meets_threshold]
    return min(eligible) if eligible else None


def downward_transition(previous_tier: int, current_tier: int) -> bool:
    if previous_tier not in (1, 2, 3) or current_tier not in (1, 2, 3):
        raise ValueError("tier must be 1, 2, or 3")
    return current_tier < previous_tier


def kill_criteria(
    *, beta1: float, p_value: float, two_year_hardware_not_beaten: bool,
    frontier_share_declined: bool, contamination_fraction: float
) -> dict[str, bool]:
    if not 0 <= contamination_fraction <= 1:
        raise ValueError("contamination_fraction must be in [0, 1]")
    return {
        "K1": beta1 >= 0 and p_value > 0.05,
        "K2": two_year_hardware_not_beaten,
        "K3": not frontier_share_declined,
        "K4": contamination_fraction > 0.30,
    }
