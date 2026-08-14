# DACDM Pilot 01 — S1.3 Model / Cutoff / Historical Snapshot / Pricing Evidence

Status: IMPLEMENTATION STARTED  
Date: 2026-08-14

## 1. Objective

S1.3 converts the empty model/evidence registries into a point-in-time research evidence system suitable for 2024–2026 historical backtesting. It implements the schema gaps discovered in S1.2.5 before provider data is populated.

No paid inference is permitted in S1.3.

## 2. Registry separation

S1.3 keeps four evidence concerns separate:

- `models.json`: model identity, provider, launch date, snapshot name, access path, pilot enablement and references to evidence records;
- `training_cutoff_evidence.json`: sourced claims about model training cutoff;
- `historical_snapshot_evidence.json`: whether an exact historical model snapshot is callable, only archived observation exists, or the historical snapshot is unavailable;
- `pricing.json`: dated input/output price records with validity windows and provenance.

The separation is deliberate. Model identity is not itself evidence of training cutoff, historical availability, or price.

## 3. Model identity rules

Each model record must use a stable DACDM `model_id`. Rolling aliases are not historical snapshot identifiers. `public_launch_date` may be null when not independently verified; unknown values must remain unknown rather than inferred.

A model may reference zero or more pricing records and historical snapshot evidence records. Multiple pricing records are expected because prices vary over time and by input/output variation.

## 4. Historical snapshot evidence

Implementation Freeze IF-01 is represented directly by `availability_status`:

- `callable_exact`
- `archived_observation`
- `historical_snapshot_unavailable`
- `unknown`

`callable_exact` requires an explicit immutable or exact snapshot identifier. A current model or successor model must never substitute for a missing historical snapshot.

## 5. Training-cutoff evidence

Training cutoff evidence records preserve the claimed cutoff, source type, locator, retrieval time, summary, confidence, and status. Conflicting evidence remains conflicting; S1.3 must not silently reconcile disagreement.

## 6. Point-in-time pricing evidence

Each pricing record represents exactly one variation:

- `input`
- `output`

Each record stores:

- USD price per one million tokens;
- `effective_from`;
- nullable `effective_to`;
- source kind;
- confidence;
- first-party or supporting source URL;
- retrieval and validation timestamps;
- optional upstream dataset revision.

This replaces the earlier one-current-price-per-model design, which S1.2.5 demonstrated was insufficient for historical backtesting.

## 7. Implementation order

1. Freeze S1.3 schemas and validators.
2. Add regression tests for unresolved evidence, price validity windows, and exact-snapshot requirements.
3. Populate an initial OpenAI/Anthropic model identity set from primary sources.
4. Populate training-cutoff evidence without guessing unknown cutoffs.
5. Populate historical snapshot availability evidence under IF-01.
6. Import historical price records from the frozen AI Price Index snapshot while retaining first-party provenance.
7. Run the 10-task historical-readiness matrix only after the evidence registries can resolve model/date/price cells deterministically.

## 8. Exit gate

S1.3 is complete only when:

- schema and validator CI is green;
- selected OpenAI/Anthropic model records are populated with sourced public launch dates where available;
- every affirmative cutoff claim has evidence;
- historical snapshot availability is explicit for each model/date needed by the micro-backtest;
- historical price records preserve point-in-time validity and source provenance;
- `dacdm validate-registries` passes;
- no unavailable historical snapshot has been replaced by a current or successor model;
- no paid model API calls have occurred.
