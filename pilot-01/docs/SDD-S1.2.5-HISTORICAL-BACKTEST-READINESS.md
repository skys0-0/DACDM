# S1.2.5 — Historical Backtest Readiness

Status: PASSED / READY FOR S1.3 / EXPLORATORY ONLY
Date: 2026-08-14

## 1. Purpose

S1.2.5 is a short calibration stage inserted before S1.3. It verifies that Pilot 01 can reconstruct point-in-time model economics and prepare a hardware-efficiency baseline without changing the frozen confirmatory protocol.

This stage does **not** claim that DACDM, H2, H3, or H4 is validated or falsified.

## 2. Research-integrity boundary

All outputs from the 10-task HumanEval exercise are labelled:

`EXPLORATORY_PIPELINE_CALIBRATION_NOT_CONFIRMATORY_EVIDENCE`

No threshold, kill criterion, effect-size target, contamination rule, model-tier rule, bootstrap rule, or registered regression specification may be changed because of S1.2.5 results.

Historical observations remain subject to Implementation Freeze IF-01. A historical model result is admissible only when an exact historical snapshot is callable/verified or sufficient archived observation exists. Otherwise the cell is `NA` / `HISTORICAL_SNAPSHOT_UNAVAILABLE`. No current or successor model may be substituted.

## 3. Frozen external datasets

### 3.1 AI Price Index

Source: `RoninForge/ai-price-index` on Hugging Face.

Frozen revision:

`82835a9bcf888b394483fc7b41ffc17c661608bf`

Frozen CSV SHA-256:

`93be1cffe6225ee3439510bb2fee50243074b0d8ef63b5e23473c9e96b1dfd9c`

Snapshot size: 110,915 bytes.

The S1.2.5 point-in-time filter resolves 112 OpenAI/Anthropic input/output price rows overlapping 2024–2026. The source retains effective-from/effective-to windows, first-party source URLs, source kind, validation date, and confidence fields.

The dataset is an evidence aggregator, not unquestioned ground truth. Confirmatory price observations must retain first-party provenance and may require independent verification.

### 3.2 Epoch AI Machine Learning Hardware

Source: Epoch AI Machine Learning Hardware CSV.

Frozen retrieval date: `2026-08-14`  
Frozen live CSV URL: `https://epoch.ai/data/ml_hardware.csv`  
Frozen CSV SHA-256:

`a3cb0d6d51a37b6a6baea58052d61375bc5a4cfbc9551ef9ddb92f85454f4d16`

Snapshot size: 97,246 bytes.

The live snapshot contains fields including release date, release price, tensor-FP16/BF16 performance, FP8/FP4/FP32/FP16 performance, power draw, max performance, price-performance, and ML OP/s.

The frozen live CSV exposes nominal `Release price (USD)` rather than the inflation-adjusted release-price series used in Epoch's published price-performance analysis. Therefore the 36-month S1.2.5 hardware series is explicitly labelled a **nominal-price readiness preview**, not the final IF-07 hardware deflator.

## 4. Deterministic 10-task micro-backtest sample

Selection was frozen before S1.3 model/evidence population:

1. take frozen HumanEval task IDs from `registries/tasks.json`;
2. compute `SHA256(task_id)`;
3. sort ascending by digest;
4. select the first 10.

Frozen task IDs:

- `humaneval:134`
- `humaneval:62`
- `humaneval:117`
- `humaneval:87`
- `humaneval:37`
- `humaneval:35`
- `humaneval:66`
- `humaneval:89`
- `humaneval:53`
- `humaneval:52`

A 30-cell task-year matrix is frozen for 10 tasks × {2024, 2025, 2026}.

Every cell is currently `UNASSESSED_PENDING_S1_3`, because model registry, historical-snapshot evidence, and admissible historical capability observations have deliberately not yet been populated. This is the correct readiness outcome: S1.2.5 must not fabricate historical minimum costs before IF-01 evidence exists.

## 5. Minimum-cost calculation after S1.3 evidence population

For each admissible model/task/date observation, the backtest layer will require:

- task pass/fail;
- input tokens;
- output tokens;
- point-in-time input price;
- point-in-time output price;
- total USD execution cost;
- provenance status;
- historical snapshot availability status.

For each task/date, minimum cost is calculated only among successful admissible observations. Missing historical capability evidence remains NA rather than being inferred from a later model or current price.

## 6. Hardware readiness calculation

S1.2.5 confirms that a 2024–2026 monthly performance-per-dollar preview can be reproduced from the frozen Epoch snapshot and normalized to `2024-01 = 1`.

For the current live snapshot, the preview prioritizes `Tensor-FP16/BF16 performance (FLOP/s)` for ML-oriented performance and divides by nominal release USD. This preview is physically and semantically separated from the final H4 deflator.

The later primary IF-07 index must still specify and freeze:

- preferred Epoch source/evidence;
- inflation/price-deflation method;
- normalization `2024-01 = 1`;
- log-linear interpolation between supported anchors;
- no primary extrapolation outside supported observations;
- formula/version metadata and supported date bounds.

## 7. Frozen artifacts

- `registries/external_data_sources.json`
- `data/external/ai_price_index/82835a9bcf888b394483fc7b41ffc17c661608bf/ai_price_index.csv`
- `data/external/epoch_ai/2026-08-14/ml_hardware.csv`
- `data/external/S1_2_5_SOURCE_METADATA.json`
- `backtest/s1_2_5/snapshot_metadata.json`
- `backtest/s1_2_5/microbacktest_tasks.json`
- `backtest/s1_2_5/microbacktest_matrix.csv`
- `backtest/s1_2_5/openai_anthropic_price_history.csv`
- `backtest/s1_2_5/hardware_efficiency_preview.csv`
- `backtest/s1_2_5/schema_gap_report.md`

## 8. Schema gaps carried into S1.3

S1.2.5 establishes that S1.3 must explicitly support:

- pricing variation (`input` / `output`);
- `effective_from` / `effective_to` validity windows;
- source kind, confidence, validation date, and first-party price source URL;
- model public launch date;
- historical snapshot availability and evidence status;
- immutable external snapshot revision/SHA-256/retrieval provenance;
- hardware index formula version, price basis, normalization month, interpolation method, and supported date bounds.

The existing one-current-price-per-model shape is insufficient for historical backtesting and must be replaced before S1.3 population.

## 9. Exit gate result

PASSED:

- external source bytes frozen and hashed;
- Hugging Face price snapshot pinned to immutable revision;
- Epoch live snapshot frozen by exact bytes, timestamp, and SHA-256;
- 112 historical OpenAI/Anthropic price rows resolved for the calibration window;
- deterministic 10-task HumanEval selection frozen;
- 30 task-year cells frozen without historical substitution;
- 36-month hardware readiness series generated;
- the limitation of nominal Epoch release prices explicitly documented;
- exploratory outputs separated from confirmatory Pilot 01 results;
- Pilot 01 CI and the S1.2.5 freeze workflow are green.

S1.3 Model Registry + Training-Cutoff / Historical-Snapshot / Pricing Evidence design may now begin. S1.2.5 does not authorize confirmatory interpretation of the calibration outputs.
