# DACDM Pilot 01 — Publication Release Candidate RC1

This directory is the external-publication release candidate created after the S1.4 adversarial review.

It is separate from and does not overwrite:

`pilot-01/results/pilot01-preinference-termination-v1.0/`

## Files

- `DACDM_Pilot_01_PreInference_Termination_Report_RC1.md` — revised publication narrative.
- `AUTHORSHIP_AND_AI_ASSISTANCE.md` — authorship, AI-assistance, and automation disclosure.
- `ZENODO_METADATA_RC1.json` — metadata freeze with live-deposit fields intentionally left unresolved.
- `PUBLICATION_MANIFEST.json` — hashes and provenance for the RC publication payload.
- `RC_STATUS.json` — release-gate state for this candidate.

## Scientific invariants

RC1 does not change the preregistered 30% K4 threshold, the S1.3.11 denominator membership, S1.3.12 contamination arithmetic, or any task contamination status. No confirmatory model-performance inference is introduced.

The external-facing result is a **pre-inference termination under the preregistered K4 contamination criterion**. The protocol mechanically classifies K4 as a falsification condition, but H2/H4 were not tested using confirmatory model-performance data.

## Why PDF/DOCX are not yet final

A DOI-bearing PDF or DOCX should be rendered only after a separate Zenodo draft has reserved the new record DOI. Publication date must also reflect the actual first-publication date. RC1 therefore freezes the narrative and metadata intent while leaving DOI/date/live relation fields unresolved.

## Next gate

`S1.6_ZENODO_DRAFT_DOI_RESERVATION_AND_FINAL_PDF_DOCX_RENDER`

No Zenodo publication is performed in S1.5.
