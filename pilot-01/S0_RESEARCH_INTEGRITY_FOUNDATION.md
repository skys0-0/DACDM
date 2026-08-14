# S0 — Research Integrity Foundation

**Status:** IMPLEMENTED BASELINE  
**Date:** 2026-08-14

## Purpose

S0 makes the frozen Pilot 01 research rules machine-checkable before any paid inference or confirmatory observation is generated.

## Delivered

- Python package skeleton (`src/dacdm`)
- exact dependency lock
- `protocol_frozen_v1.0.yaml`
- strict Pydantic schemas for task/model/pricing/hardware/contamination/execution records
- protocol-integrity validator
- contamination-rule baseline
- observed agent-overhead calculation
- minimum-cost, downward-transition and K4/Kill-Criteria baseline logic
- synthetic observation fixture
- unit/integrity/schema tests
- GitHub Actions CI with no paid API calls

## Frozen evidence identities

The manifest pins the Git blob identities of:

- frozen Pilot Protocol v1.0;
- Implementation Freeze v1.0;
- Pilot 01 SDD v1.0.

Changing any of these files without explicitly updating governance will fail `dacdm validate-protocol`.

## S0 commands

```bash
cd pilot-01
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
dacdm validate-protocol
ruff check src tests
mypy src
pytest
```

## Explicit non-goals

S0 does **not**:

- call OpenAI, Anthropic, Google, OpenRouter, or any other paid model API;
- collect confirmatory observations;
- scrape LeetCode;
- estimate regression coefficients;
- run the 1,000-replication production bootstrap;
- modify registered hypotheses or thresholds.

## Exit gate

S0 exits only when CI passes and the frozen constants/documents cannot drift unnoticed.

The next phase is S1 — Task and Evidence Registries. S1 must build deterministic registries and contamination decisions before S2 performs any live inference.
