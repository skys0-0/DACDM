# Dynamic AI Compute Demand Model (DACDM)

**Complexity Migration, Cognitive Commoditization, and the Dynamics of AI Infrastructure Demand**

**Conceptual Originator:** CHAU HUNG SAN / 辛秋雄  
**Version:** 1.0  
**Published:** 2026-08-14  
**DOI:** https://doi.org/10.5281/zenodo.21930795  
**Status:** Conceptual framework published; Pilot 01 protocol frozen; empirical validation pending.

## Overview

The Dynamic AI Compute Demand Model (DACDM) is a conceptual research framework for analyzing AI compute demand as a dynamic interaction between workload growth, task complexity, model and hardware efficiency, complexity migration, and substitution across execution pathways.

Rather than assuming that growth in AI usage translates proportionally into growth in accelerator demand, DACDM examines how previously difficult tasks may migrate toward cheaper and more efficient execution pathways as models, hardware, routing, caching, distillation, procedural memory, software optimization, and other forms of compression improve.

The framework does **not** assert that GPU or electricity demand must decline. It provides a falsifiable mechanism for studying when AI activity can continue rising while marginal demand for frontier compute, GPU capacity, or electricity grows more slowly, plateaus, or falls.

## Research Status

- **DACDM Conceptual Framework v1.0:** Frozen and publicly released. It is a conceptual working-paper framework, **not an empirically validated forecasting model**. No claim of empirical support is made at this stage.
- **DACDM Pilot 01 — Code Generation Complexity Compression:** Frozen empirical protocol dated 2026-08-14. It is the first pre-registered attempt to subject H2–H4 to falsification in the code-generation domain.
- **Empirical results:** Pending. Pilot results are intended to be reported regardless of whether they support or falsify the proposed mechanism.

## Repository Structure

```text
DACDM/
├── README.md
├── LICENSE
├── CITATION.cff
├── REFERENCES.bib
├── framework/
│   └── DACDM_Conceptual_Framework_v1.0.md
├── protocols/
│   └── DACDM_Pilot_01_Protocol_v1.0.md
└── docs/
    └── ZENODO_FINAL_METADATA.md
```

PDF and DOCX release files are archived in the Zenodo record associated with DOI `10.5281/zenodo.21930795`.

## Core Hypotheses

The v1.0 framework defines eight testable hypotheses:

- **H1 — Workload Growth Deceleration**
- **H2 — Complexity Migration**
- **H3 — Frontier Share Decline**
- **H4 — Compression Beyond Hardware**
- **H5 — GPU Elasticity Decline**
- **H6 — Novelty Counterforce**
- **H7 — Replacement Wedge**
- **H8 — Power Bottleneck Interaction**

The central empirical contest is between **Novel Complexity Creation** and **Complexity Compression**.

## Pilot 01

Pilot 01 focuses on code generation and asks whether, for a fixed set of programming tasks, the minimum-cost execution pathway that clears a fixed quality threshold shifts from frontier-tier models toward mid- or small-tier models over the 2024–2026 period at a rate exceeding hardware-efficiency improvements alone.

The protocol contains frozen quality thresholds, contamination rules, model-tier definitions, agent-overhead treatment, fixed-effects regression design, bootstrap uncertainty estimation, minimum effect thresholds, and explicit falsification criteria.

## Versioning and Research Integrity

Version 1.0 is treated as a frozen public research record. Later empirical findings or methodological revisions should be released as subsequent versions rather than silently rewriting the v1.0 research record. The Pilot 01 amendment policy prohibits post-hoc adjustment of its kill criteria or minimum effect threshold except for objectively verifiable critical data errors under the protocol's stated amendment rules.

## Authorship and AI Assistance

Conceptual synthesis and DACDM formulation are attributed to **CHAU HUNG SAN (辛秋雄)**. Drafting, structuring, and literature synthesis were AI-assisted. This attribution does not assert peer review, institutional affiliation, or priority over independently developed unpublished work.

## Citation

Preferred citation metadata is provided in [`CITATION.cff`](CITATION.cff).

Zenodo record: https://doi.org/10.5281/zenodo.21930795

## License

Research papers, protocols, documentation, and other non-code materials in this repository are licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. See [`LICENSE`](LICENSE).
