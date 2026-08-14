# DACDM Pilot 01 — Execution Workspace

**Protocol:** `protocols/DACDM_Pilot_01_Protocol_v1.0.md`  
**Protocol status:** Frozen as of 2026-08-14  
**Associated framework:** DACDM Conceptual Framework v1.0  
**DOI:** https://doi.org/10.5281/zenodo.21930795

## Purpose

This directory is the execution workspace for DACDM Pilot 01 — Code Generation Complexity Compression.

The empirical implementation must follow the frozen protocol. This workspace may contain data-processing code, inference runners, analysis code, derived datasets, logs, and results, but it must not silently modify the pre-registered hypotheses, quality thresholds, contamination policy, minimum effect threshold, or kill criteria.

## Structure

```text
pilot-01/
├── README.md
├── data/
│   └── README.md
├── src/
│   └── README.md
├── analysis/
│   └── README.md
└── results/
    └── README.md
```

## Reproducibility Rules

1. Preserve raw observations and provenance whenever legally distributable.
2. Separate raw, processed, and derived data.
3. Record model name/version, execution date, pricing basis, token usage, tool calls, retries, latency, and contamination status.
4. Never overwrite results solely because they conflict with DACDM hypotheses.
5. Document exclusions and missing observations.
6. Keep exploratory analyses clearly separated from pre-registered confirmatory analyses.
7. Any protocol amendment must follow the amendment policy in the frozen Pilot 01 protocol.

## Current Status

Repository scaffold created. Data collection and empirical analysis have not yet begun in this workspace.
