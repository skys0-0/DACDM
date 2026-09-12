from __future__ import annotations

"""Build the DOI-bearing S1.6 publication package from the frozen RC1 narrative.

This is deliberately a one-way publication renderer: it reads RC1 and S1.3.13,
writes only the separate S1.6 directory, and rejects altered scientific invariants.
"""

import argparse
import html
import hashlib
import json
import re
import shutil
import zipfile
from datetime import date
from pathlib import Path
from typing import Any


PILOT_ROOT = Path(__file__).resolve().parents[1]
RC_ROOT = PILOT_ROOT / "results" / "pilot01-preinference-termination-publication-rc1"
SOURCE_ROOT = PILOT_ROOT / "results" / "pilot01-preinference-termination-v1.0"
OUT_ROOT = PILOT_ROOT / "results" / "pilot01-preinference-termination-publication-s1-6"
PHASE = "S1.6_ZENODO_DRAFT_DOI_RESERVATION_AND_FINAL_PDF_DOCX_RENDER"


class S16BuildError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise S16BuildError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_frozen_guards() -> None:
    k4 = _load_json(SOURCE_ROOT / "K4_FINAL_ASSESSMENT.json")
    if k4.get("formal_k4_status") != "K4_TRIGGERED":
        raise S16BuildError("S1.3.13 K4 status is not frozen as K4_TRIGGERED")
    expected = {
        "denominator_count": 1301,
        "excluded_count": 1165,
        "eligible_count": 132,
        "indeterminate_count": 4,
        "k4_threshold": 0.30,
        "model_results_inspected": False,
        "paid_inference_permitted": False,
    }
    for key, expected_value in expected.items():
        if k4.get(key) != expected_value:
            raise S16BuildError(f"immutable S1.3.13 guard failed: {key}")

    rc = _load_json(RC_ROOT / "RC_STATUS.json")
    for key in (
        "k4_threshold_changed",
        "k4_arithmetic_changed",
        "denominator_membership_changed",
        "anchor_model_set_changed",
        "model_results_inspected",
        "paid_inference_performed",
    ):
        if rc.get(key) is not False:
            raise S16BuildError(f"RC1 guard failed: {key}")


def _clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.replace("<br>", "")
    text = text.replace("**", "")
    return text


def _write_docx(markdown_path: Path, docx_path: Path, doi: str) -> None:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt, RGBColor
    except ImportError as exc:
        raise S16BuildError("python-docx is required for S1.6 DOCX rendering") from exc

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(7)

    for style_name, size in (("Title", 20), ("Heading 1", 14), ("Heading 2", 11.5)):
        style = doc.styles[style_name]
        style.font.name = "Aptos Display"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("DACDM Pilot 01 | Reserved DOI: " + doi).font.size = Pt(8)

    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("# "):
            paragraph = doc.add_paragraph(style="Title")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.add_run(_clean_inline(line[2:]))
        elif line.startswith("## "):
            doc.add_paragraph(_clean_inline(line[3:]), style="Heading 1")
        elif line.startswith("### "):
            doc.add_paragraph(_clean_inline(line[4:]), style="Heading 2")
        elif line.startswith("| ") and "|" in line[2:]:
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                if not re.fullmatch(r"[| :\-]+", lines[index]):
                    table_lines.append(lines[index])
                index += 1
            if table_lines:
                rows = [[_clean_inline(cell.strip()) for cell in row.strip("|").split("|")]
                        for row in table_lines]
                table = doc.add_table(rows=0, cols=len(rows[0]))
                table.style = "Table Grid"
                for row_number, cells in enumerate(rows):
                    target = table.add_row().cells
                    for cell, content in zip(target, cells, strict=True):
                        cell.text = content
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = Pt(2)
                            for run in paragraph.runs:
                                run.font.size = Pt(9)
                                if row_number == 0:
                                    run.bold = True
            continue
        elif line.startswith("- "):
            doc.add_paragraph(_clean_inline(line[2:]), style="List Bullet")
        elif re.match(r"^\d+\. ", line):
            doc.add_paragraph(_clean_inline(re.sub(r"^\d+\. ", "", line)), style="List Number")
        elif line.startswith("```"):
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            paragraph = doc.add_paragraph("\n".join(code))
            for run in paragraph.runs:
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
        else:
            doc.add_paragraph(_clean_inline(line))
        index += 1
    doc.core_properties.title = "DACDM Pilot 01 Pre-Inference Termination Report"
    doc.core_properties.author = "CHAU HUNG SAN"
    doc.save(docx_path)


def _render_pdf(markdown_path: Path, pdf_path: Path, doi: str) -> None:
    """Render the canonical Markdown directly when the bundled LO renderer is unavailable."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise S16BuildError("reportlab is required for S1.6 PDF rendering") from exc

    pdfmetrics.registerFont(TTFont("NotoSansTC", r"C:\Windows\Fonts\NotoSansTC-VF.ttf"))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("S16Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18,
                           leading=22, alignment=TA_CENTER, spaceAfter=18)
    h1 = ParagraphStyle("S16H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13,
                        leading=16, spaceBefore=12, spaceAfter=7)
    h2 = ParagraphStyle("S16H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11,
                        leading=14, spaceBefore=9, spaceAfter=5)
    body = ParagraphStyle("S16Body", parent=styles["BodyText"], fontName="NotoSansTC", fontSize=9.5,
                          leading=13, spaceAfter=6)
    story: list[Any] = []
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(html.escape(_clean_inline(line[2:])), title))
        elif line.startswith("## "):
            story.append(Paragraph(html.escape(_clean_inline(line[3:])), h1))
        elif line.startswith("### "):
            story.append(Paragraph(html.escape(_clean_inline(line[4:])), h2))
        elif line.startswith("| ") and "|" in line[2:]:
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                if not re.fullmatch(r"[| :\-]+", lines[index]):
                    rows.append([html.escape(_clean_inline(cell.strip()))
                                 for cell in lines[index].strip("|").split("|")])
                index += 1
            if rows:
                table = Table(rows, repeatRows=1, colWidths=[3.2 * inch, 2.2 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D9D9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.extend([table, Spacer(1, 8)])
            continue
        elif line.startswith("- "):
            story.append(Paragraph("• " + html.escape(_clean_inline(line[2:])), body))
        else:
            story.append(Paragraph(html.escape(_clean_inline(line)), body))
        index += 1

    def _footer(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(A4[0] / 2, 0.45 * inch, f"DACDM Pilot 01 | Reserved DOI: {doi}")
        canvas.restoreState()

    SimpleDocTemplate(
        str(pdf_path), pagesize=A4, leftMargin=0.78 * inch, rightMargin=0.78 * inch,
        topMargin=0.72 * inch, bottomMargin=0.72 * inch,
    ).build(story, onFirstPage=_footer, onLaterPages=_footer)


def _write_checksums(paths: list[Path], output: Path) -> None:
    rows = [f"{_sha256(path)}  {path.name}" for path in paths]
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doi", required=True)
    parser.add_argument("--draft-url", required=True)
    parser.add_argument("--resource-subtype", required=True)
    parser.add_argument("--relation-working-paper", required=True)
    parser.add_argument("--relation-concept", required=True)
    parser.add_argument("--staging-publication-date", default=None)
    args = parser.parse_args()

    if not re.fullmatch(r"10\.5281/zenodo\.\d+", args.doi):
        raise S16BuildError("reserved DOI must be a Zenodo DOI")
    if args.staging_publication_date is not None:
        date.fromisoformat(args.staging_publication_date)
    _require_frozen_guards()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    report_source = RC_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_RC1.md"
    report_text = report_source.read_text(encoding="utf-8")
    report_text = report_text.replace(
        "**Publication release candidate:** RC1  \n"
        "**RC freeze phase:** `S1.5_PUBLICATION_RELEASE_CANDIDATE_AND_ZENODO_METADATA_FREEZE`  ",
        "**Publication source:** frozen RC1  \n"
        "**S1.6 release phase:** `S1.6_ZENODO_DRAFT_DOI_RESERVATION_AND_FINAL_PDF_DOCX_RENDER`  ",
        1,
    )
    report_text = report_text.replace(
        "**Zenodo publication status:** not published",
        "**Reserved Zenodo DOI:** " + args.doi + "  \n"
        "**Zenodo draft record:** " + args.draft_url + "  \n"
        "**Zenodo publication status:** draft only - not published",
        1,
    )
    report_text = report_text.replace(
        "## Abstract",
        "## Zenodo draft provenance\n\n"
        "This standalone Zenodo record is an unpublished draft. Its DOI is reserved for this "
        "release package and does not indicate public release. The publication date remains "
        "unset until the record is published.\n\n"
        "## Abstract",
        1,
    )
    # HTML breaks preserve the source report's compact metadata presentation without
    # committing Markdown's trailing-space hard-break convention.
    report_text = report_text.replace("  \n", "<br>\n")
    final_md = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.md"
    final_md.write_text(report_text, encoding="utf-8")

    metadata = {
        "phase_label": PHASE,
        "record_scope": "SEPARATE_PILOT01_METHODOLOGICAL_TERMINATION_RECORD",
        "zenodo_draft_url": args.draft_url,
        "zenodo_draft_status": "UNPUBLISHED_DRAFT",
        "reserved_doi": args.doi,
        "publication_date": None,
        "publication_date_rule": "SET_TO_ACTUAL_DATE_RECORD_IS_FIRST_MADE_PUBLIC",
        "draft_form_publication_date_staging_value": args.staging_publication_date,
        "draft_form_publication_date_finalization_required": args.staging_publication_date is not None,
        "resource_type": {"type": "publication", "subtype": args.resource_subtype},
        "title": "DACDM Pilot 01: Pre-Inference Termination under the Preregistered K4 Contamination Criterion",
        "creators": [{"family_name": "SAN", "given_names": "CHAU HUNG", "name_type": "personal"}],
        "license": "CC-BY-4.0",
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.21930795", "relation": args.relation_working_paper},
            {"identifier": "10.5281/zenodo.21930794", "relation": args.relation_concept},
        ],
        "scientific_guards": {
            "k4_threshold_changed": False,
            "k4_arithmetic_changed": False,
            "contamination_status_changed": False,
            "denominator_membership_changed": False,
            "anchor_model_evidence_changed": False,
            "model_results_inspected": False,
            "paid_model_inference_run": False,
            "zenodo_publication_performed": False,
        },
    }
    metadata_path = OUT_ROOT / "ZENODO_METADATA.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    disclosure = RC_ROOT / "AUTHORSHIP_AND_AI_ASSISTANCE.md"
    shutil.copy2(disclosure, OUT_ROOT / disclosure.name)
    docx_path = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.docx"
    _write_docx(final_md, docx_path, args.doi)
    pdf_path = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Report_v1.0.pdf"
    _render_pdf(final_md, pdf_path, args.doi)

    readme = OUT_ROOT / "README.md"
    readme.write_text(
        "# DACDM Pilot 01 S1.6 publication package\n\n"
        f"Reserved DOI: `{args.doi}`. Zenodo status: **unpublished draft**.\n\n"
        "This package is derived from the frozen RC1 publication candidate. It is separate from "
        "and does not modify `pilot-01/results/pilot01-preinference-termination-v1.0/`.\n",
        encoding="utf-8",
    )
    status = {
        "phase_label": PHASE,
        "status": "S1_6_DRAFT_DOI_RESERVED_FINAL_PACKAGE_RENDERED",
        "reserved_doi": args.doi,
        "zenodo_draft_url": args.draft_url,
        "zenodo_published": False,
        "final_pdf_docx_rendered": True,
        "scientific_result_changed": False,
        "k4_threshold_changed": False,
        "k4_arithmetic_changed": False,
        "contamination_status_changed": False,
        "denominator_membership_changed": False,
        "anchor_model_evidence_changed": False,
        "model_results_inspected": False,
        "paid_inference_performed": False,
    }
    status_path = OUT_ROOT / "S1.6_FREEZE_STATUS.json"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload_paths = [final_md, docx_path, pdf_path, metadata_path, OUT_ROOT / disclosure.name, readme, status_path]
    manifest = {
        "phase_label": PHASE,
        "reserved_doi": args.doi,
        "zenodo_draft_url": args.draft_url,
        "zenodo_published": False,
        "source_rc1_freeze_commit": "c4ab65fe1f8e9bbed9a0910eedf9d4cedbbd637f",
        "source_evidence_package_freeze_commit": "21380545bf0f2b6878fee164d18603ee96f99b11",
        "payload_files": [
            {"path": path.name, "sha256": _sha256(path), "size_bytes": path.stat().st_size}
            for path in payload_paths
        ],
        "manifest_self_hash_policy": "The manifest is frozen by the S1.6 Git commit and is not self-hashed.",
        "scientific_guards": metadata["scientific_guards"],
    }
    manifest_path = OUT_ROOT / "PUBLICATION_PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = OUT_ROOT / "SHA256SUMS.txt"
    _write_checksums(payload_paths + [manifest_path], checksums)

    archive = OUT_ROOT / "DACDM_Pilot_01_PreInference_Termination_Publication_Package_v1.0.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in payload_paths + [manifest_path, checksums]:
            package.write(path, path.name)
    (OUT_ROOT / "ZIP_SHA256.txt").write_text(
        f"{_sha256(archive)}  {archive.name}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
