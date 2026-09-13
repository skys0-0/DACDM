from __future__ import annotations

import argparse
from pathlib import Path

from dacdm.leetcode_oracle_validation import validate_registered_oracles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("registries/leetcode_oracle_source.json"),
    )
    parser.add_argument(
        "--oracle-registry",
        type=Path,
        default=Path("registries/leetcode_oracle_registry.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_3_10"),
    )
    args = parser.parse_args()

    summary = validate_registered_oracles(
        source_root=args.source_root,
        source_manifest_path=args.source_manifest,
        oracle_registry_path=args.oracle_registry,
        output_root=args.output_root,
    )
    print(
        "S1.3.10 oracle validation: "
        f"registered={summary['registered_suite_count']}, "
        f"if09_ready={summary['if09_ready_task_count']}, "
        f"next={summary['next_gate']}"
    )


if __name__ == "__main__":
    main()
