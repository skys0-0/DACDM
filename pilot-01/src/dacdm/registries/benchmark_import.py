from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


class BenchmarkImportError(ValueError):
    """Raised when a pinned benchmark source cannot be imported deterministically."""


def _git_blob_sha(data: bytes) -> str:
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload).hexdigest()


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _load_jsonl_bytes(data: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise BenchmarkImportError(f"invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise BenchmarkImportError(f"JSONL line {line_number} must be an object")
        rows.append(value)
    return rows


def _read_source(path: Path, source_format: str) -> tuple[bytes, list[dict[str, Any]]]:
    raw = path.read_bytes()
    if source_format == "jsonl":
        return raw, _load_jsonl_bytes(raw)
    if source_format == "jsonl.gz":
        try:
            unpacked = gzip.decompress(raw)
        except OSError as exc:
            raise BenchmarkImportError(f"invalid gzip source: {path}") from exc
        return raw, _load_jsonl_bytes(unpacked)
    raise BenchmarkImportError(f"unsupported source format: {source_format}")


def _humaneval_payload(row: dict[str, Any]) -> dict[str, Any]:
    required = ("task_id", "prompt", "entry_point", "test")
    missing = [key for key in required if key not in row]
    if missing:
        raise BenchmarkImportError(f"HumanEval row missing fields: {', '.join(missing)}")
    return {
        "task_id": row["task_id"],
        "prompt": row["prompt"],
        "entry_point": row["entry_point"],
        "test": row["test"],
    }


def _mbpp_payload(row: dict[str, Any]) -> dict[str, Any]:
    required = ("task_id", "text", "test_list")
    missing = [key for key in required if key not in row]
    if missing:
        raise BenchmarkImportError(f"MBPP row missing fields: {', '.join(missing)}")
    return {
        "task_id": row["task_id"],
        "text": row["text"],
        "test_list": row["test_list"],
        "test_setup_code": row.get("test_setup_code", ""),
        "challenge_test_list": row.get("challenge_test_list", []),
    }


def _canonical_task_id(benchmark: str, source_task_id: object) -> str:
    if benchmark == "humaneval":
        value = str(source_task_id)
        if value.startswith("HumanEval/"):
            value = value.split("/", 1)[1]
        return f"humaneval:{value}"
    if benchmark == "mbpp":
        return f"mbpp:{int(source_task_id)}"
    raise BenchmarkImportError(f"unsupported benchmark: {benchmark}")


def import_benchmark_source(source: dict[str, Any], source_root: Path) -> list[dict[str, Any]]:
    required_source_fields = (
        "benchmark",
        "expected_count",
        "source_repository",
        "source_revision",
        "source_path",
        "source_blob_sha",
        "source_format",
        "release_date",
        "license_ref",
    )
    missing = [key for key in required_source_fields if key not in source]
    if missing:
        raise BenchmarkImportError(f"source manifest missing fields: {', '.join(missing)}")

    benchmark = str(source["benchmark"])
    local_path = source_root / benchmark / Path(str(source["source_path"])).name
    if not local_path.exists():
        raise BenchmarkImportError(f"missing pinned source file: {local_path}")

    raw, rows = _read_source(local_path, str(source["source_format"]))
    actual_blob_sha = _git_blob_sha(raw)
    if actual_blob_sha != source["source_blob_sha"]:
        raise BenchmarkImportError(
            f"{benchmark}: source blob mismatch: expected {source['source_blob_sha']}, "
            f"got {actual_blob_sha}"
        )

    expected_count = int(source["expected_count"])
    if len(rows) != expected_count:
        raise BenchmarkImportError(
            f"{benchmark}: expected {expected_count} rows, found {len(rows)}"
        )

    records: list[dict[str, Any]] = []
    for row in rows:
        if benchmark == "humaneval":
            payload = _humaneval_payload(row)
            split = "test"
        elif benchmark == "mbpp":
            payload = _mbpp_payload(row)
            task_number = int(row["task_id"])
            if 1 <= task_number <= 10:
                split = "prompting"
            elif 11 <= task_number <= 510:
                split = "test"
            elif 511 <= task_number <= 600:
                split = "validation"
            elif 601 <= task_number <= 974:
                split = "train"
            else:
                raise BenchmarkImportError(f"MBPP task id out of frozen range: {task_number}")
        else:
            raise BenchmarkImportError(f"unsupported benchmark: {benchmark}")

        records.append(
            {
                "task_id": _canonical_task_id(benchmark, row["task_id"]),
                "benchmark": benchmark,
                "benchmark_version": str(source["source_revision"]),
                "source_ref": (
                    f"https://github.com/{source['source_repository']}/blob/"
                    f"{source['source_revision']}/{source['source_path']}"
                ),
                "source_revision": str(source["source_revision"]),
                "content_hash": _sha256_json(payload),
                "language": "python",
                "split": split,
                "license_or_terms_ref": str(source["license_ref"]),
                "release_date": str(source["release_date"]),
                "eligible": True,
                "exclusion_reason": None,
            }
        )

    return sorted(records, key=lambda item: item["task_id"])


def build_task_registry(
    manifest_path: Path,
    source_root: Path,
    output_path: Path,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise BenchmarkImportError("benchmark source manifest must be a JSON array")

    records: list[dict[str, Any]] = []
    for source in manifest:
        if not isinstance(source, dict):
            raise BenchmarkImportError("benchmark source manifest entries must be objects")
        records.extend(import_benchmark_source(source, source_root))

    task_ids = [str(record["task_id"]) for record in records]
    if len(task_ids) != len(set(task_ids)):
        raise BenchmarkImportError("duplicate canonical task_id generated")

    records.sort(key=lambda item: item["task_id"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return records
