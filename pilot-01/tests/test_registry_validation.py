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


def _identity(evidence_id: str = "identity-1") -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "model_id": "provider:model",
        "claim_type": "public_launch_date",
        "claimed_provider_model_name": "model",
        "claimed_public_launch_date": "2026-01-01",
        "source_type": "official",
        "source_locator": "fixture",
        "source_title": "fixture",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "evidence_text_or_summary": "fixture",
        "confidence": "high",
        "status": "supported",
    }


def test_unknown_cutoff_is_preserved_without_guessing(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "public_launch_date": "2026-01-01",
        "identity_evidence_ids": ["identity-1"],
        "training_cutoff_status": "unknown",
        "training_cutoff_evidence_ids": [],
        "historical_snapshot_evidence_ids": [],
        "pricing_record_ids": ["price-input", "price-output"],
        "enabled_for_pilot": False,
    }
    prices = [
        {
            "pricing_record_id": "price-input",
            "provider": "provider",
            "model_id": "provider:model",
            "variation": "input",
            "currency": "USD",
            "unit_price": 1.0,
            "unit_basis": "1M_tokens",
            "effective_from": "2026-01-01",
            "effective_to": None,
            "source_kind": "official",
            "confidence": "high",
            "source_url": "https://example.com/pricing",
            "source_locator": "fixture",
            "last_validated_at": "2026-08-14T00:00:00Z",
            "retrieved_at": "2026-08-14T00:00:00Z",
            "source_dataset_revision": None,
        },
        {
            "pricing_record_id": "price-output",
            "provider": "provider",
            "model_id": "provider:model",
            "variation": "output",
            "currency": "USD",
            "unit_price": 2.0,
            "unit_basis": "1M_tokens",
            "effective_from": "2026-01-01",
            "effective_to": None,
            "source_kind": "official",
            "confidence": "high",
            "source_url": "https://example.com/pricing",
            "source_locator": "fixture",
            "last_validated_at": "2026-08-14T00:00:00Z",
            "retrieved_at": "2026-08-14T00:00:00Z",
            "source_dataset_revision": None,
        },
    ]
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "model_identity_evidence.json", [_identity()])
    _write(tmp_path, "pricing.json", prices)
    assert validate_registry_files(tmp_path) == []


def test_launch_date_requires_identity_evidence(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "public_launch_date": "2026-01-01",
        "identity_evidence_ids": [],
        "training_cutoff_status": "unknown",
        "training_cutoff_evidence_ids": [],
        "historical_snapshot_evidence_ids": [],
        "pricing_record_ids": [],
        "enabled_for_pilot": False,
    }
    _write(tmp_path, "models.json", [model])
    errors = validate_registry_files(tmp_path)
    assert any("public launch date requires identity evidence" in error for error in errors)


def test_unresolved_evidence_reference_fails(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "public_launch_date": None,
        "identity_evidence_ids": ["missing-identity"],
        "training_cutoff_status": "supported",
        "training_cutoff_evidence_ids": ["missing-cutoff"],
        "historical_snapshot_evidence_ids": ["missing-snapshot"],
        "pricing_record_ids": ["missing-price"],
        "enabled_for_pilot": False,
    }
    _write(tmp_path, "models.json", [model])
    errors = validate_registry_files(tmp_path)
    assert any("unresolved model identity evidence" in error for error in errors)
    assert any("unresolved training cutoff evidence" in error for error in errors)
    assert any("unresolved historical snapshot evidence" in error for error in errors)
    assert any("unresolved pricing record" in error for error in errors)


def test_callable_exact_snapshot_requires_identifier(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "public_launch_date": None,
        "identity_evidence_ids": [],
        "training_cutoff_status": "unknown",
        "training_cutoff_evidence_ids": [],
        "historical_snapshot_evidence_ids": ["snap-1"],
        "pricing_record_ids": [],
        "enabled_for_pilot": False,
    }
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
    _write(tmp_path, "historical_snapshot_evidence.json", [snapshot])
    errors = validate_registry_files(tmp_path)
    assert any(
        "callable_exact historical snapshot requires snapshot_identifier" in error
        for error in errors
    )
