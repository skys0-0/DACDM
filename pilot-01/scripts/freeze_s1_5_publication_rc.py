from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


PILOT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PILOT_ROOT.parent
RC_ROOT = PILOT_ROOT / "results" / "pilot01-preinference-termination-publication-rc1"
PHASE = "S1.5_PUBLICATION_RELEASE_CANDIDATE_AND_ZENODO_METADATA_FREEZE"
NEXT_GATE = "S1.6_ZENODO_DRAFT_DOI_RESERVATION_AND_FINAL_PDF_DOCX_RENDER"
SOURCE_PACKAGE_FREEZE_COMMIT = "21380545bf0f2b6878fee164d18603ee96f99b11"
S1_3_12_FREEZE_COMMIT = "34b201ad1e00dec234d27771ce535545d99712a3"
PROTOCOL_BLOB_SHA1 = "389901146b70684b6c952a8606a5063b972645d4"


class PublicationRCError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PublicationRCError(f"expected JSON object: {path}")
    return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head_sha() -> str:
    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()


def _require_phrase(path: Path, phrase: str) -> None:
    text = path.read_text(encoding="utf-8")
    if phrase not in text:
        raise PublicationRCError(f"required publication phrase missing from {path}: {phrase}")


def main() -> None:
    if not RC_ROOT.is_dir():
        raise PublicationRCError("RC1 directory is missing")

    report = RC_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_RC1.md"
    disclosure = RC_ROOT / "AUTHORSHIP_AND_AI_ASSISTANCE.md"
    metadata_path = RC_ROOT / "ZENODO_METADATA_RC1.json"
    readme = RC_ROOT / "README.md"
    rc_status_path = RC_ROOT / "RC_STATUS.json"

    for path in (report, disclosure, metadata_path, readme, rc_status_path):
        if not path.is_file():
            raise PublicationRCError(f"required RC file missing: {path}")

    s1_3_13 = _load_json(
        PILOT_ROOT
        / "results"
        / "pilot01-preinference-termination-v1.0"
        / "K4_FINAL_ASSESSMENT.json"
    )
    s1_4 = _load_json(PILOT_ROOT / "publication-review" / "S1.4_REVIEW_STATUS.json")
    metadata = _load_json(metadata_path)
    rc_status = _load_json(rc_status_path)

    if s1_3_13.get("formal_k4_status") != "K4_TRIGGERED":
        raise PublicationRCError("S1.3.13 does not preserve K4_TRIGGERED")
    if s1_3_13.get("model_results_inspected") is not False:
        raise PublicationRCError("model performance results were inspected")
    if s1_3_13.get("paid_inference_permitted") is not False:
        raise PublicationRCError("paid inference gate is not closed")
    if s1_4.get("release_gate") != "BLOCKED_MAJOR_REVISIONS_REQUIRED":
        raise PublicationRCError("unexpected S1.4 review gate")
    if s1_4.get("scientific_result_changed") is not False:
        raise PublicationRCError("S1.4 review altered the scientific result")

    if metadata.get("phase_label") != PHASE:
        raise PublicationRCError("metadata phase label mismatch")
    if metadata.get("publication_date") is not None:
        raise PublicationRCError("publication date must remain unresolved before Zenodo publication")
    if metadata.get("reserved_doi") is not None:
        raise PublicationRCError("DOI must remain unresolved before S1.6")
    if metadata.get("zenodo_published") is not False:
        raise PublicationRCError("S1.5 must not publish Zenodo")
    creators = metadata.get("creators")
    if creators != [
        {"family_name": "SAN", "given_names": "CHAU HUNG", "name_type": "personal"}
    ]:
        raise PublicationRCError("creator metadata is not frozen as SAN / CHAU HUNG")

    if rc_status.get("k4_threshold_changed") is not False:
        raise PublicationRCError("K4 threshold changed in RC status")
    if rc_status.get("k4_arithmetic_changed") is not False:
        raise PublicationRCError("K4 arithmetic changed in RC status")
    if rc_status.get("denominator_membership_changed") is not False:
        raise PublicationRCError("denominator membership changed in RC status")
    if rc_status.get("anchor_model_set_changed") is not False:
        raise PublicationRCError("anchor model set changed in RC status")
    if rc_status.get("model_results_inspected") is not False:
        raise PublicationRCError("RC status indicates inspected model results")
    if rc_status.get("paid_inference_performed") is not False:
        raise PublicationRCError("RC status indicates paid inference")

    required_phrases = (
        "It did not explicitly define the K4 denominator or freeze the exact final test-window model membership.",
        "This exact set was frozen after S1.3.11 had already exposed pre-inference contamination sensitivity.",
        "The protocol mechanically classifies K4 as a falsification condition.",
        "The Data Dictionary later contains the opposite sign",
        "Drafting, structuring, and literature synthesis were AI-assisted.",
    )
    for phrase in required_phrases:
        _require_phrase(report, phrase)

    payload_paths = [report, disclosure, metadata_path, readme, rc_status_path]
    payload = []
    for path in payload_paths:
        payload.append(
            {
                "path": str(path.relative_to(RC_ROOT)),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )

    manifest = {
        "phase_label": PHASE,
        "candidate": "pilot01-preinference-termination-publication-rc1",
        "publication_payload_freeze_commit": _head_sha(),
        "source_evidence_package_freeze_commit": SOURCE_PACKAGE_FREEZE_COMMIT,
        "s1_3_12_k4_freeze_commit": S1_3_12_FREEZE_COMMIT,
        "protocol_git_blob_sha1": PROTOCOL_BLOB_SHA1,
        "payload_files": payload,
        "manifest_self_hash_policy": (
            "PUBLICATION_MANIFEST.json is not self-hashed because a file cannot contain its "
            "own stable cryptographic digest; its exact bytes are frozen by Git in the bot "
            "freeze commit."
        ),
        "scientific_guards": {
            "scientific_result_changed": False,
            "k4_threshold_changed": False,
            "k4_arithmetic_changed": False,
            "denominator_membership_changed": False,
            "anchor_model_set_changed": False,
            "model_results_inspected": False,
            "paid_model_inference_run": False,
            "zenodo_publication_performed": False,
        },
        "next_gate": NEXT_GATE,
    }
    (RC_ROOT / "PUBLICATION_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    freeze_status = {
        "phase_label": PHASE,
        "status": "RC1_FROZEN_READY_FOR_ZENODO_DRAFT_DOI_RESERVATION",
        "publication_payload_freeze_commit": manifest["publication_payload_freeze_commit"],
        "s1_4_major_revisions_addressed": True,
        "publication_manifest_created": True,
        "model_results_inspected": False,
        "paid_inference_performed": False,
        "reserved_doi": None,
        "zenodo_published": False,
        "final_pdf_docx_rendered": False,
        "next_gate": NEXT_GATE,
    }
    (RC_ROOT / "S1.5_FREEZE_STATUS.json").write_text(
        json.dumps(freeze_status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
