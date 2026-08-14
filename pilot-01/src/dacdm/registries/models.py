from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    training_cutoff_status: Literal["supported", "conflicting", "unknown"]
    training_cutoff_evidence_ids: list[str]
    pricing_record_id: str
    enabled_for_pilot: bool


class TrainingCutoffEvidenceRecord(StrictRecord):
    evidence_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    claim_type: Literal["training_cutoff"]
    claimed_cutoff: date | None = Field(default=None, strict=False)
    source_type: Literal["official", "model_card", "paper", "other"]
    source_locator: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    retrieved_at: datetime = Field(strict=False)
    evidence_text_or_summary: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low", "unknown"]
    status: Literal["supported", "conflicting", "unknown"]


class PricingEvidenceRecord(StrictRecord):
    pricing_record_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    currency: Literal["USD"]
    input_unit_price: float = Field(ge=0)
    output_unit_price: float = Field(ge=0)
    unit_basis: Literal["1M_tokens"]
    effective_or_observed_at: datetime = Field(strict=False)
    source_locator: str = Field(min_length=1)
    retrieved_at: datetime = Field(strict=False)
