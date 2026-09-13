from __future__ import annotations

from pathlib import Path

from dacdm.k4_final import freeze_final_preinference_k4


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    pilot = root / "pilot-01"
    summary = freeze_final_preinference_k4(
        model_set_path=pilot / "registries/test_window_model_set_v1.json",
        models_path=pilot / "registries/models.json",
        cutoffs_path=pilot / "registries/training_cutoff_evidence.json",
        s1_3_11_task_universe_path=pilot / "backtest/s1_3_11/task_universe.json",
        s1_3_11_summary_path=pilot / "backtest/s1_3_11/summary.json",
        output_root=pilot / "backtest/s1_3_12",
    )
    print(
        "S1.3.12 final pre-inference K4 evaluation: "
        f"status={summary['formal_k4_status']}, "
        f"excluded={summary['excluded_count']}/{summary['denominator_count']}, "
        f"fraction={summary['strict_known_exclusion_fraction']:.6f}, "
        f"next={summary['next_gate']}"
    )


if __name__ == "__main__":
    main()
