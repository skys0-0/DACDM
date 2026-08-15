# DACDM Pilot 01: Pre-Inference Termination under the Preregistered K4 Contamination Criterion

**Publication release candidate:** RC1  
**RC freeze phase:** `S1.5_PUBLICATION_RELEASE_CANDIDATE_AND_ZENODO_METADATA_FREEZE`  
**Pilot closure date:** 2026-08-15  
**Conceptual originator:** CHAU HUNG SAN / 辛秋雄  
**Research classification:** methodological termination report / preregistered design result  
**Zenodo publication status:** not published

## Abstract

DACDM Pilot 01 was preregistered to test Complexity Migration (H2) and Compression Beyond Hardware (H4) in code generation. The preregistered protocol fixed the contamination rule, the K4 threshold of more than 30%, and the rule that any registered kill criterion terminates the pilot. It did not explicitly define the K4 denominator or freeze the exact final test-window model membership.

Before confirmatory model-performance inference and before the final K4 decision, S1.3.11 operationalized the K4 denominator as the pre-contamination registered task universe: 164 HumanEval tasks, 974 MBPP tasks, and 163 LeetCode Weekly Contest Hard metadata candidates, for 1,301 unique tasks. S1.3.12 then froze a four-model anchor set using all canonical models already present in the validated registry. This exact anchor set was not part of the original preregistration and was frozen after pre-inference contamination sensitivity was already known; it was nevertheless fixed before paid or confirmatory model-performance inference.

Under these pre-inference operationalizations, 1,165 tasks were known contamination exclusions, 132 were eligible, and 4 were indeterminate because of month-precision cutoff boundaries. The strict known exclusion share was 89.5465%, above the frozen 30% K4 threshold without counting any indeterminate task as excluded. Pilot 01 therefore terminates before confirmatory inference under K4. The protocol mechanically classifies K4 as a falsification condition, but this result is not a model-performance refutation of H2 or H4 because no confirmatory model-performance results were collected or inspected.

## 1. What was preregistered

The frozen Pilot 01 protocol established the following relevant rules before the present termination decision:

- a task is excluded if its public release date precedes the training cutoff date of any model used in the test window;
- for unknown cutoffs, the conservative six-month public-launch fallback applies;
- K4 is triggered when more than 30% of tasks in the dataset are flagged for contamination and excluded;
- any registered kill criterion is treated by the protocol as a falsification condition;
- post-hoc changes to kill criteria and minimum-effect thresholds are prohibited.

The original frozen protocol remains unchanged.

## 2. What was operationalized after preregistration but before confirmatory inference

The protocol did not explicitly define the denominator used to compute the K4 contamination-exclusion share. S1.3.11 resolved this ambiguity before the formal K4 decision by freezing:

`PRE_CONTAMINATION_REGISTERED_TASK_UNIVERSE`

This interpretation retains contaminated tasks in the denominator used to measure contamination and prevents the exclusion process from erasing its own numerator. It is a post-preregistration implementation interpretation, not text that was literally frozen in the original protocol.

The protocol also listed representative models by tier but did not freeze the exact final model membership for K4. S1.3.12 selected:

`ALL_CANONICAL_MODELS_PRESENT_BEFORE_S1_3_12`

The resulting anchor set contained:

- `anthropic:claude-3-5-haiku-20241022`
- `anthropic:claude-3-5-sonnet-20240620`
- `openai:gpt-4o-2024-05-13`
- `openai:gpt-4o-mini-2024-07-18`

This exact set was frozen after S1.3.11 had already exposed pre-inference contamination sensitivity. It was not chosen using model-performance outcomes, because no confirmatory model-performance results had been collected or inspected. The formal K4 result should therefore be read as an application of the frozen protocol together with the documented S1.3.11 and S1.3.12 pre-inference operationalizations.

## 3. Why later tier expansion cannot rescue this K4 result

The registered contamination rule is an ANY-model predicate: a task is excluded if it predates the cutoff of any model in the test window. Conditional on the legitimacy of the frozen anchor models as members of the test window, adding further T1, T2, T3, Gemini, or later models cannot convert an already excluded task into an eligible task. Model-set expansion can only preserve or enlarge the excluded set.

This monotonicity property does not retroactively make the exact four-model anchor set preregistered. It only explains why additional model tiers are unnecessary to rescue the already-triggered K4 decision once the anchor set is accepted as the minimum frozen test-window set.

## 4. Final K4 result

| Quantity | Frozen result |
|---|---:|
| Denominator | 1,301 |
| Known excluded | 1,165 |
| Eligible | 132 |
| Indeterminate | 4 |
| Strict known exclusion share | 89.5465% |
| Conservative share including indeterminate | 89.8540% |
| K4 threshold | 30.00% |
| Formal K4 status | **K4_TRIGGERED** |

The four indeterminate tasks are not required for the decision. The known-exclusion share alone exceeds the registered threshold.

## 5. Scientific interpretation boundary

The primary external-facing description of this result is:

**pre-inference termination under the preregistered K4 contamination criterion.**

The protocol mechanically classifies K4 as a falsification condition. That terminology is preserved as part of the historical preregistration, but it must not be interpreted as empirical model-performance evidence against DACDM's H2 or H4 mechanisms.

No confirmatory model-performance results were inspected. K1, K2, and K3 were not evaluated. No registered fixed-effects regression was estimated. No confirmatory CCR series was computed. No H4 hardware-adjusted performance test was conducted. No paid confirmatory model inference was run.

Accordingly, Pilot 01 closes as a methodological/design termination, while the substantive H2/H4 mechanisms remain untested by Pilot 01 performance data.

## 6. Frozen protocol documentation defect

The mandatory contamination policy says that tasks released before a model training cutoff are excluded. The Data Dictionary later contains the opposite sign in its short description of `exclude_contamination`.

This internal inconsistency is retained as a documented limitation. The implementation followed the main mandatory contamination policy using the recorded authority hierarchy in which the frozen protocol governs, together with the SDD/Implementation Freeze precedence statements. The 30% K4 threshold was not changed.

An independent reader may reproduce the Data Dictionary's opposite-sign wording as an alternative rule, but doing so would implement a different contamination direction from the mandatory policy used by the project. The publication does not silently rewrite the frozen source text.

## 7. Additional limitations

The K4 denominator semantics and exact anchor model set were not literally preregistered. They were frozen later, before confirmatory inference, and are therefore pre-inference operationalizations rather than original protocol text.

The anchor model set does not constitute complete T1/T2/T3 confirmatory coverage. This does not change the monotonic K4 result under the ANY-model contamination rule, but it means Pilot 01 never reached the stage required to evaluate K1-K3 or model-tier migration.

Historical snapshot availability was incomplete for some retired models. No successor-model substitution or historical backcast was used to fabricate missing exact snapshots.

## 8. Authorship, AI assistance, and automation disclosure

Conceptual synthesis and DACDM formulation attributed to CHAU HUNG SAN (辛秋雄). Drafting, structuring, and literature synthesis were AI-assisted. This wording distinguishes conceptual authorship from automated drafting and does not assert peer review, institutional affiliation, or priority over unpublished independent work.

For this termination report, repository automation also generated deterministic package artifacts and validation outputs from frozen inputs. Automated generation does not change the authorship attribution above and does not imply independent peer review.

## 9. Reproducibility

The frozen S1.3.13 evidence package remains preserved unchanged. RC1 is a separate publication candidate created in response to the S1.4 adversarial review; it does not overwrite or revise the historical evidence package.

The publication manifest records the publication-payload freeze commit, source package commit, protocol blob identity, S1.3.12 K4 freeze commit, file SHA-256 values, byte sizes, and no-inference scientific guards.

## 10. Zenodo publication plan

This RC is not a Zenodo publication. The new methodological termination report should be deposited as a separate Zenodo record rather than replacing the existing DACDM conceptual-framework record.

Before producing a DOI-bearing PDF or DOCX, the next gate should create a Zenodo draft and reserve a new DOI. The actual publication date should be set to the date the record is first made public. Creator metadata should use family name `SAN` and given names `CHAU HUNG`. The final live Zenodo form should confirm the publication/report resource subtype and the exact related-identifier relation used to link the existing DACDM working-paper and concept DOIs.

Existing related DACDM identifiers:

- version DOI: `10.5281/zenodo.21930795`
- concept DOI: `10.5281/zenodo.21930794`

## 11. Release status

RC1 addresses the S1.4 narrative and provenance objections without changing the K4 arithmetic, threshold, task contamination statuses, denominator membership recorded by S1.3.11, anchor-set evidence recorded by S1.3.12, or the fact that confirmatory model-performance inference never occurred.

The next gate is DOI reservation and final document rendering, not additional Pilot 01 model inference.
