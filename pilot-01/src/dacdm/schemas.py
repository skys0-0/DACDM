from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TaskTier(StrEnum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class ModelTier(StrEnum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class SnapshotStatus(StrEnum):
    PINNED = "PINNED"
    ROLLING_ALIAS = "ROLLING_ALIAS"
    ARCHIVED_EVIDENCE_ONLY = "ARCHIVED_EVIDENCE_ONLY"
    UNVERIFIABLE = "UNVERIFIABLE"


class TaskRecord(StrictModel):
    task_id: str = Field(min_length=1)
    source: Literal["humaneval", "mbpp", "leetcode"]
    task_tier: TaskTier
    public_release_date: date
    source_url: HttpUrl | None = None
    canonical_statement_hash: str = Field(min_length=40)


class ModelRecord(StrictModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    exact_model_id: str = Field(min_length=1)
    model_tier: ModelTier
    snapshot_status: SnapshotStatus
    public_launch_date: date
    training_cutoff_date: date | None = None
    first_verified_date: date | None = None
    last_verified_date: date | None = None
    evidence_url: HttpUrl | None = None
    retrieved_at: datetime


class PricingRecord(StrictModel):
    provider: str
    exact_model_id: str
    effective_from: date
    effective_to: date | None = None
    input_usd_per_million_tokens: float = Field(ge=0)
    output_usd_per_million_tokens: float = Field(ge=0)
    source_url: HttpUrl
    retrieved_at: datetime


class HardwareIndexRecord(StrictModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$")
    index_value: float = Field(gt=0)
    base_period: Literal["2024-01"] = "2024-01"
    source: str
    retrieved_at: datetime
    method_note: str


class ContaminationDecision(StrictModel):
    task_id: str
    exact_model_id: str
    eligible: bool
    reason_code: str
    task_release_date: date
    training_cutoff_date: date | None
    model_launch_date: date
    evidence_ref: str | None = None


class ExecutionObservation(StrictModel):
    observation_id: str
    task_id: str
    date: date
    model: str
    exact_model_id: str
    model_tier: ModelTier
    pass_1: float = Field(ge=0, le=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0, le=2)
    latency_sec: float = Field(ge=0)
    api_cost_usd: float = Field(ge=0)
    agent_overhead_alpha: float | None = Field(default=0, ge=0)
    meets_threshold: bool
    hardware_perf_index: float | None = Field(default=None, gt=0)
    exclude_contamination: bool
    prompt_template_version: Literal["coding-direct-v1.0"]
    raw_response_sha256: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def contamination_cannot_meet_threshold(self) -> "ExecutionObservation":
        if self.exclude_contamination and self.meets_threshold:
            raise ValueError("excluded contamination observations cannot meet confirmatory threshold")
        return self
