from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from dacdm.leetcode_freeze import contamination_status, freeze_leetcode_weekly_hard


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_problem(
    source_root: Path, *, problem_id: int, title: str, slug: str, difficulty: str
) -> None:
    path = (
        source_root
        / "solution"
        / "0000-0099"
        / f"{problem_id:04d}.{title}"
        / "README_EN.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"difficulty: {difficulty}\n"
        "---\n\n"
        f"# [{problem_id}. {title}](https://leetcode.com/problems/{slug})\n",
        encoding="utf-8",
    )


def _unix(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, 2, 30, tzinfo=timezone.utc).timestamp())


def test_month_precision_contamination_is_tri_state() -> None:
    cutoff = {
        "cutoff_precision": "month",
        "claimed_cutoff_month": "2024-04",
    }
    assert contamination_status(date(2024, 3, 31), cutoff)[0] == "EXCLUDED"
    assert contamination_status(date(2024, 4, 15), cutoff)[0] == "INDETERMINATE"
    assert contamination_status(date(2024, 5, 1), cutoff)[0] == "ELIGIBLE"


def test_freeze_selects_weekly_hard_metadata_only(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    _write_problem(
        source_root,
        problem_id=1,
        title="Hard Candidate",
        slug="hard-candidate",
        difficulty="Hard",
    )
    _write_problem(
        source_root,
        problem_id=2,
        title="Medium Candidate",
        slug="medium-candidate",
        difficulty="Medium",
    )
    _write_problem(
        source_root,
        problem_id=3,
        title="Old Hard",
        slug="old-hard",
        difficulty="Hard",
    )
    _write_problem(
        source_root,
        problem_id=4,
        title="Biweekly Hard",
        slug="biweekly-hard",
        difficulty="Hard",
    )

    contests = [
        {
            "contest_title_slug": "weekly-contest-399",
            "contest_start_time": _unix(2023, 12, 31),
            "question_slugs": ["old-hard"],
        },
        {
            "contest_title_slug": "weekly-contest-400",
            "contest_start_time": _unix(2024, 5, 5),
            "question_slugs": ["hard-candidate", "medium-candidate"],
        },
        {
            "contest_title_slug": "biweekly-contest-130",
            "contest_start_time": _unix(2024, 5, 11),
            "question_slugs": ["biweekly-hard"],
        },
    ]
    _write_json(source_root / "solution" / "contest.json", contests)

    manifest_path = tmp_path / "source_manifest.json"
    _write_json(
        manifest_path,
        {
            "source_repository": "fixture/leetcode",
            "source_revision": "fixture-revision",
            "contest_metadata_path": "solution/contest.json",
            "contest_metadata_blob_sha": "fixture-blob",
            "source_license": "fixture-license",
        },
    )

    models_path = tmp_path / "models.json"
    _write_json(
        models_path,
        [
            {
                "model_id": "provider:model",
                "training_cutoff_evidence_ids": ["cutoff-1"],
            }
        ],
    )
    cutoffs_path = tmp_path / "cutoffs.json"
    _write_json(
        cutoffs_path,
        [
            {
                "evidence_id": "cutoff-1",
                "status": "supported",
                "cutoff_precision": "month",
                "claimed_cutoff_month": "2024-04",
            }
        ],
    )
    tasks_path = tmp_path / "tasks.json"
    _write_json(tasks_path, [{"task_id": "humaneval:0"}])

    candidate_path = tmp_path / "leetcode_weekly_hard_candidates.json"
    output_root = tmp_path / "out"
    summary = freeze_leetcode_weekly_hard(
        source_root=source_root,
        source_manifest_path=manifest_path,
        models_path=models_path,
        cutoffs_path=cutoffs_path,
        static_tasks_path=tasks_path,
        candidate_output_path=candidate_path,
        output_root=output_root,
        freeze_date=date(2024, 12, 31),
    )

    candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
    assert len(candidates) == 1
    candidate = candidates[0]
    canonical_id = "leetcode:weekly:400:hard-candidate"
    assert candidate["canonical_task_id"] == canonical_id
    assert candidate["selection_sha256"] == hashlib.sha256(
        canonical_id.encode("utf-8")
    ).hexdigest()
    assert candidate["difficulty"] == "Hard"
    assert candidate["current_model_global_contamination_status"] == "ELIGIBLE"
    assert candidate["oracle_status"] == "PENDING_IF09"
    assert candidate["confirmatory_task_status"] == "NOT_ADMITTED_ORACLE_PENDING"
    assert candidate["resource_cap_applied"] is False

    assert summary["selected_weekly_contest_count"] == 1
    assert summary["hard_metadata_candidate_count"] == 1
    assert summary["confirmatory_admitted_task_count"] == 0
    assert summary["paid_inference_permitted"] is False
    assert summary["resource_cap"] is None

    sensitivity = json.loads(
        (output_root / "k4_denominator_sensitivity.json").read_text(encoding="utf-8")
    )
    assert sensitivity["status"] == (
        "INTERPRETATION_SENSITIVITY_ONLY_NOT_FORMAL_K4_DECISION"
    )
