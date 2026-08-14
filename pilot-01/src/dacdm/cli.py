from __future__ import annotations

import argparse
import json
from pathlib import Path

from .protocol import validate_protocol_integrity
from .registries import validate_registry_files
from .registries.benchmark_import import BenchmarkImportError, build_task_registry


def _report(errors: list[str], success: str) -> None:
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(success)


def main() -> None:
    parser = argparse.ArgumentParser(prog="dacdm")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-protocol")
    sub.add_parser("validate-registries")

    build = sub.add_parser("build-task-registry")
    build.add_argument(
        "--manifest",
        type=Path,
        default=Path("registries/benchmark_sources.json"),
    )
    build.add_argument("--source-root", type=Path, required=True)
    build.add_argument(
        "--output",
        type=Path,
        default=Path("registries/tasks.json"),
    )

    args = parser.parse_args()

    if args.command == "validate-protocol":
        _report(validate_protocol_integrity(), "Protocol integrity: OK")
    elif args.command == "validate-registries":
        _report(validate_registry_files(), "Registry integrity: OK")
    elif args.command == "build-task-registry":
        try:
            records = build_task_registry(args.manifest, args.source_root, args.output)
        except (BenchmarkImportError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(f"Task registry built: {len(records)} records -> {args.output}")
