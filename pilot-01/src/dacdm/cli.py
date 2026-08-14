from __future__ import annotations

import argparse
import json
from pathlib import Path

from .preinference import PreInferenceAuditError, audit_preinference_admissibility
from .protocol import validate_protocol_integrity
from .readiness import ReadinessError, prepare_readiness
from .registries import validate_registry_files
from .registries.benchmark_import import BenchmarkImportError, build_task_registry
from .registries.s1_3_candidates import CandidateExtractionError, write_model_candidates


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

    readiness = sub.add_parser("prepare-backtest-readiness")
    readiness.add_argument(
        "--tasks",
        type=Path,
        default=Path("registries/tasks.json"),
    )
    readiness.add_argument("--ai-price-csv", type=Path, required=True)
    readiness.add_argument("--epoch-hardware-csv", type=Path, required=True)
    readiness.add_argument(
        "--source-metadata",
        type=Path,
        required=True,
    )
    readiness.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_2_5"),
    )

    candidates = sub.add_parser("extract-s1-3-model-candidates")
    candidates.add_argument("--ai-price-csv", type=Path, required=True)
    candidates.add_argument(
        "--output",
        type=Path,
        default=Path("registries/s1_3_model_candidates.json"),
    )

    audit = sub.add_parser("audit-preinference-admissibility")
    audit.add_argument("--tasks", type=Path, default=Path("registries/tasks.json"))
    audit.add_argument(
        "--sample",
        type=Path,
        default=Path("backtest/s1_2_5/microbacktest_tasks.json"),
    )
    audit.add_argument("--models", type=Path, default=Path("registries/models.json"))
    audit.add_argument(
        "--cutoffs",
        type=Path,
        default=Path("registries/training_cutoff_evidence.json"),
    )
    audit.add_argument(
        "--snapshots",
        type=Path,
        default=Path("registries/historical_snapshot_evidence.json"),
    )
    audit.add_argument("--pricing", type=Path, default=Path("registries/pricing.json"))
    audit.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_3_6"),
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
    elif args.command == "prepare-backtest-readiness":
        try:
            metadata = json.loads(args.source_metadata.read_text(encoding="utf-8"))
            if not isinstance(metadata, dict):
                raise ReadinessError("source metadata must be a JSON object")
            manifest = prepare_readiness(
                args.tasks,
                args.ai_price_csv,
                args.epoch_hardware_csv,
                args.output_root,
                metadata,
            )
        except (ReadinessError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(
            "S1.2.5 readiness prepared: "
            f"{manifest['task_count']} tasks, "
            f"{manifest['task_year_cells']} task-year cells, "
            f"{manifest['price_rows']} price rows, "
            f"{manifest['hardware_months']} hardware months"
        )
    elif args.command == "extract-s1-3-model-candidates":
        try:
            records = write_model_candidates(args.ai_price_csv, args.output)
        except (CandidateExtractionError, OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(f"S1.3 model candidates extracted: {len(records)} -> {args.output}")
    elif args.command == "audit-preinference-admissibility":
        try:
            summary = audit_preinference_admissibility(
                tasks_path=args.tasks,
                sample_path=args.sample,
                models_path=args.models,
                cutoff_path=args.cutoffs,
                snapshot_path=args.snapshots,
                pricing_path=args.pricing,
                output_root=args.output_root,
            )
        except (PreInferenceAuditError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(
            "S1.3.6 pre-inference audit: "
            f"{summary['sample_task_year_cells']} cells, "
            f"{summary['ready_for_paid_inference_cells']} ready, "
            f"paid inference gate={summary['paid_inference_gate']}"
        )
