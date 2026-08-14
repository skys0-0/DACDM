# S1.2.5 Schema Gap Report

Status: GENERATED BEFORE S1.3 POPULATION

## Pricing registry gaps

Current S1.1 pricing records are insufficient for historical backtesting because point-in-time evidence needs `variation`, `effective_from`, `effective_to`, `source_kind`, `confidence`, `last_validated_at`, and first-party `source_url` in addition to token price. S1.3 should model these explicitly rather than collapsing a model to one current price record.

## Model/evidence registry gaps

S1.3 needs model public launch date plus an explicit historical snapshot availability/evidence status so that IF-01 can distinguish callable exact snapshots, archived observations, and `HISTORICAL_SNAPSHOT_UNAVAILABLE`. No successor/current-model substitution is allowed.

## External snapshot provenance gaps

External datasets require immutable revision/hash metadata. Hugging Face revision SHA can be pinned directly. Epoch's live CSV is mutable, so DACDM freezes exact bytes with retrieval time and SHA-256.

## Hardware registry gaps

The frozen Epoch live CSV exposes nominal `Release price (USD)` but does not expose the inflation-adjusted release-price series used in Epoch's published price-performance trend. Therefore the actual S1.2.5 Epoch snapshot is intentionally only a nominal-price readiness preview. The final IF-07 hardware deflator must separately encode its price-deflation method, source series, formula version, normalization month, interpolation method, and supported date bounds. S1.2.5 must not silently treat nominal release USD as constant 2024 USD.

## Confirmatory boundary

No S1.2.5 output may modify registered hypotheses, thresholds, kill criteria, contamination rules, bootstrap specification, model-tier rules, or the frozen Pilot 01 protocol.
