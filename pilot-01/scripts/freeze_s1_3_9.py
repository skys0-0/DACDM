from __future__ import annotations

import argparse
from pathlib import Path

from dacdm.leetcode_oracle import register_leetcode_oracle_sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("registries/leetcode_oracle_source.json"),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("registries/leetcode_weekly_hard_candidates.json"),
    )
    parser.add_argument(
        "--admission-readiness",
        type=Path,
        default=Path("backtest/s1_3_8/task_admission_readiness.json"),
    )
    parser.add_argument(
        "--oracle-registry-output",
        type=Path,
        default=Path("registries/leetcode_oracle_registry.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_3_9"),
    )
    args = parser.parse_args()

    summary = register_leetcode_oracle_sources(
        source_root=args.source_root,
        source_manifest_path=args.source_manifest,
        candidates_path=args.candidates,
        admission_readiness_path=args.admission_readiness,
        oracle_registry_output_path=args.oracle_registry_output,
        output_root=args.output_root,
    )
    print(
        "S1.3.9 oracle registration: "
        f"registered_source_suites={summary['registered_source_suite_count']}, "
        f"admitted={summary['confirmatory_admitted_task_count']}, "
        f"next={summary['next_gate']}"
    )


if __name__ == "__main__":
    main()
