from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


PHASE_LABEL = "S1.3.9_REGISTERED_ORACLE_CONSTRUCTION"
MIN_REGISTERED_TESTS = 20


class LeetCodeOracleError(ValueError):
    """Raised when S1.3.9 oracle-source registration cannot be reproduced."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = _load_json(path)
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise LeetCodeOracleError(f"expected JSON array of objects: {path}")
    return raw


def _load_object(path: Path) -> dict[str, Any]:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise LeetCodeOracleError(f"expected JSON object: {path}")
    return raw


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_slug(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("_", "-")


def _load_dataset_rows(
    source_root: Path, source_manifest: dict[str, Any]
) -> tuple[dict[str, tuple[str, dict[str, Any]]], dict[str, str]]:
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    file_hashes: dict[str, str] = {}
    for split in ("train", "test"):
        raw_path = source_manifest.get(f"{split}_path")
        if not isinstance(raw_path, str) or not raw_path:
            raise LeetCodeOracleError(f"source manifest missing {split}_path")
        path = source_root / raw_path
        if not path.is_file():
            raise LeetCodeOracleError(f"missing frozen oracle source file: {path}")
        file_hashes[split] = _sha256_file(path)
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LeetCodeOracleError(
                        f"invalid JSONL row {split}:{line_number}"
                    ) from exc
                if not isinstance(row, dict):
                    raise LeetCodeOracleError(
                        f"non-object JSONL row {split}:{line_number}"
                    )
                slug = _normalize_slug(row.get("task_id"))
                if not slug:
                    raise LeetCodeOracleError(
                        f"dataset row missing task_id at {split}:{line_number}"
                    )
                if slug in index:
                    previous_split, _ = index[slug]
                    raise LeetCodeOracleError(
                        f"duplicate normalized task_id {slug!r} in {previous_split}/{split}"
                    )
                index[slug] = (split, row)
    return index, file_hashes


def _case_pair(case: object) -> tuple[object, object] | None:
    if isinstance(case, dict) and "input" in case and "output" in case:
        return case["input"], case["output"]
    if isinstance(case, list) and len(case) == 2:
        return case[0], case[1]
    return None


def _suite_metadata(row: dict[str, Any]) -> dict[str, Any]:
    raw_cases = row.get("input_output")
    if not isinstance(raw_cases, list):
        return {
            "schema_supported": False,
            "raw_case_count": 0,
            "valid_pair_count": 0,
            "distinct_pair_count": 0,
            "suite_sha256": None,
        }

    pair_hashes: list[str] = []
    for case in raw_cases:
        pair = _case_pair(case)
        if pair is None:
            continue
        digest = hashlib.sha256(_canonical_json(pair).encode("utf-8")).hexdigest()
        pair_hashes.append(digest)
    distinct_hashes = sorted(set(pair_hashes))
    suite_sha256 = (
        hashlib.sha256("\n".join(distinct_hashes).encode("ascii")).hexdigest()
        if distinct_hashes
        else None
    )
    return {
        "schema_supported": len(pair_hashes) == len(raw_cases),
        "raw_case_count": len(raw_cases),
        "valid_pair_count": len(pair_hashes),
        "distinct_pair_count": len(distinct_hashes),
        "suite_sha256": suite_sha256,
    }


def register_leetcode_oracle_sources(
    *,
    source_root: Path,
    source_manifest_path: Path,
    candidates_path: Path,
    admission_readiness_path: Path,
    oracle_registry_output_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    source_manifest = _load_object(source_manifest_path)
    candidates = _load_array(candidates_path)
    readiness = _load_array(admission_readiness_path)
    readiness_by_task = {
        str(row.get("canonical_task_id")): row for row in readiness
    }
    if len(readiness_by_task) != len(readiness):
        raise LeetCodeOracleError("S1.3.8 readiness contains duplicate canonical_task_id")

    dataset_index, source_file_hashes = _load_dataset_rows(source_root, source_manifest)
    oracle_registry: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    match_split_counts: Counter[str] = Counter()

    for candidate in sorted(
        candidates, key=lambda row: str(row.get("canonical_task_id", ""))
    ):
        task_id = str(candidate.get("canonical_task_id", ""))
        slug = _normalize_slug(candidate.get("problem_slug"))
        ready = readiness_by_task.get(task_id)
        if ready is None:
            raise LeetCodeOracleError(f"missing S1.3.8 readiness for {task_id}")

        difficulty_status = str(ready.get("difficulty_evidence_status", "UNKNOWN"))
        contamination_status = str(ready.get("contamination_status", "INDETERMINATE"))
        source_match = dataset_index.get(slug)
        source_split: str | None = None
        source_row: dict[str, Any] | None = None
        suite: dict[str, Any] = {
            "schema_supported": False,
            "raw_case_count": 0,
            "valid_pair_count": 0,
            "distinct_pair_count": 0,
            "suite_sha256": None,
        }

        if source_match is not None:
            source_split, source_row = source_match
            match_split_counts[source_split] += 1
            suite = _suite_metadata(source_row)

        if difficulty_status != "SUPPORTED":
            status = "BLOCKED_DIFFICULTY_EVIDENCE"
        elif contamination_status != "ELIGIBLE":
            status = "BLOCKED_CONTAMINATION"
        elif source_row is None:
            status = "EXTERNAL_ORACLE_SOURCE_MISSING"
        elif str(source_row.get("difficulty")) != "Hard":
            status = "EXTERNAL_ORACLE_DIFFICULTY_CONFLICT"
        elif not bool(suite["schema_supported"]):
            status = "EXTERNAL_ORACLE_SCHEMA_UNSUPPORTED"
        elif int(suite["distinct_pair_count"]) < MIN_REGISTERED_TESTS:
            status = "EXTERNAL_ORACLE_TEST_COUNT_INSUFFICIENT"
        else:
            if source_split is None:
                raise LeetCodeOracleError(f"source split missing for matched task {task_id}")
            status = "REGISTERED_SOURCE_SUITE_EDGE_REVIEW_REQUIRED"
            row_material = {
                "task_id": source_row.get("task_id"),
                "question_id": source_row.get("question_id"),
                "difficulty": source_row.get("difficulty"),
                "estimated_date": source_row.get("estimated_date"),
                "entry_point": source_row.get("entry_point"),
                "input_output": source_row.get("input_output"),
                "test": source_row.get("test"),
            }
            source_row_sha256 = hashlib.sha256(
                _canonical_json(row_material).encode("utf-8")
            ).hexdigest()
            oracle_registry.append(
                {
                    "canonical_task_id": task_id,
                    "problem_slug": slug,
                    "source_repository": source_manifest.get("source_repository"),
                    "source_revision": source_manifest.get("source_revision"),
                    "dataset_version": source_manifest.get("dataset_version"),
                    "source_split": source_split,
                    "source_path": source_manifest.get(f"{source_split}_path"),
                    "source_blob_sha": source_manifest.get(
                        f"{source_split}_blob_sha"
                    ),
                    "source_file_sha256": source_file_hashes[source_split],
                    "source_row_sha256": source_row_sha256,
                    "entry_point": source_row.get("entry_point"),
                    "distinct_registered_test_count": suite["distinct_pair_count"],
                    "test_suite_sha256": suite["suite_sha256"],
                    "test_payload_redistributed": False,
                    "ordinary_case_evidence_status": "REVIEW_REQUIRED",
                    "edge_case_evidence_status": "REVIEW_REQUIRED",
                    "executable_harness_validation_status": "PENDING_SANDBOX_VALIDATION",
                    "if09_status": "NUMERIC_TEST_COUNT_MET_ADMISSION_NOT_YET_GRANTED",
                    "model_results_inspected": False,
                    "paid_inference_permitted": False,
                    "phase_label": PHASE_LABEL,
                }
            )
        status_counts[status] += 1
        task_rows.append(
            {
                "canonical_task_id": task_id,
                "problem_slug": slug,
                "difficulty_evidence_status": difficulty_status,
                "contamination_status": contamination_status,
                "external_source_match": source_row is not None,
                "external_source_split": source_split,
                "external_source_difficulty": (
                    source_row.get("difficulty") if source_row is not None else None
                ),
                "raw_test_case_count": suite["raw_case_count"],
                "valid_test_pair_count": suite["valid_pair_count"],
                "distinct_test_pair_count": suite["distinct_pair_count"],
                "test_suite_sha256": suite["suite_sha256"],
                "status": status,
                "confirmatory_admitted": False,
                "model_results_inspected": False,
                "paid_inference_permitted": False,
                "phase_label": PHASE_LABEL,
            }
        )

    _write_json(oracle_registry_output_path, oracle_registry)
    _write_json(output_root / "task_oracle_source_registration.json", task_rows)

    summary = {
        "status": "REGISTERED_EXTERNAL_ORACLE_SOURCES_EDGE_AND_HARNESS_REVIEW_REQUIRED",
        "candidate_count": len(candidates),
        "external_dataset_row_count": len(dataset_index),
        "external_source_match_split_counts": dict(sorted(match_split_counts.items())),
        "task_status_counts": dict(sorted(status_counts.items())),
        "registered_source_suite_count": len(oracle_registry),
        "if09_minimum_registered_tests": MIN_REGISTERED_TESTS,
        "confirmatory_admitted_task_count": 0,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": "S1.3.10_EDGE_CASE_AND_EXECUTABLE_HARNESS_VALIDATION",
        "source_repository": source_manifest.get("source_repository"),
        "source_revision": source_manifest.get("source_revision"),
        "dataset_version": source_manifest.get("dataset_version"),
        "source_file_sha256": source_file_hashes,
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "summary.json", summary)
    return summary
