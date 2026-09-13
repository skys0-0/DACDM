from __future__ import annotations

import subprocess
from pathlib import Path

from dacdm.termination_package import build_termination_package


def _current_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
    ).strip()


def main() -> None:
    pilot_root = Path(__file__).resolve().parents[1]
    output_root = pilot_root / "results/pilot01-preinference-termination-v1.0"
    status = build_termination_package(
        root=pilot_root,
        output_root=output_root,
        source_commit=_current_commit(),
    )
    print(status["status"])


if __name__ == "__main__":
    main()
