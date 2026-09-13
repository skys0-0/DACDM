from __future__ import annotations

import json
from pathlib import Path

from dacdm.registries.validator import validate_registry_files


def _write(root: Path, name: str, data: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(data), encoding="utf-8")


def _base(root: Path) -> None:
    for name in (
        "tasks.json",
        "training_cutoff_evidence.json",
        "historical_snapshot_evidence.json",
    ):
        _write(root, name, [])
    _write(
        root,
        "models.json",
        [
            {
                "model_id": "provider:model",
                "provider": "provider",
                "provider_model_name": "model",
                "model_version_or_snapshot": "snapshot",
                "access_path": "api",
                "public_launch_date": None,
                "identity_evidence_ids": ["identity-1"],
                "training_cutoff_status": "unknown",
                "training_cutoff_evidence_ids": [],
                "historical_snapshot_evidence_ids": [],
                "pricing_record_ids": ["input-1", "output-1"],
                "enabled_for_pilot": False,
            }
        ],
    )
    _write(
        root,
        "model_identity_evidence.json",
        [
            {
                "evidence_id": "identity-1",
                "model_id": "provider:model",
                "claim_type": "model_identity",
                "claimed_provider_model_name": "model",
                "claimed_public_launch_date": None,
                "source_type": "official",
                "source_locator": "fixture",
                "source_title": "fixture",
                "retrieved_at": "2026-08-14T00:00:00Z",
                "evidence_text_or_summary": "fixture",
                "confidence": "high",
                "status": "supported",
            }
        ],
    )


def _price(record_id: str, variation: str, start: str, end: str | None) -> dict[str, object]:
    return {
        "pricing_record_id": record_id,
        "provider": "provider",
        "model_id": "provider:model",
        "variation": variation,
        "currency": "USD",
        "unit_price": 1.0,
        "unit_basis": "1M_tokens",
        "effective_from": start,
        "effective_to": end,
        "source_kind": "official",
        "confidence": "high",
        "source_url": "https://example.com/pricing",
        "source_locator": "fixture",
        "last_validated_at": "2026-08-14T00:00:00Z",
        "retrieved_at": "2026-08-14T00:00:00Z",
        "source_dataset_revision": None,
    }


def test_point_in_time_input_output_pair_is_valid(tmp_path: Path) -> None:
    _base(tmp_path)
    _write(
        tmp_path,
        "pricing.json",
        [
            _price("input-1", "input", "2024-01-01", None),
            _price("output-1", "output", "2024-01-01", None),
        ],
    )
    assert validate_registry_files(tmp_path) == []


def test_overlapping_price_windows_fail(tmp_path: Path) -> None:
    _base(tmp_path)
    model = json.loads((tmp_path / "models.json").read_text(encoding="utf-8"))[0]
    model["pricing_record_ids"] = ["input-1", "input-2", "output-1"]
    _write(tmp_path, "models.json", [model])
    _write(
        tmp_path,
        "pricing.json",
        [
            _price("input-1", "input", "2024-01-01", "2024-06-01"),
            _price("input-2", "input", "2024-05-01", None),
            _price("output-1", "output", "2024-01-01", None),
        ],
    )
    errors = validate_registry_files(tmp_path)
    assert any("overlapping pricing windows" in error for error in errors)


def test_price_provider_must_match_model_provider(tmp_path: Path) -> None:
    _base(tmp_path)
    input_price = _price("input-1", "input", "2024-01-01", None)
    input_price["provider"] = "other-provider"
    _write(
        tmp_path,
        "pricing.json",
        [input_price, _price("output-1", "output", "2024-01-01", None)],
    )
    errors = validate_registry_files(tmp_path)
    assert any("does not match" in error for error in errors)
