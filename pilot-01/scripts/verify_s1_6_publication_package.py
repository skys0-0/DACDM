from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


PILOT_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = PILOT_ROOT / "results" / "pilot01-preinference-termination-publication-s1-6"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    status = _load(OUT_ROOT / "S1.6_FREEZE_STATUS.json")
    metadata = _load(OUT_ROOT / "ZENODO_METADATA.json")
    manifest = _load(OUT_ROOT / "PUBLICATION_PACKAGE_MANIFEST.json")
    assert status["status"] == "S1_6_DRAFT_DOI_RESERVED_FINAL_PACKAGE_RENDERED"
    assert status["zenodo_published"] is False
    assert status["model_results_inspected"] is False
    assert status["paid_inference_performed"] is False
    assert metadata["zenodo_draft_status"] == "UNPUBLISHED_DRAFT"
    assert metadata["publication_date"] is None
    assert metadata["creators"] == [{"family_name": "SAN", "given_names": "CHAU HUNG", "name_type": "personal"}]
    assert metadata["license"] == "CC-BY-4.0"
    for key, value in manifest["scientific_guards"].items():
        assert value is False, key
    for item in manifest["payload_files"]:
        path = OUT_ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert _sha256(path) == item["sha256"], item["path"]
        assert path.stat().st_size == item["size_bytes"], item["path"]
    pdf = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")
    docx = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.docx"
    assert zipfile.is_zipfile(docx)
    archive = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Publication_Package_v1.0.zip"
    assert zipfile.is_zipfile(archive)
    assert "S1.6_FREEZE_STATUS.json" in zipfile.ZipFile(archive).namelist()


if __name__ == "__main__":
    main()
