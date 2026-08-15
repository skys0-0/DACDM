# DACDM Pilot 01: Pre-Inference Termination under a Preregistered Contamination Criterion

**Package version:** 1.0  
**Phase:** `S1.3.13_PILOT_01_PREINFERENCE_TERMINATION_PACKAGE`  
**Closure date:** 2026-08-15  
**Conceptual originator:** CHAU HUNG SAN / 辛秋雄  
**Research status:** Preregistered pre-inference termination / methodological result  
**Source commit used to generate this package:** `202880b3f6570270ab0a1f3257f680e20e9952a0`

## Abstract

DACDM Pilot 01 was preregistered to test Complexity Migration (H2) and Compression Beyond
Hardware (H4) in code generation. Before confirmatory model inference, the research pipeline
applied the frozen contamination rule and the preregistered K4 kill criterion. The K4
denominator was frozen before the final decision as the pre-contamination registered task
universe: 164 HumanEval tasks, 974 MBPP tasks, and 163 LeetCode Weekly Contest Hard metadata
candidates, for 1,301 unique tasks. With the non-outcome-selected test-window anchor model set,
1,165 tasks were known contamination exclusions, 132 were eligible, and 4 remained
indeterminate because of month-precision cutoff boundaries. The strict known exclusion share
was 89.5465%, exceeding the frozen 30% K4 threshold without counting any indeterminate
task as excluded. Under the frozen protocol, K4 is therefore triggered and Pilot 01 must stop
before paid confirmatory inference. This is a protocol-defined falsification/termination of
Pilot 01. It is not a model-performance refutation of H2 or H4 because no confirmatory model
performance results were collected or inspected.

## 1. Governing preregistration

The frozen Pilot 01 protocol states that a task is excluded when its release date precedes the
training cutoff date of any model used in the test window. It also defines K4 as triggered when
more than 30% of tasks in the dataset are flagged for contamination and excluded. The protocol
states that the pilot is considered a falsification if any registered kill criterion is
observed, and expressly forbids post-hoc changes to the kill criteria or minimum-effect
threshold.

The protocol remains unchanged. This report records the consequence of applying it.

## 2. Pre-inference decision sequence

The implementation separated denominator definition from the final numeric K4 decision.
S1.3.11 froze the denominator as the pre-contamination registered task universe so that tasks
could not disappear from the denominator merely because they were contaminated or later failed
an oracle gate. S1.3.12 then froze every canonical model already present in the validated model
registry before that phase as the test-window anchor set. No model was added or removed based on
the K4 result.

S1.3.10 had previously completed task-level IF-09 oracle validation for the registered external
LeetCode suites: 24 tasks were task-level IF-09 ready and 21 were not.
Those oracle results do not alter the K4 denominator or numerator. Oracle insufficiency is not
counted as contamination.

## 3. Frozen test-window anchor model set

- `anthropic:claude-3-5-haiku-20241022`
- `anthropic:claude-3-5-sonnet-20240620`
- `openai:gpt-4o-2024-05-13`
- `openai:gpt-4o-mini-2024-07-18`

Selection rule: `ALL_CANONICAL_MODELS_PRESENT_BEFORE_S1_3_12`.

The anchor set is sufficient for the K4 decision because the registered contamination rule uses
an ANY-model predicate. Once a task is excluded because of one selected model's cutoff, adding
another model cannot make that task eligible again. Therefore a strict exclusion share already
above 30% cannot be rescued by later tier expansion.

## 4. Final K4 result

| Quantity | Frozen result |
|---|---:|
| Denominator | 1301 |
| Known excluded | 1165 |
| Eligible | 132 |
| Indeterminate | 4 |
| Strict known exclusion share | 89.5465% |
| Conservative share incl. indeterminate | 89.8540% |
| K4 threshold | 30.00% |
| Formal K4 status | **K4_TRIGGERED** |

The four indeterminate tasks are not needed for the decision. The known-exclusion share alone
exceeds the registered threshold.

## 5. Scientific interpretation boundary

Two statements must be reported together.

First, **the frozen Pilot 01 protocol classifies this outcome as a falsification condition and
requires termination because K4 is triggered**. The project must not weaken or redefine K4 after
seeing this result.

Second, **this outcome is not an empirical model-performance test of H2 or H4**. No confirmatory
model performance results were inspected, K1-K3 were not evaluated, no registered fixed-effects
model was estimated, no confirmatory CCR was calculated, and no paid model inference was run.
The substantive mechanism therefore remains untested by Pilot 01 performance data.

This report uses the phrase **protocol-defined falsification / pre-inference termination** to
preserve both facts without converting a benchmark-admissibility failure into evidence about
model performance that was never observed.

## 6. Frozen protocol documentation defect

The mandatory contamination policy says that release dates **preceding** a model training cutoff
are excluded. The protocol Data Dictionary later contains the opposite sign in the short field
description for `exclude_contamination`. The implementation did not silently amend the frozen
protocol. S1.3.11 recorded the authority hierarchy and applied the mandatory policy together with
the SDD/Implementation Freeze precedence rule that the frozen protocol governs. The conflicting
Data Dictionary phrase is retained as a documented defect and does not change the K4 result.

## 7. Why Pilot 01 is not being rescued

No post-hoc denominator change is made. No contaminated task is removed before computing the
contamination share. No post-oracle survivor set is substituted for the registered task universe.
The 30% threshold is unchanged. The test-window anchor models were selected by a rule fixed
without reference to model outcomes, and the four cutoff-boundary indeterminate tasks are not
needed to trigger K4.

## 8. Research consequence

Pilot 01 closes at the pre-inference stage. Confirmatory model inference, K1-K3 evaluation,
registered regression, confirmatory CCR estimation, and H4 hardware-adjusted performance testing
are not performed under this pilot. The original DACDM Conceptual Framework and the frozen Pilot
01 Protocol remain preserved as historical research objects.

A future Pilot 02, if created, must be separately preregistered and should use a timestamped,
contamination-resistant task stream designed around contemporary/post-cutoff tasks. It must not
be represented as a continuation that retroactively changes Pilot 01.

## 9. Publication classification

Recommended classification: **methodological / negative research report**.

Recommended title: **DACDM Pilot 01: Pre-Inference Termination under a Preregistered Contamination Criterion**.

This package is prepared for review and later independent Zenodo publication. Generating this
package does not itself publish a Zenodo record or assign a new DOI.

## 10. Reproducibility and provenance

Machine-readable closure status, K4 assessment, source hashes, model-set identity, and package
inputs are stored beside this report in the S1.3.13 publication package. The generator refuses
to build the package unless S1.3.12 reports `K4_TRIGGERED`, confirms that no model results were
inspected, and keeps paid inference disabled.
