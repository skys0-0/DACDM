# DACDM Pilot 01 — Implementation Freeze v1.0

**Status:** FROZEN BEFORE CONFIRMATORY DATA COLLECTION  
**Freeze Date:** 2026-08-14  
**Applies To:** `DACDM_Pilot_01_SDD_v1.0.md`, Section 32  
**Governing Protocol:** `DACDM_Pilot_01_Protocol_v1.0.md`  
**Conceptual Originator:** CHAU HUNG SAN / 辛秋雄

---

## 0. Authority

This document resolves the ten implementation decisions intentionally left open in Section 32 of the Pilot 01 SDD. These choices are frozen before confirmatory results are inspected.

They are implementation rules, not amendments to the registered hypotheses, quality thresholds, H4 minimum effect, CCR definition, K1–K4, or other frozen scientific claims.

If this document conflicts with the frozen Pilot Protocol, the Protocol wins. If it conflicts with a non-frozen implementation convenience, this document wins.

No value below may be changed after confirmatory data collection begins merely because it improves statistical significance, effect size, sample retention, cost, or narrative coherence.

---

# IF-01 — Historical and Current Model Snapshots

## Decision

The confirmatory panel SHALL use **exact, immutable model snapshot identifiers** wherever the provider exposes them.

Provider aliases such as `latest`, rolling aliases, or names that may silently change SHALL NOT be treated as historical model identities.

For every model observation the registry must store:

- provider;
- exact API/model identifier returned by the provider;
- public launch/availability date;
- training cutoff evidence, when available;
- first and last verified availability dates;
- pricing effective date;
- source/evidence URL;
- retrieval timestamp;
- whether the model is `PINNED`, `ROLLING_ALIAS`, `ARCHIVED_EVIDENCE_ONLY`, or `UNVERIFIABLE`.

## Historical rule

Pilot 01 SHALL NOT pretend that running a current endpoint reconstructs a 2024 or 2025 endpoint.

A historical task-model-date observation enters the **confirmatory** panel only if at least one of the following is true:

1. the exact historical snapshot remains callable and its identity can be verified; or
2. a contemporaneous archived observation exists with sufficiently complete provenance to reproduce the registered outcome fields and execution conditions.

Otherwise the observation is `NA / HISTORICAL_SNAPSHOT_UNAVAILABLE`.

No synthetic back-casting, successor-model substitution, or alias substitution is allowed in confirmatory analysis.

## Rationale

This sacrifices sample size to protect temporal validity. Historical model unavailability is a research limitation, not a missing value to be guessed.

---

# IF-02 — LeetCode Weekly Contest Sampling Rule

## Decision

The LeetCode component SHALL use a deterministic, timestamp-based sampling frame.

### Eligible universe

A problem is eligible only when:

1. it originates from a LeetCode **Weekly Contest**;
2. the contest has a verifiable public release date;
3. the problem is publicly labeled **Hard** at registry-freeze time;
4. its release date is after the relevant model training cutoff under the Protocol contamination rule;
5. its release date is on or before the observation date;
6. an executable test oracle can be constructed without changing the substantive problem;
7. use of the task metadata/test representation is legally and technically reproducible.

### Sampling

Use **all eligible Hard problems** in the registered observation window rather than researcher-selected examples.

If resource limits require a smaller set, apply deterministic hash sampling:

```text
score = SHA256(canonical_task_id)
```

Sort ascending by `score` and take the first `N` tasks, where `N` must be fixed in the execution manifest **before inference begins**.

No selection by observed model performance is allowed.

### Canonical ID

```text
leetcode:weekly:<contest_number>:<problem_slug>
```

## Rationale

“All eligible” minimizes researcher discretion. Hash sampling provides a reproducible fallback if inference cost makes full coverage infeasible.

---

# IF-03 — Inference Sampling Parameters

## Decision

The confirmatory estimand is a **single first response under the lowest-randomness provider-supported configuration**.

### Standard configuration

Where supported:

```yaml
n: 1
temperature: 0
top_p: 1
seed: null
stop: provider_default_unless_required_by_harness
```

No self-consistency sampling, majority voting, best-of-N, hidden regeneration, or answer-selection model is permitted in the direct-model confirmatory pathway.

### Unsupported parameters

If a model/API does not support `temperature=0`, the runner SHALL:

1. use the provider-documented deterministic/lowest-randomness setting if one exists;
2. otherwise use the provider default;
3. record the exact effective parameters and `SAMPLING_CONTROL_LIMITED=true`.

The model is not silently excluded merely because its API exposes fewer controls.

### Reasoning effort

Where a provider exposes a reasoning-effort control, the confirmatory default is the provider's documented **standard/default** reasoning setting, not maximum reasoning. The exact value must be stored.

Alternative reasoning levels are exploratory unless separately pre-specified before data collection.

## Rationale

The design measures the minimum-cost ordinary execution path rather than best-of-N performance. Provider capability differences are recorded rather than hidden.

---

# IF-04 — Canonical Prompt Wrapper

## Decision

Direct code-generation observations SHALL use one minimal provider-neutral semantic prompt.

### System instruction

```text
You are solving a programming benchmark task. Return only the final code solution required by the task. Do not include Markdown fences, explanations, commentary, or test output. Do not use network access or external services.
```

### User instruction

```text
Solve the following programming task.

<BEGIN_TASK>
{canonical_problem_statement}
<END_TASK>

Return only the final code solution.
```

### Rules

- The canonical task statement is inserted without model-specific hints.
- No provider receives extra reasoning guidance unavailable to another provider.
- Required benchmark function signatures/import constraints may be appended only when they are part of the canonical benchmark contract.
- Prompt bytes after normalization are hashed and stored.
- Prompt template version: `coding-direct-v1.0`.
- Any provider-specific syntactic adaptation required by an API must preserve semantic content and be recorded.

## Rationale

A short neutral wrapper reduces prompt-engineering degrees of freedom and keeps the comparison focused on model capability/cost.

---

# IF-05 — Transport Failures vs Scientific Retries

## Decision

Infrastructure retry and scientific retry are different event types.

### Retriable infrastructure failures

Only failures that occur **before a scientifically usable model completion is obtained** may be retried automatically, including:

- HTTP 408;
- HTTP 429;
- HTTP 500/502/503/504;
- connection reset;
- provider timeout with no usable completion;
- transient SDK/network error.

### Retry limit

```yaml
max_infrastructure_retries: 2
backoff_seconds: [2, 8]
jitter: deterministic_from_attempt_id
```

This means at most **3 transport attempts total** for one scientific observation.

### Non-retriable scientific outcomes

The following SHALL NOT trigger a replacement generation within the same Pass@1 observation:

- code fails tests;
- syntax error in returned code;
- wrong answer;
- incomplete but usable completion;
- model refusal;
- valid completion that violates requested output format but can still be evaluated deterministically.

These remain the first scientific outcome.

### Ambiguous partial responses

If provider metadata indicates a completion was generated but transmission was interrupted, store it as `PARTIAL_PROVIDER_FAILURE`; do not automatically treat a later completion as the same Pass@1 sample. Confirmatory inclusion follows a deterministic rule fixed in code before production execution.

## Rationale

This prevents network reliability from becoming model-quality noise while preventing hidden regeneration from inflating Pass@1.

---

# IF-06 — Bootstrap Unit and Confidence Interval

## Decision

Confirmatory uncertainty SHALL use a **task-cluster non-parametric bootstrap**.

### Resampling unit

Resample unique `task_id` values with replacement.

For each selected task, include **all of that task's eligible dates/model observations** in the replicate.

This preserves within-task longitudinal dependence and matches the task fixed-effect design.

### Frozen settings

```yaml
replications: 1000
seed: 20260814
ci_method: percentile
confidence_level: 0.95
p_values: two_sided
```

The same bootstrap draw IDs SHALL be used where feasible across related registered statistics to improve traceability.

Failed replicates are logged. The report states both requested and successful replicate counts. If fewer than 950 of 1,000 replicates are estimable for a statistic, that bootstrap result is flagged `UNSTABLE_BOOTSTRAP` and not presented as a normal confirmatory CI without explicit disclosure.

## Rationale

Observation-level resampling would break the repeated-measures structure. Task-cluster resampling is the simplest design consistent with the panel.

---

# IF-07 — Hardware Index Interpolation

## Decision

The primary hardware counterfactual SHALL use an externally sourced AI-chip performance-per-dollar series, with Epoch AI as the preferred public source when the required data are available.

Epoch AI reports rapid long-run improvement in AI-chip FLOP/s per dollar and publishes downloadable hardware data. The project SHALL retain the exact source snapshot used rather than relying on a live webpage at reproduction time.

### Monthly construction

1. Convert source observations to a common real-price performance-per-dollar measure where the source methodology permits.
2. Normalize the index so that **2024-01 = 1.000000**.
3. Between two valid dated index anchors, interpolate **linearly in log(index)** over calendar time.
4. Do not use ordinary linear interpolation on the level.
5. Do not extrapolate beyond the first or last supported source anchor in the primary confirmatory series.
6. Months outside supported anchors are `NA / HARDWARE_INDEX_OUT_OF_RANGE`.

### Formula

For anchors `(t0, H0)` and `(t1, H1)`:

```text
ln(H_t) = ln(H0) + ((t - t0)/(t1 - t0)) * [ln(H1) - ln(H0)]
H_t = exp(ln(H_t))
```

### Sensitivity

Alternative hardware series or interpolation rules are exploratory/sensitivity analyses and cannot replace the primary result after outcomes are known.

## Rationale

Performance-per-dollar improvements are approximately multiplicative over time, so log interpolation is more defensible than level interpolation. Epoch AI's current public trend work reports AI-chip performance per dollar improving on the order of roughly one-third per year, but Pilot 01 will use the archived source data rather than hard-code that growth rate.

---

# IF-08 — Operational Definition of Agent Overhead α

## Decision

The earlier symbolic expression is operationalized so that `α` is observable and non-circular.

For one user objective `U`:

```text
C_base  = metered cost of the direct final-answer generation component
C_sub   = sum of metered model/API costs for planning, reflection, retrieval-generation,
          retries that are part of the agent workflow, and other model subtasks
C_tool  = separately metered external tool/API costs attributable to U
C_total = C_base + C_sub + C_tool
```

Define:

```text
agent_overhead_alpha = (C_total - C_base) / C_base
```

when `C_base > 0`.

Therefore:

```text
C_total = C_base * (1 + agent_overhead_alpha)
```

For a non-agent direct pathway:

```text
agent_overhead_alpha = 0
C_total = C_base
```

If `C_base = 0`, alpha is `NA` and total cost remains directly observed.

### Important boundary

Token/tool subtasks are **not** separate task observations. They remain costs of user objective `U`.

Local test execution with no separately metered marginal charge is recorded as a tool event but contributes USD 0 to `C_tool`; compute/time telemetry may be retained separately.

## Rationale

This definition makes alpha a true observed overhead ratio and avoids defining an unknown multiplier by an equation that already requires the multiplier.

---

# IF-09 — LeetCode Test-Case Coverage Rule

## Decision

Pass@1 remains the primary registered quality outcome. Test-case coverage is an audit/secondary quality field for the LeetCode Hard subset.

For each task:

```text
coverage = passed_hidden_or_registered_test_cases / total_executed_test_cases
```

### Minimum oracle requirements

A LeetCode task may enter confirmatory analysis only if the project has a deterministic executable oracle with:

- at least **20 distinct test cases**, OR
- the complete authoritative test set where legitimately accessible and reproducible;
- at least one ordinary case;
- at least one boundary/edge case where applicable;
- deterministic expected outputs.

If fewer than 20 reproducible cases are available and no complete authoritative oracle is available, mark:

`TEST_ORACLE_INSUFFICIENT`

and exclude the task from the confirmatory LeetCode subset before model results are inspected.

### Pass rule

A generated solution passes the task only if **100% of the registered executable test cases pass** within sandbox limits.

The Protocol's aggregate LeetCode-hard fixed quality threshold remains **60% Pass@1 across tasks**. The 100% rule applies to whether an individual task solution is counted as passed; it does not replace the 60% aggregate threshold.

## Rationale

A partial unit-test pass is not a solved programming problem. Requiring a minimally substantial deterministic oracle reduces false passes while preserving the registered aggregate threshold.

---

# IF-10 — Fixed-Effects Estimator and Standard Errors

## Decision

Primary confirmatory panel estimation SHALL use:

- Python;
- `linearmodels` pinned in the environment lock;
- `PanelOLS`;
- task (`task_id`) entity fixed effects;
- the registered time specification;
- covariance clustered by task/entity;
- two-sided inference;
- rank checking enabled;
- no observation weights unless the Protocol explicitly requires them.

### Primary specification

```text
Dependent variable: ln(cost_it)
Entity: task_id
Entity effects: True
Time regressor: registered linear month index
Covariance: clustered by entity/task
```

### Monthly-dummy alternative

If the Protocol's monthly-dummy alternative is reported, it is a registered secondary specification and must not replace the primary linear-time result solely because its result is more favorable.

### Standard-error treatment

Use task-clustered covariance for the regression table because repeated observations for the same task are not independent.

Bootstrap CIs remain the registered uncertainty analysis described in IF-06 and are reported alongside model-based clustered standard errors rather than silently replacing them.

### Software reproducibility

The exact `linearmodels`, NumPy, pandas, SciPy, and Python versions SHALL be locked. The analysis manifest stores the formula, estimator arguments, covariance options, sample filters, and package versions.

## Rationale

`PanelOLS` directly supports entity fixed effects and clustered covariance. Clustering by task is aligned with the repeated-measures panel and the task-level bootstrap.

---

# 11. Frozen Decision Matrix

| ID | Decision | Frozen Value |
|---|---|---|
| IF-01 | Historical model identity | Exact pinned snapshot or qualified contemporaneous archive only; otherwise NA |
| IF-02 | LeetCode sampling | All eligible Weekly Contest Hard tasks; deterministic SHA256 sampling only if resource cap fixed pre-inference |
| IF-03 | Sampling | n=1; temperature=0 where supported; lowest-randomness/provider default otherwise, fully logged |
| IF-04 | Prompt | `coding-direct-v1.0`, minimal provider-neutral code-only wrapper |
| IF-05 | Transport retries | 2 retries; 2s/8s backoff; no scientific regeneration |
| IF-06 | Bootstrap | Task-cluster; 1,000 reps; seed 20260814; percentile 95% CI |
| IF-07 | Hardware interpolation | 2024-01=1; log-linear interpolation; no primary extrapolation |
| IF-08 | Agent α | `(C_total - C_base) / C_base`; 0 for non-agent; NA if base cost=0 |
| IF-09 | LeetCode oracle | ≥20 tests or complete authoritative oracle; task pass requires 100% tests |
| IF-10 | FE estimator | `linearmodels.PanelOLS`; task FE; task-clustered covariance; two-sided |

---

# 12. Change Control

After confirmatory data collection begins, any required correction to these rules must be handled as follows:

1. preserve this file unchanged;
2. create a new versioned amendment document;
3. identify the objective error requiring correction;
4. state whether any confirmatory data had already been inspected;
5. run the original specification where technically possible;
6. label amended results separately;
7. never rewrite the historical Git record to hide the change.

Changes made because a result is weak, null, inconvenient, expensive, or statistically insignificant are prohibited.

---

# 13. Implementation Gate

**Section 32 status after this document: RESOLVED / FROZEN.**

S0 development may proceed.

Full confirmatory data collection may begin only after automated tests verify that the code implements IF-01 through IF-10 and the execution manifest records their version/hash.
