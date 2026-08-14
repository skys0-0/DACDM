from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "protocol_frozen_v1.0.yaml"

EXPECTED = {
    "quality_thresholds": {"humaneval": 0.80, "mbpp": 0.75, "leetcode_hard": 0.60},
    "ccr_rolling_window_months": 6,
    "h4_minimum_annual_deflated_decline": 0.15,
    "contamination_k4_threshold": 0.30,
}


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("protocol manifest must be a mapping")
    return data


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity requires SHA-1.


def validate_protocol_integrity(path: Path = MANIFEST) -> list[str]:
    manifest = load_manifest(path)
    errors: list[str] = []
    constants = manifest.get("registered_constants", {})
    for key, expected in EXPECTED.items():
        if constants.get(key) != expected:
            errors.append(f"registered constant drift: {key}")

    for section in ("protocol", "implementation_freeze", "sdd"):
        item = manifest[section]
        target = (ROOT / item["path"]).resolve()
        if not target.is_file():
            errors.append(f"missing frozen document: {section}: {target}")
            continue
        actual = git_blob_sha(target)
        if actual != item["git_blob_sha"]:
            errors.append(f"frozen document drift: {section}: expected {item['git_blob_sha']}, got {actual}")
    return errors
