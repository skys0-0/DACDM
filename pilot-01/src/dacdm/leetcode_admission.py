from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PHASE_LABEL = "S1.3.8_DIFFICULTY_VERIFICATION_AND_IF09_ORACLE_FEASIBILITY"
PROBLEMSET_API = "https://leetcode.com/api/problems/all/"
GRAPHQL_API = "https://leetcode.com/graphql"
DIFFICULTY_BY_LEVEL = {1: "Easy", 2: "Medium", 3: "Hard"}
GRAPHQL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
  }
}
""".strip()


class LeetCodeAdmissionError(ValueError):
    """Raised when the S1.3.8 admission-readiness audit cannot be completed."""


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise LeetCodeAdmissionError(f"expected JSON array of objects: {path}")
    return raw


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _request_json(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    attempts: int = 3,
) -> Any:
    merged_headers = {
        "User-Agent": "DACDM-Pilot-01-research-metadata-freeze/1.0",
        "Accept": "application/json",
    }
    if headers:
        merged_headers.update(headers)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, data=data, headers=merged_headers)
            with urlopen(request, timeout=30) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep((0.5, 2.0)[min(attempt, 1)])
    raise LeetCodeAdmissionError(f"official LeetCode metadata request failed: {last_error}")


def _problemset_index() -> dict[str, dict[str, Any]]:
    raw = _request_json(PROBLEMSET_API)
    if not isinstance(raw, dict):
        raise LeetCodeAdmissionError("LeetCode problemset API did not return an object")
    pairs = raw.get("stat_status_pairs")
    if not isinstance(pairs, list):
        raise LeetCodeAdmissionError("LeetCode problemset API missing stat_status_pairs")

    index: dict[str, dict[str, Any]] = {}
    for row in pairs:
        if not isinstance(row, dict):
            continue
        stat = row.get("stat")
        difficulty = row.get("difficulty")
        if not isinstance(stat, dict) or not isinstance(difficulty, dict):
            continue
        slug = stat.get("question__title_slug")
        if not isinstance(slug, str) or not slug:
            continue
        level = difficulty.get("level")
        label = DIFFICULTY_BY_LEVEL.get(level) if isinstance(level, int) else None
        if label is None:
            continue
        index[slug] = {
            "problem_slug": slug,
            "frontend_question_id": str(stat.get("frontend_question_id", "")),
            "title": str(stat.get("question__title", "")),
            "difficulty": label,
            "source_method": "official_problemset_api",
            "source_locator": PROBLEMSET_API,
        }
    return index


def _graphql_problem(slug: str) -> dict[str, Any]:
    payload = json.dumps(
        {
            "operationName": "questionData",
            "query": GRAPHQL_QUERY,
            "variables": {"titleSlug": slug},
        }
    ).encode("utf-8")
    raw = _request_json(
        GRAPHQL_API,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Referer": f"https://leetcode.com/problems/{slug}/",
        },
    )
    if not isinstance(raw, dict):
        raise LeetCodeAdmissionError(f"GraphQL response is not an object for {slug}")
    data = raw.get("data")
    question = data.get("question") if isinstance(data, dict) else None
    if not isinstance(question, dict):
        raise LeetCodeAdmissionError(f"GraphQL question metadata missing for {slug}")
    difficulty = question.get("difficulty")
    if difficulty not in {"Easy", "Medium", "Hard"}:
        raise LeetCodeAdmissionError(f"invalid GraphQL difficulty for {slug}: {difficulty!r}")
    return {
        "problem_slug": str(question.get("titleSlug", slug)),
        "frontend_question_id": str(question.get("questionFrontendId", "")),
        "title": str(question.get("title", "")),
        "difficulty": difficulty,
        "source_method": "official_graphql",
        "source_locator": GRAPHQL_API,
    }


def fetch_official_problem_metadata(
    *,
    candidates_path: Path,
    output_path: Path,
    retrieved_at: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _load_array(candidates_path)
    if retrieved_at is None:
        retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    slugs = [str(row.get("problem_slug", "")) for row in candidates]
    if not slugs or any(not slug for slug in slugs):
        raise LeetCodeAdmissionError("candidate registry contains missing problem_slug")
    if len(set(slugs)) != len(slugs):
        raise LeetCodeAdmissionError("candidate registry contains duplicate problem_slug")

    problemset: dict[str, dict[str, Any]] = {}
    problemset_error: str | None = None
    try:
        problemset = _problemset_index()
    except LeetCodeAdmissionError as exc:
        problemset_error = str(exc)

    records: list[dict[str, Any]] = []
    for slug in slugs:
        metadata = problemset.get(slug)
        if metadata is None:
            metadata = _graphql_problem(slug)
        records.append(
            {
                **metadata,
                "official_problem_url": f"https://leetcode.com/problems/{slug}/",
                "retrieved_at": retrieved_at,
                "problemset_api_error": problemset_error,
                "phase_label": PHASE_LABEL,
            }
        )

    records.sort(key=lambda row: str(row["problem_slug"]))
    _write_json(output_path, records)
    return records


def _description_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start_marker = "<!-- description:start -->"
    end_marker = "<!-- description:end -->"
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start >= 0 and end > start:
        return text[start + len(start_marker) : end]
    return text


def _public_example_count(path: Path) -> int:
    text = _description_text(path)
    explicit_examples = text.count('class="example">Example')
    inputs = text.count("<strong>Input:</strong>")
    outputs = text.count("<strong>Output:</strong>")
    paired = min(inputs, outputs)
    if explicit_examples:
        return min(explicit_examples, paired) if paired else explicit_examples
    return paired


def _difficulty_status(
    candidate: dict[str, Any], official: dict[str, Any]
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if official.get("problem_slug") != candidate.get("problem_slug"):
        reasons.append("PROBLEM_SLUG_MISMATCH")
    if official.get("difficulty") != "Hard":
        reasons.append("OFFICIAL_DIFFICULTY_NOT_HARD")
    candidate_frontend = str(candidate.get("frontend_question_id", ""))
    official_frontend = str(official.get("frontend_question_id", ""))
    if candidate_frontend and official_frontend and candidate_frontend != official_frontend:
        reasons.append("FRONTEND_QUESTION_ID_MISMATCH")
    return ("SUPPORTED" if not reasons else "CONFLICTING", reasons)


def audit_leetcode_admission_readiness(
    *,
    candidates_path: Path,
    official_metadata_path: Path,
    source_root: Path,
    difficulty_evidence_output_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    candidates = _load_array(candidates_path)
    official_rows = _load_array(official_metadata_path)
    official_by_slug = {str(row.get("problem_slug")): row for row in official_rows}
    if len(official_by_slug) != len(official_rows):
        raise LeetCodeAdmissionError("official metadata contains duplicate problem_slug")

    difficulty_evidence: list[dict[str, Any]] = []
    readiness_rows: list[dict[str, Any]] = []
    difficulty_counts: Counter[str] = Counter()
    contamination_counts: Counter[str] = Counter()
    oracle_counts: Counter[str] = Counter()
    admission_counts: Counter[str] = Counter()

    for candidate in candidates:
        slug = str(candidate.get("problem_slug", ""))
        canonical_task_id = str(candidate.get("canonical_task_id", ""))
        official = official_by_slug.get(slug)
        if official is None:
            raise LeetCodeAdmissionError(f"official difficulty evidence missing for {slug}")

        difficulty_status, difficulty_reasons = _difficulty_status(candidate, official)
        difficulty_counts[difficulty_status] += 1
        evidence_id = f"leetcode-difficulty:{slug}:{official.get('retrieved_at', 'unknown')}"
        difficulty_evidence.append(
            {
                "evidence_id": evidence_id,
                "canonical_task_id": canonical_task_id,
                "problem_slug": slug,
                "claimed_difficulty": official.get("difficulty"),
                "claimed_frontend_question_id": official.get("frontend_question_id"),
                "source_type": "official",
                "source_method": official.get("source_method"),
                "source_locator": official.get("source_locator"),
                "official_problem_url": official.get("official_problem_url"),
                "retrieved_at": official.get("retrieved_at"),
                "status": difficulty_status,
                "reasons": difficulty_reasons,
                "phase_label": PHASE_LABEL,
            }
        )

        evidence_path = candidate.get("difficulty_evidence_path")
        if not isinstance(evidence_path, str) or not evidence_path:
            raise LeetCodeAdmissionError(f"missing mirror evidence path for {canonical_task_id}")
        source_path = source_root / evidence_path
        if not source_path.is_file():
            raise LeetCodeAdmissionError(f"missing frozen mirror file: {source_path}")
        public_examples = _public_example_count(source_path)

        contamination = str(
            candidate.get("current_model_global_contamination_status", "INDETERMINATE")
        )
        contamination_counts[contamination] += 1

        # S1.3.8 does not invent hidden tests or treat statement examples as an executable oracle.
        executable_registered_tests = 0
        complete_authoritative_oracle = False
        if executable_registered_tests >= 20 or complete_authoritative_oracle:
            oracle_status = "IF09_ORACLE_READY"
        else:
            oracle_status = "TEST_ORACLE_INSUFFICIENT_CURRENT_FROZEN_EVIDENCE"
        oracle_counts[oracle_status] += 1

        if difficulty_status != "SUPPORTED":
            admission_status = "BLOCKED_DIFFICULTY_EVIDENCE"
        elif contamination != "ELIGIBLE":
            admission_status = "BLOCKED_CONTAMINATION"
        elif oracle_status != "IF09_ORACLE_READY":
            admission_status = "BLOCKED_ORACLE_CONSTRUCTION_REQUIRED"
        else:
            admission_status = "CONFIRMATORY_ADMISSIBLE_PRE_INFERENCE"
        admission_counts[admission_status] += 1

        readiness_rows.append(
            {
                "canonical_task_id": canonical_task_id,
                "problem_slug": slug,
                "contest_number": candidate.get("contest_number"),
                "release_date": candidate.get("release_date"),
                "official_difficulty": official.get("difficulty"),
                "difficulty_evidence_status": difficulty_status,
                "contamination_status": contamination,
                "public_statement_example_count": public_examples,
                "registered_executable_test_count": executable_registered_tests,
                "complete_authoritative_oracle_available": complete_authoritative_oracle,
                "oracle_status": oracle_status,
                "confirmatory_admission_status": admission_status,
                "model_results_inspected": False,
                "paid_inference_permitted": False,
                "phase_label": PHASE_LABEL,
            }
        )

    difficulty_evidence.sort(key=lambda row: str(row["canonical_task_id"]))
    readiness_rows.sort(key=lambda row: str(row["canonical_task_id"]))
    _write_json(difficulty_evidence_output_path, difficulty_evidence)
    _write_json(output_root / "task_admission_readiness.json", readiness_rows)

    examples = Counter(int(row["public_statement_example_count"]) for row in readiness_rows)
    summary = {
        "status": "DIFFICULTY_VERIFIED_ORACLE_CONSTRUCTION_REQUIRED",
        "candidate_count": len(candidates),
        "difficulty_evidence_counts": dict(sorted(difficulty_counts.items())),
        "contamination_counts": dict(sorted(contamination_counts.items())),
        "oracle_status_counts": dict(sorted(oracle_counts.items())),
        "admission_status_counts": dict(sorted(admission_counts.items())),
        "public_statement_example_count_distribution": {
            str(key): value for key, value in sorted(examples.items())
        },
        "if09_minimum_registered_tests": 20,
        "confirmatory_admitted_task_count": admission_counts[
            "CONFIRMATORY_ADMISSIBLE_PRE_INFERENCE"
        ],
        "model_results_inspected": False,
        "paid_inference_permitted": False,
        "next_gate": "S1.3.9_REGISTERED_ORACLE_CONSTRUCTION",
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "summary.json", summary)

    denominator_note = {
        "status": "K4_DENOMINATOR_INTERPRETATION_UNRESOLVED_NO_FORMAL_K4_DECISION",
        "frozen_k4_threshold": 0.30,
        "candidate_count": len(candidates),
        "difficulty_supported_count": difficulty_counts["SUPPORTED"],
        "confirmatory_admitted_task_count": summary["confirmatory_admitted_task_count"],
        "rule": (
            "S1.3.8 MUST NOT choose a K4 denominator after observing model outcomes. "
            "A denominator interpretation must be frozen before formal K4 evaluation, "
            "without changing the frozen 30% criterion itself."
        ),
        "paid_inference_permitted": False,
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "k4_denominator_gate.json", denominator_note)
    return summary
