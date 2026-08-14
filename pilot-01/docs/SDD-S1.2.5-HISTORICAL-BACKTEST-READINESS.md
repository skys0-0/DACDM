# S1.2.5 — Historical Backtest Readiness

Status: IMPLEMENTATION STARTED / EXPLORATORY ONLY
Date: 2026-08-14

## 1. Purpose

S1.2.5 is a short calibration stage inserted before S1.3. It verifies that Pilot 01 can reconstruct point-in-time model economics and a hardware-efficiency baseline without changing the frozen confirmatory protocol.

This stage must not be used to claim that DACDM, H2, H3, or H4 is validated or falsified.

## 2. Research-integrity boundary

All outputs from the 10-task HumanEval exercise are labelled:

`EXPLORATORY_PIPELINE_CALIBRATION_NOT_CONFIRMATORY_EVIDENCE`

No threshold, kill criterion, effect-size target, contamination rule, model-tier rule, bootstrap rule, or registered regression specification may be changed because of S1.2.5 results.

Historical observations remain subject to Implementation Freeze IF-01. A historical model result is admissible only when an exact historical snapshot is callable/verified or sufficient archived observation exists. Otherwise the cell is `NA` with reason `HISTORICAL_SNAPSHOT_UNAVAILABLE`.

## 3. External datasets

### 3.1 AI Price Index

Source: RoninForge/ai-price-index on Hugging Face.

Use the pinned dataset revision recorded in `registries/external_data_sources.json`, not the moving `main` branch. Preserve the raw CSV snapshot and its SHA-256 digest.

Primary use:

- point-in-time OpenAI and Anthropic input/output token prices;
- effective-from/effective-to price windows;
- first-party source URLs and confidence/source-kind metadata;
- schema-gap testing for the DACDM Pricing Registry.

The dataset is an evidence aggregator, not unquestioned ground truth. High-impact price rows used in confirmatory analysis must retain their first-party source provenance and may require independent verification later.

### 3.2 Epoch AI Machine Learning Hardware

Source: Epoch AI Machine Learning Hardware CSV.

Epoch publishes a live CSV rather than an immutable historical file revision. Therefore S1.2.5 freezes the exact bytes retrieved, records retrieval time, SHA-256, row count, source URL, and source page metadata.

Primary use:

- verify availability of release date, ML/FP16/FP32 performance, release price, inflation-adjusted price, power draw, and related fields;
- test construction of the preliminary hardware-efficiency index required by IF-07;
- normalize the later registered hardware index to `2024-01 = 1`;
- do not extrapolate beyond supported observations in the primary analysis.

## 4. Deterministic 10-task micro-backtest

Select HumanEval tasks without manual choice:

1. take the frozen HumanEval task IDs from `registries/tasks.json`;
2. compute `SHA256(task_id)`;
3. sort ascending by digest;
4. select the first 10.

The selection must be persisted before any historical capability/cost result is examined.

The micro-backtest matrix spans 2024, 2025, and 2026 model observations where admissible. Missing historical capability evidence is retained as NA rather than substituted with a current or successor model.

## 5. Minimum calculations

For each admissible model/task/date observation:

- task pass/fail;
- input tokens;
- output tokens;
- point-in-time input price;
- point-in-time output price;
- total USD execution cost;
- provenance status;
- historical snapshot availability status.

For each task/date, calculate the minimum cost among successful admissible observations. Do not infer a missing cost from a later model or current price.

## 6. Hardware readiness calculation

S1.2.5 only tests whether an index can be reproduced from the frozen Epoch snapshot. It does not run the registered H4 inference.

The later primary index must follow IF-07:

- preferred source: Epoch AI;
- normalize `2024-01 = 1`;
- log-linear interpolation between supported anchors;
- no primary extrapolation outside the supported interval;
- alternatives are exploratory only.

## 7. Required artifacts

- `registries/external_data_sources.json`
- `data/external/ai_price_index/<revision>/ai_price_index.csv`
- `data/external/epoch_ai/<snapshot>/ml_hardware.csv`
- `data/external/SNAPSHOT_MANIFEST.json`
- deterministic 10-task selection artifact
- schema-gap report before S1.3 is frozen

## 8. Exit gate

S1.2.5 passes only when:

- external source bytes are frozen and hashed;
- AI Price Index revision is immutable;
- Epoch retrieval snapshot metadata is recorded;
- OpenAI/Anthropic historical price rows can be resolved point-in-time or explicitly marked unavailable;
- deterministic 10-task HumanEval selection is frozen;
- hardware-index construction is mechanically feasible from the snapshot or the exact blocking gap is documented;
- exploratory/calibration outputs are physically separated from confirmatory Pilot 01 results;
- CI remains green.

Only after this gate should S1.3 Model Registry + Training-Cutoff Evidence Registry be frozen.
