from pathlib import Path

from dacdm.k4_universe import freeze_k4_universe


def main() -> None:
    root = Path(".")
    summary = freeze_k4_universe(
        root=root,
        interpretation_path=Path("registries/k4_denominator_interpretation.json"),
        static_tasks_path=Path("registries/tasks.json"),
        leetcode_candidates_path=Path("registries/leetcode_weekly_hard_candidates.json"),
        models_path=Path("registries/models.json"),
        cutoffs_path=Path("registries/training_cutoff_evidence.json"),
        s1_3_10_summary_path=Path("backtest/s1_3_10/summary.json"),
        s1_3_10_validation_path=Path("backtest/s1_3_10/task_validation.json"),
        output_root=Path("backtest/s1_3_11"),
    )
    print(
        "S1.3.11 K4 universe freeze: "
        f"denominator={summary['denominator_count']}, "
        f"formal={summary['formal_k4_status']}, "
        f"current-evidence fraction={summary['current_evidence_excluded_fraction']:.6f}, "
        f"next={summary['next_gate']}"
    )


if __name__ == "__main__":
    main()
