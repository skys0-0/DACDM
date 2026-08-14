from __future__ import annotations

import json
from pathlib import Path

from dacdm.registries.validator import validate_registry_files


def _write(root: Path, name: str, data: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(data), encoding="utf-8")


def _empty(root: Path) -> None:
    for name in ("tasks.json", "models.json", "training_cutoff_evidence.json", "pricing.json"):
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


def test_unknown_cutoff_is_preserved_without_guessing(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "training_cutoff_status": "unknown",
        "training_cutoff_evidence_ids": [],
        "pricing_record_id": "price-1",
        "enabled_for_pilot": False,
    }
    price = {
        "pricing_record_id": "price-1",
        "provider": "provider",
        "model_id": "provider:model",
        "currency": "USD",
        "input_unit_price": 0.0,
        "output_unit_price": 0.0,
        "unit_basis": "1M_tokens",
        "effective_or_observed_at": "2026-08-14T00:00:00Z",
        "source_locator": "fixture",
        "retrieved_at": "2026-08-14T00:00:00Z",
    }
    _write(tmp_path, "models.json", [model])
    _write(tmp_path, "pricing.json", [price])
    assert validate_registry_files(tmp_path) == []


def test_unresolved_evidence_reference_fails(tmp_path: Path) -> None:
    _empty(tmp_path)
    model = {
        "model_id": "provider:model",
        "provider": "provider",
        "provider_model_name": "model",
        "model_version_or_snapshot": "snapshot",
        "access_path": "api",
        "training_cutoff_status": "supported",
        "training_cutoff_evidence_ids": ["missing-evidence"],
        "pricing_record_id": "missing-price",
        "enabled_for_pilot": False,
    }
    _write(tmp_path, "models.json", [model])
    errors = validate_registry_files(tmp_path)
    assert any("unresolved training cutoff evidence" in error for error in errors)
    assert any("unresolved pricing record" in error for error in errors)
