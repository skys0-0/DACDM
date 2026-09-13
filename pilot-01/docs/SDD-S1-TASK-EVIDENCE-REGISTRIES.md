# S1 — Task & Evidence Registries

Status: PREPARED / NOT YET CLOSED

## 1. Objective

S1 establishes deterministic, auditable registries required before any paid Pilot 01 inference. It converts benchmark, model, training-cutoff, pricing, and contamination assumptions into versioned evidence records.

S1 does **not** run the Pilot experiment and does **not** introduce paid inference.

## 2. Scope

S1 MUST establish:

1. Task registry
2. Model registry
3. Training-cutoff evidence registry
4. Pricing registry
5. Deterministic contamination engine
6. Registry schemas and validators
7. Frozen evidence snapshots / provenance
8. Tests and CI coverage

## 3. Implementation principles

- No backward compatibility layers.
- Use the simplest implementation that fully satisfies Pilot 01.
- Registries are data-first, explicit, reviewable, and version controlled.
- No network dependency during validation/tests.
- Unknown evidence remains `unknown`; it MUST NOT be silently inferred.
- Evidence and interpretation are separate fields.
- Raw task content and task identifiers MUST be reproducible from a pinned source/version.

## 4. Proposed repository structure

```text
pilot-01/
  registries/
    tasks/
      humaneval.jsonl
      mbpp.jsonl
      leetcode.jsonl
    models/
      models.json
    evidence/
      training_cutoff.json
      pricing.json
      sources.json
  schemas/
    task.schema.json
    model.schema.json
    training_cutoff.schema.json
    pricing.schema.json
  src/dacdm/
    registries/
      __init__.py
      loader.py
      validator.py
      contamination.py
  tests/
    test_task_registry.py
    test_model_registry.py
    test_evidence_registry.py
    test_contamination.py
    fixtures/
  docs/
    SDD-S1-TASK-EVIDENCE-REGISTRIES.md
```

The exact paths may be reduced if the current S0 package layout makes a smaller implementation cleaner; avoid parallel abstractions.

## 5. Task Registry

Each experimental task MUST have a stable record containing at minimum:

- `task_id`
- `benchmark`
- `benchmark_version`
- `source_ref`
- `source_revision`
- `content_hash`
- `language`
- `split`
- `license_or_terms_ref`
- `eligible`
- `exclusion_reason`

Benchmark-specific metadata may be stored in a small `metadata` object only when required by the frozen Pilot 01 protocol.

Initial benchmark families:

- HumanEval
- MBPP
- LeetCode-derived task set only if its inclusion is permitted by the frozen protocol and source/licensing constraints

S1 MUST NOT silently substitute a different benchmark or task version.

## 6. Model Registry

Each model record MUST include:

- `model_id`
- `provider`
- `provider_model_name`
- `model_version_or_snapshot`
- `access_path`
- `training_cutoff_status`
- `training_cutoff_evidence_ids`
- `pricing_record_id`
- `enabled_for_pilot`

Aliases MUST resolve to one explicit experimental model identity before inference.

## 7. Training-Cutoff Evidence Registry

This registry records evidence, not guesses.

Minimum fields:

- `evidence_id`
- `model_id`
- `claim_type`
- `claimed_cutoff`
- `source_type`
- `source_locator`
- `source_title`
- `retrieved_at`
- `evidence_text_or_summary`
- `confidence`
- `status`

Allowed status values should remain minimal, e.g. `supported`, `conflicting`, `unknown`.

Where a provider does not publish a defensible cutoff, record `unknown`. S1 MUST NOT manufacture a date.

## 8. Pricing Registry

Pricing is frozen as evidence for cost accounting and later reproducibility.

Minimum fields:

- `pricing_record_id`
- `provider`
- `model_id`
- `currency`
- `input_unit_price`
- `output_unit_price`
- `unit_basis`
- `effective_or_observed_at`
- `source_locator`
- `retrieved_at`

Do not mix cached-input, batch, reasoning-token, or other special prices into the base fields unless Pilot 01 actually uses them. Add only fields required by the execution path.

## 9. Deterministic Contamination Engine

Purpose: classify task/model combinations using frozen registry evidence before inference.

The engine MUST:

1. Accept only registry-backed inputs.
2. Produce deterministic output for identical inputs.
3. Record rule/version used.
4. Distinguish `eligible`, `excluded`, and `unknown` rather than forcing a binary answer when evidence is insufficient.
5. Produce machine-readable reason codes.
6. Avoid LLM calls.
7. Avoid network calls.

Initial decision inputs may include benchmark publication/release evidence, task provenance, model training-cutoff evidence, and explicit protocol exclusions. The implementation MUST follow the frozen Pilot 01 protocol rather than inventing probabilistic contamination scores.

Example output shape:

```json
{
  "task_id": "...",
  "model_id": "...",
  "decision": "unknown",
  "reason_codes": ["TRAINING_CUTOFF_UNKNOWN"],
  "rule_version": "s1-v1"
}
```

## 10. Provenance

Every external factual record used for experimental eligibility MUST have a source locator and retrieval timestamp. Where practical, store a content hash or immutable revision identifier.

Do not treat an editable web page as immutable evidence merely because its URL is stable.

## 11. Validation

Add one CLI entry point consistent with the S0 package design, preferably extending the existing `dacdm` CLI rather than creating another command family.

Target command:

```bash
dacdm validate-registries
```

It MUST fail non-zero on schema violations, duplicate primary identifiers, unresolved required references, invalid enum values, or broken internal registry links.

## 12. Tests

Minimum S1 tests:

- valid registry fixture passes
- malformed task fails
- duplicate task ID fails
- duplicate model ID fails
- unresolved evidence reference fails
- unknown training cutoff remains unknown
- deterministic contamination result is stable
- excluded case emits expected reason code
- no-network validation path

## 13. CI

Extend the existing S0 integrity workflow rather than creating an unrelated pipeline.

S1 CI gate MUST run:

```text
install locked dependencies/package
validate-protocol
validate-registries
ruff
mypy
pytest
```

S0 checks remain green.

## 14. Out of Scope

S1 MUST NOT:

- execute paid model inference
- collect Pilot outcome measurements
- tune prompts based on Pilot outcomes
- change H2–H4
- change frozen experimental thresholds
- introduce a database when versioned files suffice
- add a web UI
- use an LLM to decide contamination
- claim empirical validation of DACDM

## 15. S1 Exit Gate

S1 is CLOSED only when all are true:

- [ ] benchmark task sources/versions are explicitly pinned
- [ ] task registry validates
- [ ] model registry validates
- [ ] training-cutoff evidence registry validates
- [ ] pricing registry validates
- [ ] cross-registry references validate
- [ ] contamination engine is deterministic and tested
- [ ] unknown evidence is preserved as unknown
- [ ] no paid inference has occurred
- [ ] S0 protocol integrity still passes
- [ ] ruff passes
- [ ] mypy passes
- [ ] pytest passes
- [ ] GitHub Actions is green on the S1 commit/PR

## 16. Recommended execution order

1. Confirm S0 package/CLI structure.
2. Implement schemas and loader.
3. Add minimal fixtures and validator tests.
4. Pin task sources and generate task registry deterministically.
5. Add model registry.
6. Add evidence/source records.
7. Add pricing records.
8. Implement contamination rules.
9. Extend CLI.
10. Extend CI.
11. Run full S0 + S1 gate.
12. Review evidence manually before closing S1.

## 17. Freeze rule

Once S1 closes, the exact registry snapshots used by Pilot 01 become part of the experimental record. Any later correction that could change task eligibility, model identity, contamination classification, or cost accounting must be explicit and versioned rather than silently rewriting the Pilot input state.
