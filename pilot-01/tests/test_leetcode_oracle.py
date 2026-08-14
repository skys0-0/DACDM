from __future__ import annotations

import gzip
import json
from pathlib import Path

from dacdm.leetcode_oracle import register_leetcode_oracle_sources


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_jsonl_gz(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _cases(count: int) -> list[dict[str, object]]:
    return [{"input": [index], "output": index * 2} for index in range(count)]


def test_registers_numeric_suite_without_granting_confirmatory_admission(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    train_path = source_root / "data" / "train.jsonl.gz"
    test_path = source_root / "data" / "test.jsonl.gz"
    _write_jsonl_gz(train_path, [])
    _write_jsonl_gz(
        test_path,
        [
            {
                "task_id": "hard_candidate",
                "question_id": 1,
                "difficulty": "Hard",
                "estimated_date": "2024-08-01",
                "entry_point": "solve",
                "input_output": _cases(20),
                "test": "def check(candidate): pass",
            }
        ],
    )

    manifest = tmp_path / "source.json"
    _write_json(
        manifest,
        {
            "source_repository": "fixture/LeetCodeDataset",
            "source_revision": "fixture-revision",
            "dataset_version": "v0",
            "train_path": "data/train.jsonl.gz",
            "train_blob_sha": "train-blob",
            "test_path": "data/test.jsonl.gz",
            "test_blob_sha": "test-blob",
        },
    )
    candidates = tmp_path / "candidates.json"
    _write_json(
        candidates,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:hard-candidate",
                "problem_slug": "hard-candidate",
            }
        ],
    )
    readiness = tmp_path / "readiness.json"
    _write_json(
        readiness,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:hard-candidate",
                "difficulty_evidence_status": "SUPPORTED",
                "contamination_status": "ELIGIBLE",
            }
        ],
    )

    oracle_registry = tmp_path / "oracle_registry.json"
    output_root = tmp_path / "out"
    summary = register_leetcode_oracle_sources(
        source_root=source_root,
        source_manifest_path=manifest,
        candidates_path=candidates,
        admission_readiness_path=readiness,
        oracle_registry_output_path=oracle_registry,
        output_root=output_root,
    )

    rows = json.loads(oracle_registry.read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert rows[0]["distinct_registered_test_count"] == 20
    assert rows[0]["if09_status"] == (
        "NUMERIC_TEST_COUNT_MET_ADMISSION_NOT_YET_GRANTED"
    )
    assert rows[0]["edge_case_evidence_status"] == "REVIEW_REQUIRED"
    assert summary["registered_source_suite_count"] == 1
    assert summary["confirmatory_admitted_task_count"] == 0
    assert summary["paid_inference_permitted"] is False


def test_blocks_contamination_before_oracle_registration(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    _write_jsonl_gz(
        source_root / "train.jsonl.gz",
        [
            {
                "task_id": "old_hard",
                "difficulty": "Hard",
                "input_output": _cases(25),
            }
        ],
    )
    _write_jsonl_gz(source_root / "test.jsonl.gz", [])
    manifest = tmp_path / "source.json"
    _write_json(
        manifest,
        {
            "source_repository": "fixture/source",
            "source_revision": "fixture",
            "dataset_version": "v0",
            "train_path": "train.jsonl.gz",
            "train_blob_sha": "a",
            "test_path": "test.jsonl.gz",
            "test_blob_sha": "b",
        },
    )
    candidates = tmp_path / "candidates.json"
    _write_json(
        candidates,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:old-hard",
                "problem_slug": "old-hard",
            }
        ],
    )
    readiness = tmp_path / "readiness.json"
    _write_json(
        readiness,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:old-hard",
                "difficulty_evidence_status": "SUPPORTED",
                "contamination_status": "EXCLUDED",
            }
        ],
    )

    oracle_registry = tmp_path / "oracles.json"
    output_root = tmp_path / "out"
    summary = register_leetcode_oracle_sources(
        source_root=source_root,
        source_manifest_path=manifest,
        candidates_path=candidates,
        admission_readiness_path=readiness,
        oracle_registry_output_path=oracle_registry,
        output_root=output_root,
    )

    assert json.loads(oracle_registry.read_text(encoding="utf-8")) == []
    assert summary["task_status_counts"]["BLOCKED_CONTAMINATION"] == 1


def test_requires_20_distinct_pairs(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    duplicate_cases = _cases(19) + [{"input": [0], "output": 0}]
    _write_jsonl_gz(
        source_root / "train.jsonl.gz",
        [
            {
                "task_id": "hard-candidate",
                "difficulty": "Hard",
                "input_output": duplicate_cases,
            }
        ],
    )
    _write_jsonl_gz(source_root / "test.jsonl.gz", [])
    manifest = tmp_path / "source.json"
    _write_json(
        manifest,
        {
            "source_repository": "fixture/source",
            "source_revision": "fixture",
            "dataset_version": "v0",
            "train_path": "train.jsonl.gz",
            "train_blob_sha": "a",
            "test_path": "test.jsonl.gz",
            "test_blob_sha": "b",
        },
    )
    candidates = tmp_path / "candidates.json"
    _write_json(
        candidates,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:hard-candidate",
                "problem_slug": "hard-candidate",
            }
        ],
    )
    readiness = tmp_path / "readiness.json"
    _write_json(
        readiness,
        [
            {
                "canonical_task_id": "leetcode:weekly:1:hard-candidate",
                "difficulty_evidence_status": "SUPPORTED",
                "contamination_status": "ELIGIBLE",
            }
        ],
    )

    output_root = tmp_path / "out"
    summary = register_leetcode_oracle_sources(
        source_root=source_root,
        source_manifest_path=manifest,
        candidates_path=candidates,
        admission_readiness_path=readiness,
        oracle_registry_output_path=tmp_path / "oracles.json",
        output_root=output_root,
    )
    assert summary["registered_source_suite_count"] == 0
    assert (
        summary["task_status_counts"]["EXTERNAL_ORACLE_TEST_COUNT_INSUFFICIENT"]
        == 1
    )
