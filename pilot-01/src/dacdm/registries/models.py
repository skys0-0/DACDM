from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TaskRegistryRecord(StrictRecord):
    task_id: str = Field(min_length=1)
    benchmark: Literal["humaneval", "mbpp", "leetcode"]
    benchmark_version: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    language: str = Field(min_length=1)
    split: str = Field(min_length=1)
    license_or_terms_ref: str = Field(min_length=1)
    release_date: date | None = Field(default=None, strict=False)
    eligible: bool
    exclusion_reason: str | None = None


class ModelRegistryRecord(StrictRecord):
    model_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    provider_model_name: str = Field(min_length=1)
    model_version_or_snapshot: str = Field(min_length=1)
    access_path: str = Field(min_length=1)
    public_launch_date: date | None = Field(default=None, strict=False)
    identity_evidence_ids: list[str]
    training_cutoff_status: Literal["supported", "conflicting", "unknown"]
    training_cutoff_evidence_ids: list[str]
    historical_snapshot_evidence_ids: list[str]
    pricing_record_ids: list[str]
    enabled_for_pilot: bool


class ModelIdentityEvidenceRecord(StrictRecord):
    evidence_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    claim_type: Literal["model_identity", "public_launch_date"]
    claimed_provider_model_name: str = Field(min_length=1)
    claimed_public_launch_date: date | None = Field(default=None, strict=False)
    source_type: Literal["official", "archived_official"]
    source_locator: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    retrieved_at: datetime = Field(strict=False)
    evidence_text_or_summary: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low", "unknown"]
    status: Literal["supported", "conflicting", "unknown"]


class TrainingCutoffEvidenceRecord(StrictRecord):
    evidence_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    claim_type: Literal["training_cutoff"]
    cutoff_precision: Literal["day", "month", "unknown"]
    claimed_cutoff_date: date | None = Field(default=None, strict=False)
    claimed_cutoff_month: str | None = Field(
        default=None, pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$"
    )
    source_type: Literal[
        "official",
        "archived_official",
        "model_card",
        "paper",
        "other",
    ]
    source_locator: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    retrieved_at: datetime = Field(strict=False)
    evidence_text_or_summary: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low", "unknown"]
    status: Literal["supported", "conflicting", "unknown"]

    @model_validator(mode="after")
    def cutoff_value_matches_precision(self) -> TrainingCutoffEvidenceRecord:
        if self.cutoff_precision == "day":
            if self.claimed_cutoff_date is None or self.claimed_cutoff_month is not None:
                raise ValueError("day precision requires claimed_cutoff_date only")
        elif self.cutoff_precision == "month":
            if self.claimed_cutoff_month is None or self.claimed_cutoff_date is not None:
                raise ValueError("month precision requires claimed_cutoff_month only")
        elif self.claimed_cutoff_date is not None or self.claimed_cutoff_month is not None:
            raise ValueError("unknown precision requires no claimed cutoff value")
        return self


class HistoricalSnapshotEvidenceRecord(StrictRecord):
    evidence_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    observation_date: date = Field(strict=False)
    snapshot_identifier: str | None = None
    availability_status: Literal[
        "callable_exact",
        "archived_observation",
        "historical_snapshot_unavailable",
        "unknown",
    ]
    source_type: Literal[
        "official",
        "archived_official",
        "benchmark_archive",
        "paper",
        "other",
    ]
    source_locator: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    retrieved_at: datetime = Field(strict=False)
    evidence_text_or_summary: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low", "unknown"]

    @model_validator(mode="after")
    def exact_snapshot_requires_identifier(self) -> HistoricalSnapshotEvidenceRecord:
        if self.availability_status == "callable_exact" and not self.snapshot_identifier:
            raise ValueError("callable_exact historical snapshot requires snapshot_identifier")
        return self


class PricingEvidenceRecord(StrictRecord):
    pricing_record_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    variation: Literal["input", "output"]
    currency: Literal["USD"]
    unit_price: float = Field(ge=0)
    unit_basis: Literal["1M_tokens"]
    effective_from: date = Field(strict=False)
    effective_to: date | None = Field(default=None, strict=False)
    source_kind: Literal[
        "official",
        "archived_official",
        "aggregator_with_first_party_source",
        "other",
    ]
    confidence: Literal["high", "medium", "low", "unknown"]
    source_url: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    last_validated_at: datetime = Field(strict=False)
    retrieved_at: datetime = Field(strict=False)
    source_dataset_revision: str | None = None

    @model_validator(mode="after")
    def validity_window_must_be_forward(self) -> PricingEvidenceRecord:
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be later than effective_from")
        return self
