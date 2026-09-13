from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .leetcode_admission import (
    LeetCodeAdmissionError,
    audit_leetcode_admission_readiness,
    fetch_official_problem_metadata,
)
from .leetcode_freeze import LeetCodeFreezeError, freeze_leetcode_weekly_hard
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

    leetcode = sub.add_parser("freeze-leetcode-weekly-hard")
    leetcode.add_argument("--source-root", type=Path, required=True)
    leetcode.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("registries/leetcode_weekly_hard_source.json"),
    )
    leetcode.add_argument("--models", type=Path, default=Path("registries/models.json"))
    leetcode.add_argument(
        "--cutoffs",
        type=Path,
        default=Path("registries/training_cutoff_evidence.json"),
    )
    leetcode.add_argument("--tasks", type=Path, default=Path("registries/tasks.json"))
    leetcode.add_argument(
        "--candidate-output",
        type=Path,
        default=Path("registries/leetcode_weekly_hard_candidates.json"),
    )
    leetcode.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_3_7"),
    )
    leetcode.add_argument(
        "--freeze-date",
        type=date.fromisoformat,
        default=date(2026, 8, 14),
    )
    leetcode.add_argument("--source-archive-sha256")

    official = sub.add_parser("fetch-leetcode-official-metadata")
    official.add_argument(
        "--candidates",
        type=Path,
        default=Path("registries/leetcode_weekly_hard_candidates.json"),
    )
    official.add_argument(
        "--output",
        type=Path,
        default=Path("registries/leetcode_official_problem_metadata.json"),
    )
    official.add_argument("--retrieved-at")

    admission = sub.add_parser("audit-leetcode-admission-readiness")
    admission.add_argument("--source-root", type=Path, required=True)
    admission.add_argument(
        "--candidates",
        type=Path,
        default=Path("registries/leetcode_weekly_hard_candidates.json"),
    )
    admission.add_argument(
        "--official-metadata",
        type=Path,
        default=Path("registries/leetcode_official_problem_metadata.json"),
    )
    admission.add_argument(
        "--difficulty-evidence-output",
        type=Path,
        default=Path("registries/leetcode_difficulty_evidence.json"),
    )
    admission.add_argument(
        "--output-root",
        type=Path,
        default=Path("backtest/s1_3_8"),
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
    elif args.command == "freeze-leetcode-weekly-hard":
        try:
            summary = freeze_leetcode_weekly_hard(
                source_root=args.source_root,
                source_manifest_path=args.source_manifest,
                models_path=args.models,
                cutoffs_path=args.cutoffs,
                static_tasks_path=args.tasks,
                candidate_output_path=args.candidate_output,
                output_root=args.output_root,
                freeze_date=args.freeze_date,
                source_archive_sha256=args.source_archive_sha256,
            )
        except (LeetCodeFreezeError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(
            "S1.3.7 LeetCode metadata freeze: "
            f"{summary['selected_weekly_contest_count']} contests, "
            f"{summary['hard_metadata_candidate_count']} Hard metadata candidates, "
            f"oracle={summary['oracle_status']}"
        )
    elif args.command == "fetch-leetcode-official-metadata":
        try:
            records = fetch_official_problem_metadata(
                candidates_path=args.candidates,
                output_path=args.output,
                retrieved_at=args.retrieved_at,
            )
        except (LeetCodeAdmissionError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(f"S1.3.8 official LeetCode metadata fetched: {len(records)} records")
    elif args.command == "audit-leetcode-admission-readiness":
        try:
            summary = audit_leetcode_admission_readiness(
                candidates_path=args.candidates,
                official_metadata_path=args.official_metadata,
                source_root=args.source_root,
                difficulty_evidence_output_path=args.difficulty_evidence_output,
                output_root=args.output_root,
            )
        except (LeetCodeAdmissionError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            raise SystemExit(1) from exc
        print(
            "S1.3.8 LeetCode admission audit: "
            f"{summary['candidate_count']} candidates, "
            f"admitted={summary['confirmatory_admitted_task_count']}, "
            f"next={summary['next_gate']}"
        )
