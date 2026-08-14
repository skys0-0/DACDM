from __future__ import annotations

import json
from pathlib import Path

from dacdm.registries.validator import validate_registry_files


def _write(root: Path, name: str, data: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(data), encoding="utf-8")


def _empty(root: Path) -> None:
    for name in (
        "tasks.json",
        "models.json",
        "model_identity_evidence.json",
        "training_cutoff_evidence.json",
        "historical_snapshot_evidence.json",
        "pricing.json",
    ):
        _write(root, name, [])


def _model(identity_ids: list[str], launch_date: str | None = "2026-01-01") -> dict[str, object]:
    return {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "public_launch_date": launch_date,
        "identity_evidence_ids": identity_ids,
        "training_cutoff_status": "unknown",
        "training_cutoff_evidence_ids": [],
        "historical_snapshot_evidence_ids": [],
        "pricing_record_ids": [],
        "enabled_for_pilot": False,
    }


def _identity(evidence_id: str = "identity-1") -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "model_id": "provider:model",
        "claim_type": "model_identity",
        "claimed_provider_model_name": "model",
        "claimed_public_launch_date": None,
        "source_type": "official",
        "source_locator": "fixture",
        "source_title": "fixture identity",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "evidence_text_or_summary": "fixture",
        "confidence": "high",
        "status": "supported",
    }


def _launch(evidence_id: str = "launch-1") -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "model_id": "provider:model",
        "claim_type": "public_launch_date",
        "claimed_provider_model_name": "model",
        "claimed_public_launch_date": "2026-01-01",
        "source_type": "official",
        "source_locator": "fixture",
        "source_title": "fixture launch",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "evidence_text_or_summary": "fixture",
        "confidence": "high",
        "status": "supported",
    }


def _cutoff(status: str = "supported") -> dict[str, object]:
    return {
        "evidence_id": "cutoff-1",
        "model_id": "provider:model",
        "claim_type": "training_cutoff",
        "cutoff_precision": "month",
        "claimed_cutoff_date": None,
        "claimed_cutoff_month": "2025-04",
        "source_type": "official",
        "source_locator": "fixture",
        "source_title": "fixture cutoff",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "evidence_text_or_summary": "fixture month precision",
        "confidence": "high",
        "status": status,
    }


def test_empty_registry_snapshot_is_structurally_valid(tmp_path: Path) -> None:
    _empty(tmp_path)
    assert validate_registry_files(tmp_path) == []


def test_duplicate_task_id_fails(tmp_path: Path) -> None:
    _empty(tmp_path)
    task = {
        "task_id": "humaneval:0",
        "benchmark": "humaneval",
        "benchmark_version": "test",
        "source_ref": "fixture",
        "source_revision": "fixture-rev",
        "content_hash": "sha256:" + "0" * 64,
        "language": "python",
        "split": "test",
        "license_or_terms_ref": "fixture-license",
        "release_date": None,
        "eligible": True,
        "exclusion_reason": None,
    }
    _write(tmp_path, "tasks.json", [task, task])
    assert "duplicate task_id: humaneval:0" in validate_registry_files(tmp_path)


def test_unknown_cutoff_is_preserved_without_guessing(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1", "launch-1"])
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity(), _launch()])
    assert validate_registry_files(tmp_path) == []


def test_month_precision_cutoff_is_valid_and_reconciled(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1", "launch-1"])
    model["training_cutoff_status"] = "supported"
    model["training_cutoff_evidence_ids"] = ["cutoff-1"]
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity(), _launch()])
    _write(tmp_path, "training_cutoff_evidence.json", [_cutoff()])
    assert validate_registry_files(tmp_path) == []


def test_supported_cutoff_requires_supported_evidence(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1", "launch-1"])
    model["training_cutoff_status"] = "supported"
    model["training_cutoff_evidence_ids"] = ["cutoff-1"]
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity(), _launch()])
    _write(tmp_path, "training_cutoff_evidence.json", [_cutoff(status="unknown")])
    errors = validate_registry_files(tmp_path)
    assert any("supported cutoff requires supported" in error for error in errors)


def test_month_precision_rejects_invented_day(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1", "launch-1"])
    model["training_cutoff_status"] = "supported"
    model["training_cutoff_evidence_ids"] = ["cutoff-1"]
    cutoff = _cutoff()
    cutoff["claimed_cutoff_date"] = "2025-04-30"
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity(), _launch()])
    _write(tmp_path, "training_cutoff_evidence.json", [cutoff])
    errors = validate_registry_files(tmp_path)
    assert any("month precision requires claimed_cutoff_month only" in error for error in errors)


def test_canonical_model_requires_supported_matching_identity(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["launch-1"])
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_launch()])
    errors = validate_registry_files(tmp_path)
    assert any("canonical registry entry requires supported" in error for error in errors)


def test_launch_date_requires_matching_launch_evidence(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1"])
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity()])
    errors = validate_registry_files(tmp_path)
    assert any("public launch date requires matching" in error for error in errors)


def test_unresolved_evidence_reference_fails(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["missing-identity"], launch_date=None)
    model["training_cutoff_status"] = "supported"
    model["training_cutoff_evidence_ids"] = ["missing-cutoff"]
    model["historical_snapshot_evidence_ids"] = ["missing-snapshot"]
    model["pricing_record_ids"] = ["missing-price"]
    _write(tmp_path, "models.json", [model])
    errors = validate_registry_files(tmp_path)
    assert any("unresolved model identity evidence" in error for error in errors)
    assert any("unresolved training cutoff evidence" in error for error in errors)
    assert any("unresolved historical snapshot evidence" in error for error in errors)
    assert any("unresolved pricing record" in error for error in errors)


def test_callable_exact_snapshot_requires_identifier(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = _model(["identity-1"], launch_date=None)
    model["historical_snapshot_evidence_ids"] = ["snap-1"]
    snapshot = {
        "evidence_id": "snap-1",
        "model_id": "provider:model",
        "observation_date": "2024-06-01",
        "snapshot_identifier": None,
        "availability_status": "callable_exact",
        "source_type": "official",
        "source_locator": "fixture",
        "source_title": "fixture",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "evidence_text_or_summary": "fixture",
        "confidence": "high",
    }
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity()])
    _write(tmp_path, "historical_snapshot_evidence.json", [snapshot])
    errors = validate_registry_files(tmp_path)
    assert any(
        "callable_exact historical snapshot requires snapshot_identifier" in error
        for error in errors
    )
