from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .models import (
    HistoricalSnapshotEvidenceRecord,
    ModelIdentityEvidenceRecord,
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
    identities, identity_errors = _load(
        root / "model_identity_evidence.json", ModelIdentityEvidenceRecord
    )
    cutoffs, cutoff_errors = _load(
        root / "training_cutoff_evidence.json", TrainingCutoffEvidenceRecord
    )
    snapshots, snapshot_errors = _load(
        root / "historical_snapshot_evidence.json", HistoricalSnapshotEvidenceRecord
    )
    prices, price_errors = _load(root / "pricing.json", PricingEvidenceRecord)
    errors.extend(
        model_errors + identity_errors + cutoff_errors + snapshot_errors + price_errors
    )

    for label, values in (
        ("task_id", [record.task_id for record in tasks]),
        ("model_id", [record.model_id for record in models]),
        ("model_identity_evidence_id", [record.evidence_id for record in identities]),
        ("training_cutoff_evidence_id", [record.evidence_id for record in cutoffs]),
        ("historical_snapshot_evidence_id", [record.evidence_id for record in snapshots]),
        ("pricing_record_id", [record.pricing_record_id for record in prices]),
    ):
        for duplicate in sorted(_duplicates(values)):
            errors.append(f"duplicate {label}: {duplicate}")

    model_ids = {record.model_id for record in models}
    identity_ids = {record.evidence_id for record in identities}
    identities_by_id = {record.evidence_id: record for record in identities}
    cutoff_ids = {record.evidence_id for record in cutoffs}
    cutoffs_by_id = {record.evidence_id: record for record in cutoffs}
    snapshot_ids = {record.evidence_id for record in snapshots}
    pricing_ids = {record.pricing_record_id for record in prices}

    for model in models:
        referenced_identities: list[ModelIdentityEvidenceRecord] = []
        for evidence_id in model.identity_evidence_ids:
            if evidence_id not in identity_ids:
                errors.append(
                    f"model {model.model_id}: unresolved model identity evidence {evidence_id}"
                )
                continue
            identity = identities_by_id[evidence_id]
            referenced_identities.append(identity)
            if identity.model_id != model.model_id:
                errors.append(
                    f"model {model.model_id}: identity evidence {evidence_id} belongs to "
                    f"{identity.model_id}"
                )

        supported_identity = any(
            evidence.model_id == model.model_id
            and evidence.claim_type == "model_identity"
            and evidence.claimed_provider_model_name == model.provider_model_name
            and evidence.status == "supported"
            for evidence in referenced_identities
        )
        if not supported_identity:
            errors.append(
                f"model {model.model_id}: canonical registry entry requires supported "
                "first-party model_identity evidence matching provider_model_name"
            )

        if model.public_launch_date is not None:
            supported_launch_date = any(
                evidence.model_id == model.model_id
                and evidence.claim_type == "public_launch_date"
                and evidence.claimed_provider_model_name == model.provider_model_name
                and evidence.claimed_public_launch_date == model.public_launch_date
                and evidence.status == "supported"
                for evidence in referenced_identities
            )
            if not supported_launch_date:
                errors.append(
                    f"model {model.model_id}: public launch date requires matching "
                    "supported public_launch_date evidence"
                )

        referenced_cutoffs: list[TrainingCutoffEvidenceRecord] = []
        for evidence_id in model.training_cutoff_evidence_ids:
            if evidence_id not in cutoff_ids:
                errors.append(
                    f"model {model.model_id}: unresolved training cutoff evidence {evidence_id}"
                )
                continue
            cutoff = cutoffs_by_id[evidence_id]
            referenced_cutoffs.append(cutoff)
            if cutoff.model_id != model.model_id:
                errors.append(
                    f"model {model.model_id}: training cutoff evidence {evidence_id} belongs to "
                    f"{cutoff.model_id}"
                )

        if model.training_cutoff_status == "unknown":
            if model.training_cutoff_evidence_ids:
                errors.append(
                    f"model {model.model_id}: unknown cutoff must not reference affirmative evidence"
                )
        elif model.training_cutoff_status == "supported":
            if not any(evidence.status == "supported" for evidence in referenced_cutoffs):
                errors.append(
                    f"model {model.model_id}: supported cutoff requires supported "
                    "training cutoff evidence"
                )
        elif model.training_cutoff_status == "conflicting":
            if not any(evidence.status == "conflicting" for evidence in referenced_cutoffs):
                errors.append(
                    f"model {model.model_id}: conflicting cutoff requires conflicting "
                    "training cutoff evidence"
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

    for identity_evidence in identities:
        if identity_evidence.model_id not in model_ids:
            errors.append(
                "model identity evidence "
                f"{identity_evidence.evidence_id}: unknown model {identity_evidence.model_id}"
            )

    for cutoff_evidence in cutoffs:
        if cutoff_evidence.model_id not in model_ids:
            errors.append(
                f"evidence {cutoff_evidence.evidence_id}: unknown model {cutoff_evidence.model_id}"
            )

    for snapshot_evidence in snapshots:
        if snapshot_evidence.model_id not in model_ids:
            errors.append(
                "historical snapshot evidence "
                f"{snapshot_evidence.evidence_id}: unknown model {snapshot_evidence.model_id}"
            )

    for price in prices:
        if price.model_id not in model_ids:
            errors.append(f"pricing {price.pricing_record_id}: unknown model {price.model_id}")

    return errors
