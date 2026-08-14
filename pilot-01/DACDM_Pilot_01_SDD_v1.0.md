# DACDM Pilot 01 — Software Design Document (SDD)

**Document:** `DACDM_Pilot_01_SDD_v1.0`  
**SDD Version:** 1.0  
**Prepared:** 2026-08-14  
**Status:** Implementation specification — may evolve only where it does not alter the frozen empirical protocol  
**Governing Protocol:** `DACDM_Pilot_01_Protocol_v1.0.md` — **Frozen / Pre-registered**  
**Associated Framework:** `DACDM_Conceptual_Framework_v1.0.md`  
**DOI:** 10.5281/zenodo.21930795  
**Conceptual Originator:** CHAU HUNG SAN / 辛秋雄

---

## 0. Document Authority and Boundary

This SDD defines the software, data, execution, validation, and analysis architecture required to implement **DACDM Pilot 01 — Code Generation Complexity Compression**.

The SDD is subordinate to the frozen Pilot 01 protocol. It may specify implementation details that the protocol leaves open, but it **must not change**:

- H2, H3, or H4;
- the fixed quality thresholds;
- contamination rules;
- model-tier logic;
- the unit of analysis;
- the treatment of agent overhead;
- the registered dependent variables;
- the fixed-effects analysis;
- CCR definitions;
- the 15% annual minimum effect threshold for H4;
- K1–K4;
- bootstrap replication count;
- or the amendment policy.

If an implementation choice conflicts with the frozen protocol, **the protocol wins**. The conflict must be logged rather than silently resolved.

This document does **not** claim that Pilot 01 has been executed or that DACDM has empirical support.

---

# 1. System Objective

Build a reproducible empirical research pipeline that can:

1. construct a timestamped coding-task panel;
2. determine contamination eligibility;
3. execute eligible tasks against selected AI models;
4. capture quality, token, latency, tool, retry, and cost telemetry;
5. classify observations into frozen model tiers;
6. determine the minimum-cost and minimum-tier pathway clearing the fixed quality anchor;
7. construct hardware-deflated cost measures;
8. estimate complexity migration and CCR;
9. run the pre-registered fixed-effects and bootstrap analyses;
10. evaluate K1–K4 without discretionary reinterpretation;
11. preserve raw evidence and a complete audit trail;
12. reproduce final tables, figures, and machine-readable results from immutable inputs.

The system is a **research pipeline**, not a production SaaS platform.

---

# 2. Design Principles

## 2.1 Protocol first

Scientific constraints are configuration that is versioned but not casually editable. Frozen values are loaded from a machine-readable protocol manifest and verified before every confirmatory run.

## 2.2 Simplest implementation

Prefer a local/CI-capable Python pipeline, relational/columnar files, deterministic CLI commands, and established statistical libraries. Do not introduce microservices, distributed queues, Kubernetes, or agent frameworks unless later scale measurements prove they are necessary.

## 2.3 Layered growth

Implementation proceeds end-to-end in small layers:

**task registry → eligibility → single-model inference → evaluator → telemetry/cost → panel → analysis → bootstrap → report**

Every layer must work before adding the next.

## 2.4 Immutable raw evidence

Raw prompts, responses, test outputs, provider metadata, and execution manifests are append-only. Corrections create new derived records; they do not rewrite raw evidence.

## 2.5 Separation of concerns

Task ingestion, contamination screening, inference, evaluation, pricing, tier classification, aggregation, statistics, and reporting are separate modules.

## 2.6 Reproducibility over convenience

Every analytical output must be traceable to:

- source task;
- model identifier;
- execution configuration;
- raw response;
- evaluator version;
- pricing record;
- hardware index record;
- code commit;
- protocol manifest;
- and analysis run ID.

---

# 3. Scope

## 3.1 In scope

- HumanEval task metadata and execution
- MBPP task metadata and execution
- selected timestamped LeetCode Weekly Contest tasks where legally/reproducibly usable
- task release-date registry
- model launch/training-cutoff evidence registry
- contamination filtering
- model registry and T1/T2/T3 assignment
- provider adapters
- direct non-agent inference
- optional agent execution measurement
- sandboxed Python code evaluation
- Pass@1 calculation
- test coverage metadata for the registered LeetCode subset
- token/latency/cost logging
- historical/current pricing registry
- hardware performance-per-dollar index ingestion
- panel construction
- minimum-cost/minimum-tier calculation
- CCR_task and CCR_compute
- fixed-effects regression
- 1,000-replication non-parametric bootstrap
- sensitivity analyses explicitly marked as such
- kill-criteria evaluation
- reproducible result export

## 3.2 Out of scope for v1.0 implementation

- general-purpose benchmarking platform
- web dashboard
- public multi-user service
- automated publication submission
- autonomous changes to the protocol
- automatic re-tiering based on undocumented model judgment
- training/fine-tuning models
- GPU hardware benchmarking conducted by this repository
- retroactive reconstruction of unavailable proprietary telemetry as if observed
- treating agent subtasks as independent observations

---

# 4. Frozen Scientific Contract

A machine-readable file SHALL mirror the frozen protocol:

`pilot-01/config/protocol_frozen_v1.0.yaml`

Minimum fields:

```yaml
protocol:
  name: DACDM Pilot 01
  version: "1.0"
  frozen_date: "2026-08-14"
  status: frozen

quality_thresholds:
  humaneval: 0.80
  mbpp: 0.75
  leetcode_hard: 0.60

bootstrap:
  replications: 1000
  confidence_level: 0.95
  p_values: two_sided

h4:
  minimum_deflated_cost_decline_per_year: 0.15

ccr:
  rolling_window_months: 6

kill_criteria:
  K1: registered
  K2: registered
  K3: registered
  K4_contamination_exclusion_share: 0.30
```

The manifest is an implementation mirror, **not a new source of scientific authority**. A test must compare its values against a checked-in frozen reference. Confirmatory execution must fail if registered values are missing or altered.

---

# 5. Proposed Repository Structure

```text
DACDM/
├── README.md
├── LICENSE
├── CITATION.cff
├── REFERENCES.bib
├── framework/
├── protocols/
│   └── DACDM_Pilot_01_Protocol_v1.0.md
└── pilot-01/
    ├── README.md
    ├── pyproject.toml
    ├── uv.lock                         # if uv is adopted
    ├── .env.example
    ├── config/
    │   ├── protocol_frozen_v1.0.yaml
    │   ├── providers.example.yaml
    │   └── execution.yaml
    ├── data/
    │   ├── README.md
    │   ├── raw/                        # normally gitignored
    │   ├── processed/
    │   ├── derived/
    │   └── registries/
    │       ├── models.csv
    │       ├── model_cutoffs.csv
    │       ├── pricing.csv
    │       ├── hardware_index.csv
    │       └── task_sources.csv
    ├── src/dacdm_pilot/
    │   ├── __init__.py
    │   ├── cli.py
    │   ├── config.py
    │   ├── schemas.py
    │   ├── tasks/
    │   │   ├── humaneval.py
    │   │   ├── mbpp.py
    │   │   ├── leetcode.py
    │   │   └── registry.py
    │   ├── contamination/
    │   │   ├── rules.py
    │   │   └── evidence.py
    │   ├── models/
    │   │   ├── registry.py
    │   │   └── tiers.py
    │   ├── providers/
    │   │   ├── base.py
    │   │   ├── openai_adapter.py
    │   │   ├── anthropic_adapter.py
    │   │   └── google_adapter.py
    │   ├── execution/
    │   │   ├── runner.py
    │   │   ├── manifest.py
    │   │   ├── telemetry.py
    │   │   └── agent_accounting.py
    │   ├── evaluation/
    │   │   ├── sandbox.py
    │   │   ├── pass1.py
    │   │   └── coverage.py
    │   ├── economics/
    │   │   ├── pricing.py
    │   │   ├── cost.py
    │   │   └── hardware.py
    │   ├── panel/
    │   │   ├── build.py
    │   │   └── transitions.py
    │   ├── analysis/
    │   │   ├── fixed_effects.py
    │   │   ├── ccr.py
    │   │   ├── bootstrap.py
    │   │   ├── sensitivity.py
    │   │   └── kill_criteria.py
    │   └── reporting/
    │       ├── tables.py
    │       ├── figures.py
    │       └── report.py
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   ├── fixtures/
    │   └── protocol/
    ├── analysis/
    │   ├── README.md
    │   └── notebooks/                  # exploratory only
    ├── results/
    │   ├── README.md
    │   ├── confirmatory/
    │   ├── exploratory/
    │   └── manifests/
    └── scripts/
        ├── bootstrap_environment.sh
        └── reproduce.sh
```

---

# 6. Technology Baseline

Recommended minimal stack:

| Concern | Choice |
|---|---|
| Language | Python 3.12+ |
| Environment | `uv` or standard `venv` + locked dependencies |
| Dataframes | pandas |
| Columnar data | Parquet via PyArrow |
| Validation | Pydantic |
| Statistical models | statsmodels and/or linearmodels |
| Bootstrap | NumPy/SciPy + project implementation |
| HTTP | official provider SDKs where available |
| CLI | Typer |
| Config | YAML + Pydantic validation |
| Tests | pytest |
| Formatting/lint | Ruff |
| Type checking | mypy or pyright |
| Charts | matplotlib |
| Secrets | environment variables only |
| CI | GitHub Actions |

SQLite may be used for execution bookkeeping, but Parquet/CSV should remain the portable analytical interchange format.

---

# 7. Core Data Model

The protocol data dictionary remains authoritative. Implementation extends it with provenance fields without redefining registered variables.

## 7.1 `TaskRecord`

```text
task_id
benchmark
task_tier
release_date
source_url
prompt_hash
test_hash
license_or_access_note
ingestion_version
```

## 7.2 `ModelRecord`

```text
model_id
provider
public_model_name
model_version
launch_date
training_cutoff
cutoff_evidence_url
model_tier
tier_evidence
pricing_key
active_from
active_to
```

## 7.3 `ExecutionRecord`

Contains the protocol fields:

```text
task_id
date
model
model_tier
pass_1
input_tokens
output_tokens
reasoning_tokens
tool_calls
retries
latency_sec
api_cost_usd
agent_overhead_alpha
meets_threshold
hardware_perf_index
exclude_contamination
source_url
notes
```

plus implementation provenance:

```text
run_id
attempt_id
provider_request_id
prompt_template_version
execution_mode
raw_response_path
test_result_path
pricing_version
evaluator_version
git_commit
created_at_utc
```

## 7.4 `TaskDateSummary`

```text
task_id
date
threshold
eligible_model_count
min_cost
min_tier
winning_model
hardware_perf_index
cost_deflated
```

## 7.5 Missing data

Unknown reasoning-token counts are stored as `NA`, never `0`.

Unavailable observations must carry an explicit reason code, for example:

- `MODEL_UNAVAILABLE`
- `API_ERROR`
- `RATE_LIMIT`
- `CUTOFF_UNKNOWN`
- `CONTAMINATION_EXCLUDED`
- `PRICE_UNAVAILABLE`
- `TEST_ENVIRONMENT_FAILURE`

---

# 8. Task Ingestion

## 8.1 HumanEval

Ingest canonical task IDs, prompts/tests as permitted, source metadata, and provenance.

## 8.2 MBPP

Same principle. Dataset versions must be pinned.

## 8.3 LeetCode

Because the protocol requires timestamp filtering, every selected task requires an independently auditable contest date.

The implementation must avoid committing restricted problem content where redistribution is not allowed. Store task identifiers, dates, hashes, and retrieval provenance when necessary.

## 8.4 Task immutability

Once a task is included in a registered execution batch:

- its canonical identifier is immutable;
- prompt/test corrections produce a new task revision;
- old observations remain associated with the original revision.

---

# 9. Contamination Engine

The contamination engine executes **before inference inclusion**.

## 9.1 Registered rule

A task is excluded if its public release date precedes the training cutoff date of any model used in the relevant test window.

For models with unknown training cutoff, apply the protocol's conservative rule concerning the six-month period relative to public launch.

## 9.2 Evidence requirement

Every cutoff decision must store:

```text
model_id
cutoff_status
cutoff_date
evidence_source
evidence_type
retrieved_at
review_status
```

No LLM-generated guess may be used as cutoff evidence.

## 9.3 Deterministic output

`contamination_check(task, model)` returns:

```text
ELIGIBLE
EXCLUDED
REVIEW_REQUIRED
```

`REVIEW_REQUIRED` observations cannot enter confirmatory analysis until resolved under a documented rule consistent with the protocol.

## 9.4 K4

The pipeline automatically computes the contamination-exclusion share and exposes the value to the kill-criteria module.

---

# 10. Model Registry and Tiering

T1/T2/T3 classification is frozen in concept but requires operational evidence.

Every model entry stores:

- exact API identifier;
- provider;
- release/availability dates;
- public capability evidence;
- price evidence;
- tier;
- date assigned;
- rationale;
- reviewer;
- source links.

Tier assignment must happen **before** confirmatory results for that model are inspected.

A new model may be added under the protocol's existing criteria, but the addition must be versioned in the registry.

---

# 11. Provider Adapter Interface

All providers implement a common interface conceptually equivalent to:

```python
generate(request) -> ModelResponse
```

`ModelResponse` normalizes:

```text
provider
model
response_text
input_tokens
output_tokens
reasoning_tokens
latency_sec
provider_request_id
finish_reason
raw_metadata
```

Provider-specific raw payloads are preserved separately.

The adapter must not silently retry. Retries are controlled by the execution runner so that `retries` remains observable.

---

# 12. Execution Runner

## 12.1 Execution manifest

Before a batch begins, generate an immutable manifest containing:

- run ID;
- UTC timestamp;
- Git commit;
- protocol version/hash;
- task-set hash;
- model-registry hash;
- pricing-registry hash;
- hardware-index version;
- evaluator version;
- provider/model list;
- execution mode;
- random seed where applicable.

## 12.2 Pass@1 discipline

The primary observation must preserve Pass@1 semantics. Retry behavior used for infrastructure failures must be distinguished from attempts that would change the scientific meaning of Pass@1.

A provider transport failure may be reissued and logged as infrastructure retry. A failed generated solution must not be silently replaced by another sample and still called the same Pass@1 observation.

## 12.3 Resume behavior

Runs may resume after interruption using immutable attempt IDs. Completed observations are not rerun unless a new run ID is created.

---

# 13. Code Execution Sandbox

Generated code is untrusted.

Required controls:

- isolated subprocess/container;
- no network access during test execution unless explicitly required and documented;
- CPU time limit;
- wall-clock timeout;
- memory limit;
- temporary filesystem;
- restricted environment variables;
- no access to provider secrets;
- captured stdout/stderr;
- deterministic test harness where possible.

A sandbox failure is not automatically a model failure. Environment failures receive a separate status.

---

# 14. Quality Evaluation

## 14.1 Primary metric

Pass@1.

Registered aggregate thresholds:

- HumanEval: **80%**
- MBPP: **75%**
- LeetCode-hard subset: **60%**

## 14.2 LeetCode hard subset

The implementation records test-case coverage in addition to Pass@1 as required by the protocol.

## 14.3 Evaluator versioning

Every result stores the evaluator/test-suite hash. Changing a test harness creates a new evaluator version and requires explicit comparability review.

---

# 15. Cost Accounting

## 15.1 Direct API cost

For each execution:

```text
input_cost
output_cost
reasoning_cost_if_separately_priced
other_provider_metered_cost
total_api_cost
```

Historical pricing must be effective-dated.

Never calculate a 2024 observation using a 2026 price unless the analysis explicitly requires such a counterfactual and labels it accordingly.

## 15.2 Agent pathway

For agent execution, preserve the user-level objective as the unit of analysis.

Record:

- final answer call;
- all subtasks;
- tool calls;
- retrieval;
- tests;
- reflection/retries;
- total cost.

The implementation reports the protocol's `agent_overhead_α` as an observed quantity. It must not invent a constant alpha.

## 15.3 Minimum cost

For each eligible task-date, calculate the minimum observed cost among pathways meeting the fixed quality anchor, subject to the protocol's aggregation definition.

---

# 16. Hardware Deflation

Hardware performance-per-dollar is an external counterfactual input.

Registry fields:

```text
period
index_value
base_period
source
retrieved_at
method_note
```

Base normalization: 2024 = 1, consistent with the protocol data dictionary.

`cost_deflated` must be computed by a single tested function. The exact transformation used in analysis must be stated in the generated methods output.

No interpolation method should be hidden. If interpolation is required, its rule is versioned and reported.

---

# 17. Panel Construction

The panel builder joins:

```text
Task
× eligible execution date
× model/pathway
× quality
× price
× hardware index
× contamination status
```

Derived task-date records identify:

- models clearing threshold;
- minimum observed cost;
- lowest tier clearing threshold;
- frontier share;
- transition state.

Panel construction must be reproducible from raw/processed inputs.

---

# 18. CCR Engine

For six-month rolling windows:

\[
CCR_t = \sum_{i>j} w_i P_{i\rightarrow j,t}
\]

Produce:

1. `CCR_task` — task-count weighted;
2. `CCR_compute` — weighted by original high-tier compute cost.

The engine stores the transition matrix behind every reported CCR value.

No upward or same-tier transition is silently counted as downward compression.

---

# 19. Confirmatory Statistical Analysis

## 19.1 Registered model

\[
\ln(cost_{i,t}) =
\beta_1 Tier_{i,t}
+ \beta_2 Time_t
+ \gamma_i
+ \epsilon_{i,t}
\]

where task fixed effects absorb stable task-level difficulty.

The implementation should support:

- registered linear time trend;
- registered monthly-dummy alternative where specified by the protocol;
- task fixed effects;
- two-sided inference.

## 19.2 Important implementation safeguard

The analysis code must generate a model specification manifest showing the exact formula, sample filters, missing-data exclusions, and estimator options before producing the final coefficient table.

This prevents accidental specification drift.

## 19.3 H4

Observed deflated cost decline is compared against the hardware-only counterfactual in which complexity migration is absent.

The registered minimum support threshold remains **15% per year** average deflated decline over 2024–2026.

---

# 20. Bootstrap

Use non-parametric bootstrap with exactly **1,000 replications** for registered confidence intervals.

Outputs:

- beta coefficients;
- CCR by rolling window;
- CACP if computed.

Requirements:

- fixed stored seed for reproducibility;
- bootstrap unit explicitly recorded;
- failed replications logged;
- effective replication count reported;
- percentile/other CI construction method stated in output metadata.

The protocol does not fully specify every bootstrap implementation detail; therefore these details must be frozen in the analysis manifest **before inspecting confirmatory results**.

---

# 21. Kill-Criteria Engine

The final confirmatory pipeline evaluates K1–K4 mechanically.

Output example:

```json
{
  "K1": {"triggered": false, "evidence": "..."},
  "K2": {"triggered": false, "evidence": "..."},
  "K3": {"triggered": false, "evidence": "..."},
  "K4": {"triggered": false, "evidence": "..."}
}
```

The system must not replace the protocol wording with a more favorable interpretation after results are known.

Because the supplied protocol contains wording around K1–K3 that may require careful logical reporting, the software should report **each criterion independently**, alongside raw statistics, rather than hiding them behind one opaque “validated/falsified” boolean.

---

# 22. Confirmatory vs Exploratory Boundary

## Confirmatory

Only analyses directly specified by the frozen protocol.

Stored under:

`results/confirmatory/`

## Exploratory

Examples:

- alternative tier mappings;
- alternative quality thresholds;
- alternate contamination assumptions;
- provider-specific subgroup analysis;
- different time windows;
- alternative cost normalizations.

Stored under:

`results/exploratory/`

Every exploratory output must carry:

`PRE-REGISTRATION STATUS: EXPLORATORY / POST-HOC`

Exploratory findings cannot be substituted for failed confirmatory results.

---

# 23. Audit Trail

Every material action creates an append-only event:

```text
event_id
timestamp_utc
actor
action
entity_type
entity_id
old_hash
new_hash
reason
git_commit
```

At minimum audit:

- task inclusion/exclusion;
- cutoff evidence change;
- tier assignment/change;
- pricing update;
- evaluator change;
- manual data correction;
- run start/stop;
- analysis freeze;
- report generation.

---

# 24. Validation and Test Strategy

## 24.1 Unit tests

Required for:

- contamination date logic;
- tier validation;
- threshold comparison;
- price lookup by effective date;
- API cost arithmetic;
- agent aggregation;
- hardware deflation;
- minimum-cost selection;
- minimum-tier selection;
- transition calculation;
- CCR weighting;
- K1–K4 evaluation.

## 24.2 Integration tests

Use small fixtures:

- 3 tasks;
- 3 model tiers;
- 2 dates six months apart;
- known threshold outcomes;
- known costs.

Expected CCR and kill-criteria outputs are calculated manually and asserted.

## 24.3 Protocol integrity tests

CI fails if:

- frozen threshold changes;
- bootstrap count differs from 1,000;
- rolling window differs from six months;
- H4 minimum effect differs from 15%;
- K4 contamination threshold differs from 30%;
- protocol manifest hash changes without an explicit documented amendment.

---

# 25. Security and Secrets

Provider keys:

- never committed;
- loaded from environment variables;
- redacted from logs;
- unavailable inside generated-code sandboxes.

Raw model outputs are treated as untrusted data.

No generated code receives repository write access by default.

---

# 26. Reproducibility Commands

Target CLI:

```bash
dacdm validate-protocol
dacdm ingest-tasks
dacdm validate-contamination
dacdm validate-model-registry
dacdm run --manifest <manifest>
dacdm evaluate --run-id <id>
dacdm build-panel
dacdm analyze-confirmatory
dacdm analyze-exploratory
dacdm bootstrap
dacdm evaluate-kill-criteria
dacdm build-report
```

One-command reproduction after prerequisites:

```bash
./scripts/reproduce.sh
```

This should rebuild processed data and analytical outputs without modifying raw evidence.

---

# 27. CI/CD

GitHub Actions should initially perform only:

1. dependency installation;
2. lint;
3. type checks;
4. unit tests;
5. protocol-integrity tests;
6. fixture integration tests.

CI must **not** call paid model APIs by default.

Live inference requires an explicit manual workflow or local execution with secrets and a declared run manifest.

---

# 28. Result Artifacts

A completed confirmatory run should generate:

```text
results/confirmatory/
├── analysis_manifest.json
├── sample_flow.csv
├── regression_main.csv
├── regression_main.md
├── ccr_task.csv
├── ccr_compute.csv
├── bootstrap_summary.csv
├── kill_criteria.json
├── contamination_summary.csv
├── model_tier_summary.csv
├── cost_decline_summary.csv
├── figures/
└── report.md
```

`sample_flow.csv` should make exclusions auditable from source population to final analytical sample.

---

# 29. Development Phases

## Phase S0 — Research integrity foundation

Deliver:

- package skeleton;
- environment lock;
- frozen protocol manifest;
- schemas;
- test framework;
- protocol-integrity tests;
- CI.

**Exit:** CI proves registered constants cannot drift unnoticed.

## Phase S1 — Task and evidence registries

Deliver:

- HumanEval ingestion;
- MBPP ingestion;
- LeetCode metadata adapter;
- task registry;
- model registry;
- cutoff evidence registry;
- contamination engine.

**Exit:** deterministic eligible/excluded/review-required table.

## Phase S2 — Single-provider vertical slice

Deliver:

- one provider adapter;
- direct inference runner;
- execution manifest;
- telemetry;
- sandbox;
- Pass@1 evaluator;
- cost calculator.

**Exit:** one small legal fixture/task batch runs end-to-end.

## Phase S3 — Multi-model/multi-provider execution

Deliver:

- remaining required provider adapters;
- tier registry enforcement;
- pricing history;
- robust run/resume behavior.

**Exit:** normalized cross-provider observation table.

## Phase S4 — Economics and panel

Deliver:

- hardware index ingestion;
- cost deflation;
- task-date summary;
- min-cost/min-tier logic;
- transition matrices.

**Exit:** analysis-ready panel.

## Phase S5 — Confirmatory statistics

Deliver:

- FE regression;
- CCR_task;
- CCR_compute;
- bootstrap;
- K1–K4 engine;
- analysis manifest.

**Exit:** fixture-based statistical pipeline independently testable.

## Phase S6 — Pilot execution

Deliver:

- frozen execution manifests;
- production inference runs;
- cleaned panel;
- exclusion report.

**Exit:** dataset frozen for confirmatory analysis.

## Phase S7 — Results and reproducibility

Deliver:

- confirmatory outputs;
- exploratory outputs separated;
- final report;
- reproduction script;
- checksums.

**Exit:** independent reviewer can trace every headline result to underlying observations.

---

# 30. Acceptance Criteria

Pilot 01 software is implementation-ready when:

- [ ] frozen protocol values are machine-validated;
- [ ] task IDs and source dates are reproducible;
- [ ] contamination decisions retain evidence;
- [ ] model tier assignments are versioned and pre-result;
- [ ] raw API responses are preserved;
- [ ] Pass@1 cannot be inflated by hidden retries;
- [ ] code execution is isolated;
- [ ] cost uses effective-dated pricing;
- [ ] unknown reasoning tokens remain NA;
- [ ] agent costs aggregate at user-objective level;
- [ ] hardware deflation is deterministic;
- [ ] min-cost/min-tier logic is tested;
- [ ] CCR transition matrices are retained;
- [ ] FE specification is emitted before results;
- [ ] bootstrap runs exactly 1,000 registered replications;
- [ ] K1–K4 are independently and mechanically reported;
- [ ] confirmatory and exploratory outputs are physically separated;
- [ ] CI blocks protocol drift;
- [ ] `reproduce.sh` rebuilds analytical outputs from preserved inputs.

---

# 31. Known Methodological Implementation Risks

### R1 — Historical 2024–2026 inference is not equivalent to contemporaneous observation

Running currently accessible model endpoints in 2026/2027 does not automatically reconstruct what an earlier model endpoint produced in 2024. Exact historical model versions and archived evidence are required for valid temporal comparisons.

**Control:** model-version registry and explicit availability dates; do not fabricate unavailable historical observations.

### R2 — Benchmark contamination may eliminate much of HumanEval/MBPP for newer models

The protocol's contamination rule is deliberately conservative and may make standard old benchmarks unusable for some comparisons.

**Control:** report K4 mechanically; preserve exclusions; do not weaken the rule post hoc.

### R3 — Provider model aliases can change

Aliases may silently point to newer snapshots.

**Control:** prefer pinned snapshot identifiers; capture raw provider model ID in every execution.

### R4 — Historical price reconstruction

API prices change independently of capability.

**Control:** effective-dated pricing evidence and immutable pricing snapshots.

### R5 — Pass@1 comparability

Different prompt wrappers, sampling parameters, tool access, or retry policies can change the estimand.

**Control:** execution manifests and fixed prompt/evaluator versions.

### R6 — Agent overhead definition

The protocol states alpha is observed rather than assumed, but exact operational computation requires implementation precision.

**Control:** retain all component costs and publish the calculation formula before confirmatory analysis.

### R7 — Regression interpretation

Tier is ordinal and strongly linked to price/capability; implementation must not overstate causal interpretation.

**Control:** report the registered model faithfully and label additional robustness analyses exploratory unless pre-specified.

---

# 32. Decisions That Must Be Frozen Before Full Data Collection

The protocol does not fully determine the following implementation details. They should be resolved and timestamped **before confirmatory results are inspected**:

1. exact model snapshots for each historical/current date;
2. exact selected LeetCode contest/problem sampling rule;
3. inference temperature and other sampling parameters;
4. canonical prompt wrapper;
5. treatment of provider transport failures versus scientific retries;
6. exact bootstrap resampling unit and CI construction method;
7. exact hardware-index interpolation rule;
8. exact operational formula for observed `agent_overhead_α`;
9. exact test-case coverage rule for the LeetCode subset;
10. fixed-effects software/estimator options and standard-error treatment.

These are implementation freezes, not amendments to the scientific hypotheses.

---

# 33. Recommended Immediate Sprint

The first coding sprint should **not call any paid model API**.

Implement only:

1. repository/package skeleton;
2. `protocol_frozen_v1.0.yaml`;
3. Pydantic schemas;
4. task/model/pricing/hardware registry schemas;
5. contamination rule engine;
6. protocol-integrity tests;
7. synthetic fixture dataset;
8. cost/min-tier/CCR/Kill-Criteria unit tests;
9. GitHub Actions CI.

This gives the project a scientifically safe foundation before any empirical observations are generated.

---

## Final Governance Rule

> The implementation exists to test the frozen protocol. The protocol does not exist to accommodate the implementation or the observed results.

Any discrepancy between code behavior and the frozen Pilot 01 protocol must be surfaced, logged, and resolved transparently before confirmatory analysis proceeds.
