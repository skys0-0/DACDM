from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .models import (
    HistoricalSnapshotEvidenceRecord,
    ModelRegistryRecord,
    PricingEvidenceRecord,
    TaskRegistryRecord,
    TrainingCutoffEvidenceRecord,
)

T = TypeVar("T", bound=BaseModel)
REGISTRY_ROOT = Path(__file__).resolve().parents[3] / "registries"


def _load(path: Path, model: type[T]) -> tuple[list[T], list[str]]:
    if not path.exists():
        return [], [f"missing registry: {path.relative_to(REGISTRY_ROOT.parent)}"]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [], [f"cannot read {path.name}: {exc}"]
    if not isinstance(raw, list):
        return [], [f"{path.name}: root must be a JSON array"]
    records: list[T] = []
    errors: list[str] = []
    for index, item in enumerate(raw):
        try:
            records.append(model.model_validate(item))
        except ValidationError as exc:
            errors.append(f"{path.name}[{index}]: {exc}")
    return records, errors


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_registry_files(root: Path = REGISTRY_ROOT) -> list[str]:
    tasks, errors = _load(root / "tasks.json", TaskRegistryRecord)
    models, model_errors = _load(root / "models.json", ModelRegistryRecord)
    cutoffs, cutoff_errors = _load(
        root / "training_cutoff_evidence.json", TrainingCutoffEvidenceRecord
    )
    snapshots, snapshot_errors = _load(
        root / "historical_snapshot_evidence.json", HistoricalSnapshotEvidenceRecord
    )
    prices, price_errors = _load(root / "pricing.json", PricingEvidenceRecord)
    errors.extend(model_errors + cutoff_errors + snapshot_errors + price_errors)

    for label, values in (
        ("task_id", [record.task_id for record in tasks]),
        ("model_id", [record.model_id for record in models]),
        ("training_cutoff_evidence_id", [record.evidence_id for record in cutoffs]),
        ("historical_snapshot_evidence_id", [record.evidence_id for record in snapshots]),
        ("pricing_record_id", [record.pricing_record_id for record in prices]),
    ):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate {label}: {duplicate}")

    model_ids = {record.model_id for record in models}
    cutoff_ids = {record.evidence_id for record in cutoffs}
    snapshot_ids = {record.evidence_id for record in snapshots}
    pricing_ids = {record.pricing_record_id for record in prices}

    for model in models:
        for evidence_id in model.training_cutoff_evidence_ids:
            if evidence_id not in cutoff_ids:
                errors.append(
                    f"model {model.model_id}: unresolved training cutoff evidence {evidence_id}"
                )
        for evidence_id in model.historical_snapshot_evidence_ids:
            if evidence_id not in snapshot_ids:
                errors.append(
                    f"model {model.model_id}: unresolved historical snapshot evidence {evidence_id}"
                )
        for pricing_record_id in model.pricing_record_ids:
            if pricing_record_id not in pricing_ids:
                errors.append(
                    f"model {model.model_id}: unresolved pricing record {pricing_record_id}"
                )
        if model.training_cutoff_status == "unknown" and model.training_cutoff_evidence_ids:
            errors.append(
                f"model {model.model_id}: unknown cutoff must not reference affirmative evidence"
            )

    for evidence in cutoffs:
        if evidence.model_id not in model_ids:
            errors.append(f"evidence {evidence.evidence_id}: unknown model {evidence.model_id}")

    for evidence in snapshots:
        if evidence.model_id not in model_ids:
            errors.append(
                f"historical snapshot evidence {evidence.evidence_id}: unknown model {evidence.model_id}"
            )

    for price in prices:
        if price.model_id not in model_ids:
            errors.append(f"pricing {price.pricing_record_id}: unknown model {price.model_id}")

    return errors
