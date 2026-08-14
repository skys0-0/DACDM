from __future__ import annotations

import json
from pathlib import Path

from dacdm.leetcode_admission import audit_leetcode_admission_readiness


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_problem(path: Path, example_count: int) -> None:
    examples = "\n".join(
        (
            f'<p><strong class="example">Example {index}:</strong></p>'
            "<p><strong>Input:</strong> x = 1</p>"
            "<p><strong>Output:</strong> 1</p>"
        )
        for index in range(1, example_count + 1)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<!-- description:start -->\n"
        + examples
        + "\n<!-- description:end -->\n"
        + "<strong>Input:</strong> solution-section-noise\n",
        encoding="utf-8",
    )


def _candidate(*, difficulty: str = "Hard", contamination: str = "ELIGIBLE") -> dict[str, object]:
    return {
        "canonical_task_id": "leetcode:weekly:400:hard-candidate",
        "contest_number": 400,
        "release_date": "2024-05-05",
        "problem_slug": "hard-candidate",
        "frontend_question_id": "1234",
        "difficulty": difficulty,
        "difficulty_evidence_path": "solution/1200-1299/1234.Hard Candidate/README_EN.md",
        "current_model_global_contamination_status": contamination,
    }


def _official(*, difficulty: str = "Hard") -> dict[str, object]:
    return {
        "problem_slug": "hard-candidate",
        "frontend_question_id": "1234",
        "title": "Hard Candidate",
        "difficulty": difficulty,
        "source_method": "official_problemset_api",
        "source_locator": "https://leetcode.com/api/problems/all/",
        "official_problem_url": "https://leetcode.com/problems/hard-candidate/",
        "retrieved_at": "2026-08-14T15:50:00Z",
    }


def test_admission_audit_verifies_difficulty_but_does_not_invent_oracle(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    evidence_path = source_root / "solution/1200-1299/1234.Hard Candidate/README_EN.md"
    _write_problem(evidence_path, 3)

    candidates = tmp_path / "candidates.json"
    official = tmp_path / "official.json"
    _write_json(candidates, [_candidate()])
    _write_json(official, [_official()])

    difficulty_out = tmp_path / "difficulty.json"
    output_root = tmp_path / "out"
    summary = audit_leetcode_admission_readiness(
        candidates_path=candidates,
        official_metadata_path=official,
        source_root=source_root,
        difficulty_evidence_output_path=difficulty_out,
        output_root=output_root,
    )

    assert summary["candidate_count"] == 1
    assert summary["difficulty_evidence_counts"] == {"SUPPORTED": 1}
    assert summary["confirmatory_admitted_task_count"] == 0
    assert summary["paid_inference_permitted"] is False
    assert summary["next_gate"] == "S1.3.9_REGISTERED_ORACLE_CONSTRUCTION"

    readiness = json.loads(
        (output_root / "task_admission_readiness.json").read_text(encoding="utf-8")
    )[0]
    assert readiness["public_statement_example_count"] == 3
    assert readiness["registered_executable_test_count"] == 0
    assert readiness["oracle_status"] == (
        "TEST_ORACLE_INSUFFICIENT_CURRENT_FROZEN_EVIDENCE"
    )
    assert readiness["confirmatory_admission_status"] == (
        "BLOCKED_ORACLE_CONSTRUCTION_REQUIRED"
    )
    assert readiness["model_results_inspected"] is False


def test_admission_audit_blocks_nonhard_official_difficulty(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    evidence_path = source_root / "solution/1200-1299/1234.Hard Candidate/README_EN.md"
    _write_problem(evidence_path, 2)

    candidates = tmp_path / "candidates.json"
    official = tmp_path / "official.json"
    _write_json(candidates, [_candidate()])
    _write_json(official, [_official(difficulty="Medium")])

    summary = audit_leetcode_admission_readiness(
        candidates_path=candidates,
        official_metadata_path=official,
        source_root=source_root,
        difficulty_evidence_output_path=tmp_path / "difficulty.json",
        output_root=tmp_path / "out",
    )

    assert summary["difficulty_evidence_counts"] == {"CONFLICTING": 1}
    assert summary["admission_status_counts"] == {"BLOCKED_DIFFICULTY_EVIDENCE": 1}
    evidence = json.loads((tmp_path / "difficulty.json").read_text(encoding="utf-8"))[0]
    assert evidence["status"] == "CONFLICTING"
    assert "OFFICIAL_DIFFICULTY_NOT_HARD" in evidence["reasons"]
