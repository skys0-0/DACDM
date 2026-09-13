from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PHASE_LABEL = "S1.3.7_METADATA_CANDIDATE_UNIVERSE_NOT_CONFIRMATORY_ADMISSION"
WEEKLY_RE = re.compile(r"^weekly-contest-(\d+)$")
PROBLEM_URL_RE = re.compile(r"https://leetcode\.com/problems/([a-z0-9-]+)")
TITLE_RE = re.compile(
    r"^#\s*\[(?P<frontend_id>\d+)\.\s*(?P<title>.+?)\]"
    r"\(https://leetcode\.com/problems/(?P<slug>[a-z0-9-]+)\)\s*$",
    re.MULTILINE,
)
DIFFICULTY_RE = re.compile(r"^difficulty:\s*(Easy|Medium|Hard)\s*$", re.MULTILINE)


class LeetCodeFreezeError(ValueError):
    """Raised when the deterministic S1.3.7 metadata freeze cannot be completed."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_array(path: Path) -> list[dict[str, Any]]:
    raw = _load_json(path)
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise LeetCodeFreezeError(f"expected JSON array of objects: {path}")
    return raw


def _load_object(path: Path) -> dict[str, Any]:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise LeetCodeFreezeError(f"expected JSON object: {path}")
    return raw


def _read_prefix(path: Path, limit: int = 32768) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read(limit)


def _problem_metadata_index(source_root: Path) -> dict[str, dict[str, str]]:
    solution_root = source_root / "solution"
    if not solution_root.is_dir():
        raise LeetCodeFreezeError(f"missing solution directory: {solution_root}")

    index: dict[str, dict[str, str]] = {}
    duplicates: set[str] = set()
    for path in solution_root.rglob("README_EN.md"):
        prefix = _read_prefix(path)
        difficulty_match = DIFFICULTY_RE.search(prefix)
        if difficulty_match is None:
            continue
        title_match = TITLE_RE.search(prefix)
        if title_match is None:
            url_match = PROBLEM_URL_RE.search(prefix)
            if url_match is None:
                continue
            slug = url_match.group(1)
            frontend_id = ""
            title = path.parent.name
        else:
            slug = title_match.group("slug")
            frontend_id = title_match.group("frontend_id")
            title = title_match.group("title").strip()

        relative_path = path.relative_to(source_root).as_posix()
        row = {
            "problem_slug": slug,
            "frontend_question_id": frontend_id,
            "title": title,
            "difficulty": difficulty_match.group(1),
            "difficulty_evidence_path": relative_path,
            "official_problem_url": f"https://leetcode.com/problems/{slug}",
        }
        if slug in index and index[slug]["difficulty_evidence_path"] != relative_path:
            duplicates.add(slug)
        index[slug] = row

    if duplicates:
        raise LeetCodeFreezeError(
            "duplicate problem metadata slugs: " + ", ".join(sorted(duplicates))
        )
    if not index:
        raise LeetCodeFreezeError("no LeetCode problem metadata found")
    return index


def _utc_datetime(unix_seconds: Any) -> datetime:
    if isinstance(unix_seconds, bool) or not isinstance(unix_seconds, (int, float)):
        raise LeetCodeFreezeError(f"invalid contest_start_time: {unix_seconds!r}")
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def _month_bounds(value: str) -> tuple[date, date]:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise LeetCodeFreezeError(f"invalid cutoff month: {value!r}") from exc
    if parsed.month == 12:
        next_month = date(parsed.year + 1, 1, 1)
    else:
        next_month = date(parsed.year, parsed.month + 1, 1)
    first = date(parsed.year, parsed.month, 1)
    last = date.fromordinal(next_month.toordinal() - 1)
    return first, last


def contamination_status(
    task_release_date: date, cutoff_evidence: dict[str, Any]
) -> tuple[str, str]:
    """Apply known-cutoff contamination without inventing a day from month evidence."""
    precision = cutoff_evidence.get("cutoff_precision")
    if precision == "day":
        raw = cutoff_evidence.get("claimed_cutoff_date")
        if not isinstance(raw, str):
            return "INDETERMINATE", "CUTOFF_DAY_MISSING"
        cutoff = date.fromisoformat(raw)
        if task_release_date < cutoff:
            return "EXCLUDED", "TASK_PRECEDES_TRAINING_CUTOFF"
        return "ELIGIBLE", "TASK_ON_OR_AFTER_TRAINING_CUTOFF"

    if precision == "month":
        raw = cutoff_evidence.get("claimed_cutoff_month")
        if not isinstance(raw, str):
            return "INDETERMINATE", "CUTOFF_MONTH_MISSING"
        first, last = _month_bounds(raw)
        if task_release_date < first:
            return "EXCLUDED", "TASK_PRECEDES_TRAINING_CUTOFF_MONTH"
        if task_release_date > last:
            return "ELIGIBLE", "TASK_AFTER_TRAINING_CUTOFF_MONTH"
        return "INDETERMINATE", "TASK_WITHIN_CUTOFF_MONTH_PRECISION_BOUNDARY"

    return "INDETERMINATE", "CUTOFF_PRECISION_UNKNOWN"


def _supported_cutoff(
    model: dict[str, Any], cutoff_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    rows = [
        cutoff_by_id[str(evidence_id)]
        for evidence_id in model.get("training_cutoff_evidence_ids", [])
        if str(evidence_id) in cutoff_by_id
        and cutoff_by_id[str(evidence_id)].get("status") == "supported"
    ]
    return rows[0] if len(rows) == 1 else None


def _global_status(per_model: list[dict[str, str]]) -> str:
    statuses = {row["status"] for row in per_model}
    if "EXCLUDED" in statuses:
        return "EXCLUDED"
    if "INDETERMINATE" in statuses:
        return "INDETERMINATE"
    if statuses == {"ELIGIBLE"}:
        return "ELIGIBLE"
    return "INDETERMINATE"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise LeetCodeFreezeError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def freeze_leetcode_weekly_hard(
    *,
    source_root: Path,
    source_manifest_path: Path,
    models_path: Path,
    cutoffs_path: Path,
    static_tasks_path: Path,
    candidate_output_path: Path,
    output_root: Path,
    freeze_date: date,
    source_archive_sha256: str | None = None,
) -> dict[str, Any]:
    source_manifest = _load_object(source_manifest_path)
    models = _load_array(models_path)
    cutoffs = _load_array(cutoffs_path)
    static_tasks = _load_array(static_tasks_path)
    cutoff_by_id = {str(row.get("evidence_id")): row for row in cutoffs}

    contest_path = source_root / str(
        source_manifest.get("contest_metadata_path", "solution/contest.json")
    )
    contests = _load_array(contest_path)
    metadata_by_slug = _problem_metadata_index(source_root)

    window_start = date(2024, 1, 1)
    selected_contests: list[dict[str, Any]] = []
    all_selected_problem_count = 0
    resolved_problem_rows: list[dict[str, Any]] = []

    for contest in contests:
        slug = contest.get("contest_title_slug")
        if not isinstance(slug, str):
            continue
        match = WEEKLY_RE.fullmatch(slug)
        if match is None:
            continue
        started = _utc_datetime(contest.get("contest_start_time"))
        release_date = started.date()
        if release_date < window_start or release_date > freeze_date:
            continue
        question_slugs = contest.get("question_slugs")
        if not isinstance(question_slugs, list) or not all(
            isinstance(value, str) and value for value in question_slugs
        ):
            raise LeetCodeFreezeError(f"invalid question_slugs for {slug}")

        contest_number = int(match.group(1))
        selected_contests.append(
            {
                "contest_number": contest_number,
                "contest_slug": slug,
                "contest_start_time_utc": started.isoformat().replace("+00:00", "Z"),
                "release_date": release_date.isoformat(),
                "problem_count": len(question_slugs),
            }
        )
        all_selected_problem_count += len(question_slugs)
        for problem_slug in question_slugs:
            metadata = metadata_by_slug.get(problem_slug)
            if metadata is None:
                raise LeetCodeFreezeError(
                    f"missing problem metadata for {slug}: {problem_slug}"
                )
            resolved_problem_rows.append(
                {
                    **metadata,
                    "contest_number": contest_number,
                    "contest_slug": slug,
                    "contest_start_time_utc": started.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "release_date": release_date.isoformat(),
                }
            )

    if not selected_contests:
        raise LeetCodeFreezeError("no Weekly Contests in the frozen observation window")
    selected_contests.sort(key=lambda row: int(row["contest_number"]))

    hard_rows = [row for row in resolved_problem_rows if row["difficulty"] == "Hard"]
    if not hard_rows:
        raise LeetCodeFreezeError("no Hard problems in frozen Weekly Contest window")

    candidates: list[dict[str, Any]] = []
    model_summary_counter: dict[str, Counter[str]] = {
        str(model["model_id"]): Counter() for model in models
    }
    global_counter: Counter[str] = Counter()

    for row in hard_rows:
        canonical_task_id = (
            f"leetcode:weekly:{row['contest_number']}:{row['problem_slug']}"
        )
        release_date = date.fromisoformat(str(row["release_date"]))
        per_model: list[dict[str, str]] = []
        for model in models:
            model_id = str(model["model_id"])
            cutoff = _supported_cutoff(model, cutoff_by_id)
            if cutoff is None:
                status, reason = (
                    "INDETERMINATE",
                    "SUPPORTED_CUTOFF_NOT_UNIQUELY_RESOLVED",
                )
            else:
                status, reason = contamination_status(release_date, cutoff)
            per_model.append({"model_id": model_id, "status": status, "reason": reason})
            model_summary_counter[model_id][status] += 1

        global_status = _global_status(per_model)
        global_counter[global_status] += 1
        candidates.append(
            {
                "canonical_task_id": canonical_task_id,
                "contest_number": row["contest_number"],
                "contest_slug": row["contest_slug"],
                "contest_start_time_utc": row["contest_start_time_utc"],
                "release_date": row["release_date"],
                "problem_slug": row["problem_slug"],
                "frontend_question_id": row["frontend_question_id"],
                "title": row["title"],
                "difficulty": "Hard",
                "official_problem_url": row["official_problem_url"],
                "official_contest_url": (
                    f"https://leetcode.com/contest/{row['contest_slug']}/"
                ),
                "mirror_repository": source_manifest.get("source_repository"),
                "mirror_revision": source_manifest.get("source_revision"),
                "contest_metadata_path": source_manifest.get(
                    "contest_metadata_path", "solution/contest.json"
                ),
                "difficulty_evidence_path": row["difficulty_evidence_path"],
                "selection_sha256": hashlib.sha256(
                    canonical_task_id.encode("utf-8")
                ).hexdigest(),
                "per_model_contamination": per_model,
                "current_model_global_contamination_status": global_status,
                "oracle_status": "PENDING_IF09",
                "confirmatory_task_status": "NOT_ADMITTED_ORACLE_PENDING",
                "resource_cap_applied": False,
                "phase_label": PHASE_LABEL,
            }
        )

    candidates.sort(
        key=lambda row: (int(row["contest_number"]), str(row["problem_slug"]))
    )
    _write_json(candidate_output_path, candidates)

    model_summary_rows: list[dict[str, Any]] = []
    for model in models:
        model_id = str(model["model_id"])
        counts = model_summary_counter[model_id]
        model_summary_rows.append(
            {
                "model_id": model_id,
                "hard_candidate_count": len(candidates),
                "contamination_excluded": counts["EXCLUDED"],
                "contamination_eligible": counts["ELIGIBLE"],
                "contamination_indeterminate": counts["INDETERMINATE"],
                "phase_label": PHASE_LABEL,
            }
        )
    _write_csv(output_root / "model_contamination_summary.csv", model_summary_rows)

    static_count = len(static_tasks)
    hard_count = len(candidates)
    current_global_excluded = global_counter["EXCLUDED"]
    static_source_denominator = static_count + hard_count
    optimistic_static_source_excluded = static_count + current_global_excluded
    best_case_fraction = static_count / static_source_denominator
    current_fraction = optimistic_static_source_excluded / static_source_denominator
    all_weekly_upper_bound_denominator = static_count + all_selected_problem_count
    all_weekly_best_case_fraction = static_count / all_weekly_upper_bound_denominator
    k4_sensitivity = {
        "status": "INTERPRETATION_SENSITIVITY_ONLY_NOT_FORMAL_K4_DECISION",
        "threshold": 0.30,
        "static_humaneval_mbpp_task_count": static_count,
        "leetcode_weekly_hard_metadata_candidate_count": hard_count,
        "leetcode_current_global_contamination_excluded": current_global_excluded,
        "leetcode_current_global_contamination_indeterminate": global_counter[
            "INDETERMINATE"
        ],
        "leetcode_current_global_contamination_eligible": global_counter["ELIGIBLE"],
        "static_source_denominator_including_hard_candidates": static_source_denominator,
        "current_excluded_fraction_under_static_source_denominator": current_fraction,
        "best_case_fraction_if_every_hard_candidate_were_clean": best_case_fraction,
        "all_weekly_problem_count_in_window": all_selected_problem_count,
        "all_weekly_best_case_fraction_if_every_weekly_problem_were_clean": (
            all_weekly_best_case_fraction
        ),
        "above_30pct_even_under_all_weekly_best_case": (
            all_weekly_best_case_fraction > 0.30
        ),
        "interpretation_note": (
            "These calculations test a denominator interpretation that includes the frozen "
            "HumanEval/MBPP task sources plus LeetCode metadata candidates. They do not "
            "formally evaluate K4 because the protocol does not resolve the denominator "
            "ambiguity and LeetCode tasks are not confirmatory-admitted until IF-09 oracles "
            "are available. The all-weekly calculation is an intentionally generous upper "
            "bound, not a protocol dataset definition."
        ),
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "k4_denominator_sensitivity.json", k4_sensitivity)

    by_year = Counter(str(row["release_date"])[:4] for row in candidates)
    summary = {
        "status": "METADATA_CANDIDATE_UNIVERSE_FROZEN_ORACLE_PENDING",
        "freeze_date": freeze_date.isoformat(),
        "window_start": window_start.isoformat(),
        "selected_weekly_contest_count": len(selected_contests),
        "all_weekly_problem_count": all_selected_problem_count,
        "hard_metadata_candidate_count": hard_count,
        "hard_candidates_by_year": dict(sorted(by_year.items())),
        "oldest_selected_contest": selected_contests[0],
        "newest_selected_contest": selected_contests[-1],
        "resource_cap": None,
        "sampling_rule": "ALL_METADATA_HARD_CANDIDATES_NO_RESOURCE_CAP",
        "current_global_contamination_counts": dict(sorted(global_counter.items())),
        "oracle_status": "PENDING_IF09",
        "confirmatory_admitted_task_count": 0,
        "paid_inference_permitted": False,
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "summary.json", summary)

    source_snapshot = {
        "source_repository": source_manifest.get("source_repository"),
        "source_revision": source_manifest.get("source_revision"),
        "contest_metadata_path": source_manifest.get("contest_metadata_path"),
        "contest_metadata_blob_sha": source_manifest.get("contest_metadata_blob_sha"),
        "source_license": source_manifest.get("source_license"),
        "source_archive_sha256": source_archive_sha256,
        "freeze_date": freeze_date.isoformat(),
        "metadata_use_only": True,
        "official_problem_url_template": "https://leetcode.com/problems/{problem_slug}",
        "official_contest_url_template": (
            "https://leetcode.com/contest/weekly-contest-{contest_number}/"
        ),
        "phase_label": PHASE_LABEL,
    }
    _write_json(output_root / "source_snapshot.json", source_snapshot)
    return summary
