from __future__ import annotations

import ast
import gzip
import hashlib
import html
import json
import re
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PHASE_LABEL = "S1.3.10_EDGE_CASE_AND_EXECUTABLE_HARNESS_VALIDATION"
DOCKER_IMAGE = "python:3.12-slim-bookworm"
MIN_REGISTERED_TESTS = 20


class LeetCodeOracleValidationError(ValueError):
    """Raised when S1.3.10 validation cannot be completed reproducibly."""


@dataclass(frozen=True)
class BoundConstraint:
    name: str
    kind: str
    low: int
    high: int


_NUM = r"-?\d+(?:\s*(?:\^|\*\*)\s*\d+)?"
_LENGTH_RE = re.compile(
    rf"(?P<low>{_NUM})\s*<=\s*(?P<name>[A-Za-z_]\w*)\.length\s*<=\s*(?P<high>{_NUM})"
)
_INDEX_LENGTH_RE = re.compile(
    rf"(?P<low>{_NUM})\s*<=\s*(?P<name>[A-Za-z_]\w*)\[i\]\.length\s*<=\s*(?P<high>{_NUM})"
)
_ELEMENT_RE = re.compile(
    rf"(?P<low>{_NUM})\s*<=\s*(?P<name>[A-Za-z_]\w*)\[i\]\s*<=\s*(?P<high>{_NUM})"
)
_SCALAR_RE = re.compile(
    rf"(?P<low>{_NUM})\s*<=\s*(?P<name>[A-Za-z_]\w*)\s*<=\s*(?P<high>{_NUM})"
)
_LEN_FN_RE = re.compile(
    rf"(?P<low>{_NUM})\s*<=\s*len\((?P<name>[A-Za-z_]\w*)\)\s*<=\s*(?P<high>{_NUM})"
)
_INPUT_PARAM_RE = re.compile(r"(\w+)\s*=\s*(.+?)(?=,\s*\w+\s*=|$)")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = _load_json(path)
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise LeetCodeOracleValidationError(f"expected JSON array of objects: {path}")
    return raw


def _load_object(path: Path) -> dict[str, Any]:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise LeetCodeOracleValidationError(f"expected JSON object: {path}")
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
            raise LeetCodeOracleValidationError(f"source manifest missing {split}_path")
        path = source_root / raw_path
        if not path.is_file():
            raise LeetCodeOracleValidationError(f"missing frozen source file: {path}")
        file_hashes[split] = _sha256_file(path)
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise LeetCodeOracleValidationError(
                        f"non-object dataset row {split}:{line_number}"
                    )
                slug = _normalize_slug(row.get("task_id"))
                if not slug:
                    raise LeetCodeOracleValidationError(
                        f"dataset row missing task_id {split}:{line_number}"
                    )
                if slug in index:
                    raise LeetCodeOracleValidationError(
                        f"duplicate normalized source task_id: {slug}"
                    )
                index[slug] = (split, row)
    return index, file_hashes


def _integer_power(base: int, exponent: int) -> int:
    if exponent < 0:
        raise ValueError("negative exponents are not supported in constraint bounds")
    result = 1
    for _ in range(exponent):
        result *= base
    return result


def _parse_int_token(token: str) -> int:
    compact = re.sub(r"\s+", "", token)
    if "**" in compact:
        base, exponent = compact.split("**", 1)
        return _integer_power(int(base), int(exponent))
    if "^" in compact:
        base, exponent = compact.split("^", 1)
        return _integer_power(int(base), int(exponent))
    return int(compact)


def _plain_description(text: str) -> str:
    with_sup = re.sub(
        r"<sup[^>]*>(.*?)</sup>",
        lambda match: "^" + re.sub(r"<[^>]+>", "", match.group(1)),
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_tags = re.sub(r"<[^>]+>", " ", with_sup)
    normalized = html.unescape(without_tags).replace("≤", "<=").replace("≥", ">=")
    return re.sub(r"\s+", " ", normalized)


def extract_bound_constraints(problem_description: str) -> list[BoundConstraint]:
    text = _plain_description(problem_description)
    found: set[BoundConstraint] = set()
    patterns = (
        (_INDEX_LENGTH_RE, "index_length"),
        (_LENGTH_RE, "length"),
        (_LEN_FN_RE, "length"),
        (_ELEMENT_RE, "element"),
        (_SCALAR_RE, "scalar"),
    )
    for pattern, kind in patterns:
        for match in pattern.finditer(text):
            try:
                low = _parse_int_token(match.group("low"))
                high = _parse_int_token(match.group("high"))
            except ValueError:
                continue
            if low > high:
                continue
            found.add(
                BoundConstraint(
                    name=match.group("name"),
                    kind=kind,
                    low=low,
                    high=high,
                )
            )
    return sorted(found, key=lambda item: (item.name, item.kind, item.low, item.high))


def parse_input_params(input_str: str) -> dict[str, Any]:
    normalized = (
        input_str.replace("null", "None")
        .replace("true", "True")
        .replace("false", "False")
    )
    params: dict[str, Any] = {}
    for match in _INPUT_PARAM_RE.finditer(normalized):
        key = match.group(1).strip()
        value_str = match.group(2).strip()
        try:
            params[key] = ast.literal_eval(value_str)
        except (SyntaxError, ValueError):
            continue
    return params


def _constraint_values(constraint: BoundConstraint, params: dict[str, Any]) -> list[int]:
    value = params.get(constraint.name)
    if constraint.kind == "scalar":
        if isinstance(value, bool) or not isinstance(value, int):
            return []
        return [value]
    if constraint.kind == "length":
        if isinstance(value, (str, list, tuple)):
            return [len(value)]
        return []
    if constraint.kind == "index_length":
        if not isinstance(value, (list, tuple)):
            return []
        return [len(item) for item in value if isinstance(item, (str, list, tuple))]
    if constraint.kind == "element":
        if not isinstance(value, (list, tuple)):
            return []
        return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]
    return []


def classify_constraint_coverage(
    problem_description: str, input_output: object
) -> dict[str, Any]:
    constraints = extract_bound_constraints(problem_description)
    if not isinstance(input_output, list):
        return {
            "constraint_count": len(constraints),
            "mapped_constraint_count": 0,
            "ordinary_case_supported": False,
            "edge_case_supported": False,
            "ordinary_case_count": 0,
            "edge_case_count": 0,
        }

    ordinary_case_count = 0
    edge_case_count = 0
    mapped_constraints: set[BoundConstraint] = set()
    for case in input_output:
        if not isinstance(case, dict) or not isinstance(case.get("input"), str):
            continue
        params = parse_input_params(case["input"])
        case_ordinary = False
        case_edge = False
        for constraint in constraints:
            values = _constraint_values(constraint, params)
            if not values:
                continue
            mapped_constraints.add(constraint)
            for value in values:
                if value == constraint.low or value == constraint.high:
                    case_edge = True
                elif constraint.low < value < constraint.high:
                    case_ordinary = True
        ordinary_case_count += int(case_ordinary)
        edge_case_count += int(case_edge)

    return {
        "constraint_count": len(constraints),
        "mapped_constraint_count": len(mapped_constraints),
        "ordinary_case_supported": ordinary_case_count > 0,
        "edge_case_supported": edge_case_count > 0,
        "ordinary_case_count": ordinary_case_count,
        "edge_case_count": edge_case_count,
    }


def _source_row_hash(row: dict[str, Any]) -> str:
    material = {
        "task_id": row.get("task_id"),
        "question_id": row.get("question_id"),
        "difficulty": row.get("difficulty"),
        "estimated_date": row.get("estimated_date"),
        "entry_point": row.get("entry_point"),
        "input_output": row.get("input_output"),
        "test": row.get("test"),
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def _reference_program(row: dict[str, Any]) -> str:
    prompt = row.get("prompt")
    completion = row.get("completion")
    test = row.get("test")
    entry_point = row.get("entry_point")
    values = (prompt, completion, test, entry_point)
    if not all(isinstance(value, str) and value for value in values):
        raise LeetCodeOracleValidationError(
            f"source row lacks executable reference fields: {row.get('task_id')}"
        )
    return f"{prompt}\n{completion}\n{test}\ncheck({entry_point})\n"


def _docker_image_digest(image: str) -> str:
    subprocess.run(["docker", "pull", image], check=True, capture_output=True, text=True)
    result = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{json .RepoDigests}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    repo_digests = json.loads(result.stdout.strip())
    if not isinstance(repo_digests, list) or not repo_digests:
        raise LeetCodeOracleValidationError(f"Docker image digest unavailable for {image}")
    return str(repo_digests[0])


def _run_program_in_sandbox(
    program_path: Path, *, container_name: str, image: str, timeout_seconds: int = 20
) -> str:
    absolute_parent = program_path.parent.resolve()
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        "none",
        "--read-only",
        "--memory",
        "768m",
        "--cpus",
        "1",
        "--pids-limit",
        "64",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65534:65534",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=64m",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        f"{absolute_parent}:/work:ro",
        image,
        "python",
        "-I",
        "-B",
        "/work/program.py",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            capture_output=True,
            text=True,
        )
        return "TIMEOUT"
    if completed.returncode == 0:
        return "PASS"
    return "FAIL"


def validate_registered_oracles(
    *,
    source_root: Path,
    source_manifest_path: Path,
    oracle_registry_path: Path,
    output_root: Path,
    docker_image: str = DOCKER_IMAGE,
) -> dict[str, Any]:
    source_manifest = _load_object(source_manifest_path)
    registry = _load_array(oracle_registry_path)
    dataset_index, file_hashes = _load_dataset_rows(source_root, source_manifest)
    image_digest = _docker_image_digest(docker_image)

    status_counts: Counter[str] = Counter()
    edge_counts: Counter[str] = Counter()
    harness_counts: Counter[str] = Counter()
    validated: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="dacdm-s1-3-10-") as temp_dir:
        temp_root = Path(temp_dir)
        for position, record in enumerate(registry):
            task_id = str(record.get("canonical_task_id", ""))
            slug = _normalize_slug(record.get("problem_slug"))
            source_match = dataset_index.get(slug)
            if source_match is None:
                raise LeetCodeOracleValidationError(f"registered source row missing: {slug}")
            split, row = source_match
            expected_path = source_manifest.get(f"{split}_path")
            if expected_path != record.get("source_path"):
                raise LeetCodeOracleValidationError(f"source path drift: {task_id}")
            if file_hashes[split] != record.get("source_file_sha256"):
                raise LeetCodeOracleValidationError(f"source file hash drift: {task_id}")
            if _source_row_hash(row) != record.get("source_row_sha256"):
                raise LeetCodeOracleValidationError(f"source row hash drift: {task_id}")

            description = row.get("problem_description")
            if not isinstance(description, str):
                coverage: dict[str, Any] = {
                    "constraint_count": 0,
                    "mapped_constraint_count": 0,
                    "ordinary_case_supported": False,
                    "edge_case_supported": False,
                    "ordinary_case_count": 0,
                    "edge_case_count": 0,
                }
            else:
                coverage = classify_constraint_coverage(description, row.get("input_output"))

            if coverage["ordinary_case_supported"]:
                ordinary_status = "SUPPORTED_BY_DOCUMENTED_BOUND_INTERIOR_CASE"
            else:
                ordinary_status = "ORDINARY_CASE_EVIDENCE_INSUFFICIENT"
            if coverage["edge_case_supported"]:
                edge_status = "SUPPORTED_BY_EXACT_DOCUMENTED_CONSTRAINT_BOUND"
            else:
                edge_status = "EDGE_CASE_EVIDENCE_INSUFFICIENT"
            edge_counts[edge_status] += 1

            program = _reference_program(row)
            program_sha256 = hashlib.sha256(program.encode("utf-8")).hexdigest()
            task_dir = temp_root / f"task-{position:03d}"
            task_dir.mkdir()
            program_path = task_dir / "program.py"
            program_path.write_text(program, encoding="utf-8")
            first = _run_program_in_sandbox(
                program_path,
                container_name=f"dacdm-s1310-{position:03d}-a",
                image=docker_image,
            )
            second = _run_program_in_sandbox(
                program_path,
                container_name=f"dacdm-s1310-{position:03d}-b",
                image=docker_image,
            )
            if first == "PASS" and second == "PASS":
                harness_status = "REFERENCE_PASS_DETERMINISTIC_TWO_RUNS"
            elif first == second:
                harness_status = f"REFERENCE_{first}_DETERMINISTIC_TWO_RUNS"
            else:
                harness_status = "HARNESS_NONDETERMINISTIC_TWO_RUNS"
            harness_counts[harness_status] += 1

            numeric_count = int(record.get("distinct_registered_test_count", 0))
            if (
                numeric_count >= MIN_REGISTERED_TESTS
                and ordinary_status == "SUPPORTED_BY_DOCUMENTED_BOUND_INTERIOR_CASE"
                and edge_status == "SUPPORTED_BY_EXACT_DOCUMENTED_CONSTRAINT_BOUND"
                and harness_status == "REFERENCE_PASS_DETERMINISTIC_TWO_RUNS"
            ):
                task_status = "TASK_LEVEL_IF09_READY_GLOBAL_INFERENCE_GATE_BLOCKED"
                if09_status = "IF09_ORACLE_READY"
            else:
                task_status = "TASK_LEVEL_IF09_NOT_READY"
                if09_status = "IF09_ORACLE_INCOMPLETE"
            status_counts[task_status] += 1

            validated.append(
                {
                    "canonical_task_id": task_id,
                    "problem_slug": slug,
                    "distinct_registered_test_count": numeric_count,
                    "constraint_count": coverage["constraint_count"],
                    "mapped_constraint_count": coverage["mapped_constraint_count"],
                    "ordinary_case_count": coverage["ordinary_case_count"],
                    "edge_case_count": coverage["edge_case_count"],
                    "ordinary_case_evidence_status": ordinary_status,
                    "edge_case_evidence_status": edge_status,
                    "reference_program_sha256": program_sha256,
                    "reference_run_1": first,
                    "reference_run_2": second,
                    "executable_harness_validation_status": harness_status,
                    "if09_status": if09_status,
                    "confirmatory_task_admission_status": task_status,
                    "model_results_inspected": False,
                    "paid_inference_permitted": False,
                    "phase_label": PHASE_LABEL,
                }
            )

    _write_json(output_root / "task_validation.json", validated)
    ready_count = status_counts["TASK_LEVEL_IF09_READY_GLOBAL_INFERENCE_GATE_BLOCKED"]
    summary = {
        "status": "TASK_LEVEL_IF09_VALIDATION_COMPLETE_GLOBAL_INFERENCE_GATE_BLOCKED",
        "registered_suite_count": len(registry),
        "if09_ready_task_count": ready_count,
        "if09_not_ready_task_count": len(registry) - ready_count,
        "task_status_counts": dict(sorted(status_counts.items())),
        "edge_evidence_status_counts": dict(sorted(edge_counts.items())),
        "harness_status_counts": dict(sorted(harness_counts.items())),
        "docker_image_requested": docker_image,
        "docker_image_frozen_digest": image_digest,
        "sandbox_policy": {
            "network": "none",
            "rootfs": "read_only",
            "memory": "768m",
            "cpus": 1,
            "pids_limit": 64,
            "capabilities": "ALL_DROPPED",
            "no_new_privileges": True,
            "user": "65534:65534",
            "tmpfs": "/tmp noexec",
            "reference_runs_per_task": 2,
        },
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": "S1.3.11_GLOBAL_TASK_UNIVERSE_AND_K4_DENOMINATOR_FREEZE",
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "summary.json", summary)
    return summary
