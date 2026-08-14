from copy import deepcopy

from dacdm.protocol import EXPECTED, load_manifest, validate_protocol_integrity


def test_frozen_documents_and_constants_match() -> None:
    assert validate_protocol_integrity() == []


def test_registered_constants_are_exact() -> None:
    manifest = load_manifest()
    constants = manifest["registered_constants"]
    for key, expected in EXPECTED.items():
        assert constants[key] == expected
    assert constants["bootstrap"]["replications"] == 1000
    assert constants["bootstrap"]["seed"] == 20260814
    assert constants["inference"]["max_infrastructure_retries"] == 2
    assert constants["prompt_template_version"] == "coding-direct-v1.0"
    assert constants["leetcode_oracle"]["minimum_distinct_tests"] == 20


def test_manifest_copy_can_detect_constant_drift() -> None:
    manifest = deepcopy(load_manifest())
    manifest["registered_constants"]["ccr_rolling_window_months"] = 12
    assert manifest["registered_constants"]["ccr_rolling_window_months"] != EXPECTED["ccr_rolling_window_months"]
