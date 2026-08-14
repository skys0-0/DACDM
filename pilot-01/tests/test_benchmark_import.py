from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from dacdm.registries.benchmark_import import (
    BenchmarkImportError,
    build_task_registry,
)


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, object]], *, gzip_source: bool) -> bytes:
    payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
    raw = gzip.compress(payload, mtime=0) if gzip_source else payload
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _manifest(tmp_path: Path) -> tuple[Path, Path]:
    source_root = tmp_path / "sources"
    human_rows = [
        {
            "task_id": "HumanEval/0",
            "prompt": "def add(a, b):\n",
            "entry_point": "add",
            "test": "def check(candidate): assert candidate(1, 2) == 3",
            "canonical_solution": "    return a + b\n",
        }
    ]
    mbpp_rows = [
        {
            "task_id": 11,
            "text": "Return the square of n.",
            "code": "def square(n): return n*n",
            "test_list": ["assert square(3) == 9"],
            "test_setup_code": "",
            "challenge_test_list": [],
        }
    ]
    human_raw = _write_jsonl(
        source_root / "humaneval" / "HumanEval.jsonl.gz",
        human_rows,
        gzip_source=True,
    )
    mbpp_raw = _write_jsonl(
        source_root / "mbpp" / "mbpp.jsonl",
        mbpp_rows,
        gzip_source=False,
    )
    manifest = [
        {
            "benchmark": "humaneval",
            "expected_count": 1,
            "source_repository": "openai/human-eval",
            "source_revision": "human-rev",
            "source_path": "data/HumanEval.jsonl.gz",
            "source_blob_sha": _git_blob_sha(human_raw),
            "source_format": "jsonl.gz",
            "release_date": "2021-07-07",
            "license_ref": "human-license",
        },
        {
            "benchmark": "mbpp",
            "expected_count": 1,
            "source_repository": "google-research/google-research",
            "source_revision": "mbpp-rev",
            "source_path": "mbpp/mbpp.jsonl",
            "source_blob_sha": _git_blob_sha(mbpp_raw),
            "source_format": "jsonl",
            "release_date": "2021-08-16",
            "license_ref": "mbpp-license",
        },
    ]
    manifest_path = tmp_path / "benchmark_sources.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, source_root


def test_build_task_registry_is_deterministic(tmp_path: Path) -> None:
    manifest_path, source_root = _manifest(tmp_path)
    output_a = tmp_path / "tasks-a.json"
    output_b = tmp_path / "tasks-b.json"

    first = build_task_registry(manifest_path, source_root, output_a)
    second = build_task_registry(manifest_path, source_root, output_b)

    assert first == second
    assert output_a.read_bytes() == output_b.read_bytes()
    assert [row["task_id"] for row in first] == ["humaneval:0", "mbpp:11"]
    assert all(str(row["content_hash"]).startswith("sha256:") for row in first)


def test_reference_solution_does_not_change_experimental_content_hash(tmp_path: Path) -> None:
    manifest_path, source_root = _manifest(tmp_path)
    output = tmp_path / "tasks.json"
    original = build_task_registry(manifest_path, source_root, output)
    original_hash = next(row["content_hash"] for row in original if row["task_id"] == "humaneval:0")

    source_path = source_root / "humaneval" / "HumanEval.jsonl.gz"
    row = {
        "task_id": "HumanEval/0",
        "prompt": "def add(a, b):\n",
        "entry_point": "add",
        "test": "def check(candidate): assert candidate(1, 2) == 3",
        "canonical_solution": "    return 999\n",
    }
    new_raw = _write_jsonl(source_path, [row], gzip_source=True)
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["source_blob_sha"] = _git_blob_sha(new_raw)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    changed = build_task_registry(manifest_path, source_root, output)
    changed_hash = next(row["content_hash"] for row in changed if row["task_id"] == "humaneval:0")
    assert changed_hash == original_hash


def test_mbpp_split_is_derived_from_frozen_task_ranges(tmp_path: Path) -> None:
    manifest_path, source_root = _manifest(tmp_path)
    output = tmp_path / "tasks.json"
    records = build_task_registry(manifest_path, source_root, output)
    mbpp = next(row for row in records if row["task_id"] == "mbpp:11")
    assert mbpp["split"] == "test"


def test_source_blob_mismatch_fails_closed(tmp_path: Path) -> None:
    manifest_path, source_root = _manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest[0]["source_blob_sha"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BenchmarkImportError, match="source blob mismatch"):
        build_task_registry(manifest_path, source_root, tmp_path / "tasks.json")


def test_expected_count_mismatch_fails_closed(tmp_path: Path) -> None:
    manifest_path, source_root = _manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest[1]["expected_count"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(BenchmarkImportError, match="expected 2 rows, found 1"):
        build_task_registry(manifest_path, source_root, tmp_path / "tasks.json")
