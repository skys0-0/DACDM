import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dacdm.schemas import ExecutionObservation


def test_synthetic_fixture_validates() -> None:
    path = Path(__file__).parent / "fixtures" / "synthetic_observations.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) == 1
    observation = ExecutionObservation.model_validate(rows[0])
    assert observation.reasoning_tokens is None


def test_unknown_reasoning_tokens_remain_na() -> None:
    path = Path(__file__).parent / "fixtures" / "synthetic_observations.json"
    row = json.loads(path.read_text(encoding="utf-8"))[0]
    row["reasoning_tokens"] = None
    assert ExecutionObservation.model_validate(row).reasoning_tokens is None


def test_extra_fields_are_rejected() -> None:
    path = Path(__file__).parent / "fixtures" / "synthetic_observations.json"
    row = json.loads(path.read_text(encoding="utf-8"))[0]
    row["unregistered_magic"] = 1
    with pytest.raises(ValidationError):
        ExecutionObservation.model_validate(row)
