# DACDM Pilot 01 — Code Generation Complexity Compression

**Protocol Version:** 1.0  
**Date Frozen:** 2026-08-14  
**Pre-registration Status:** Frozen. No changes to this protocol will be made after this date, regardless of results.  
**Associated Framework:** DACDM Conceptual Framework v1.0 (Hung, 2026)

---

## 1. Pilot Objective

This pilot tests whether **Complexity Migration (H2)** and **Compression Beyond Hardware (H4)** are observable in a controlled, well-measured task domain: **code generation**.

Specifically, it asks:

> For a fixed set of programming tasks, does the minimum-cost execution pathway that clears a fixed quality threshold shift from frontier-tier models to mid- or small-tier models over the 2024–2026 period, at a rate exceeding hardware efficiency improvements alone?

---

## 2. Task Family Definition

**Domain:** Code generation from natural-language problem statements.

**Task Sources (three tiers of difficulty):**

| Tier | Benchmark | Description | Quality Anchor |
| :--- | :--- | :--- | :--- |
| Easy | HumanEval | 164 hand-written programming problems | Pass@1 |
| Medium | MBPP (Mostly Basic Python Problems) | 974 problems, basic Python | Pass@1 |
| Hard | LeetCode Weekly Contest Problems (selected) | Problems from contests, filtered by timestamp | Pass@1 + test case coverage |

**Contamination Policy (Mandatory):**

- All tasks must have a **public release date** (e.g., LeetCode contest date).
- A task is **excluded** if its release date precedes the **training cutoff date** of any model used in the test window.
- For models with unknown training cutoff, we apply a conservative filter: exclude any task released more than 6 months before the model’s public launch.
- This ensures that observed performance gains reflect genuine reasoning, not data contamination.

---

## 3. Quality Threshold (Fixed Quality Anchor)

The pilot uses **Pass@1** as the primary quality metric.

- **Fixed Quality Threshold:** 80% Pass@1 on HumanEval, 75% on MBPP, 60% on LeetCode-hard subset.
- A task is considered “solved” for the purpose of minimum-cost pathway if the model’s Pass@1 meets or exceeds the threshold.
- **Secondary (Exploratory) Quality Anchor:** We also record the *best available* Pass@1 for each task-date as a contemporary benchmark, but the primary CCR computation uses the fixed threshold.

---

## 4. Model Tier Classification (Frozen)

Models are classified into three tiers based on **publicly available capability benchmarks and API pricing**, independent of provider claims:

| Tier | Label | Representative Models (2024–2026) | Criteria |
| :--- | :--- | :--- | :--- |
| **T1** | Small / Fast / Cheap | GPT-4o-mini, Claude 3.5 Haiku, Gemini 1.5 Flash | Low cost, low latency, < 100B parameter equivalent |
| **T2** | Mid-tier | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro | Moderate cost, high capability, used for most production tasks |
| **T3** | Frontier / Reasoning | o1-preview, o1-mini, Claude 3.7 Opus, GPT-5 (if available) | High cost, test-time scaling, reasoning tokens, reserved for hard tasks |

*Note: If a new model is released, it is assigned to a tier based on its benchmark performance and price, using the same criteria. The tier assignment is applied consistently across all dates.*

---

## 5. Unit of Analysis and Agent Overhead (α)

**Primary unit of analysis:** A single user-level code generation objective (U).

**Agent subtask decomposition:** If an agent (e.g., AutoGPT, Devin) is used to solve U, we record the total API calls and cost incurred to complete U. We define:

$$
c(U) = c_{base} + \alpha \cdot \sum_{s=1}^{k} c(S_s)
$$

where:
- \( c_{base} \) = cost of the final answer generation call
- \( S_s \) = any subtask executed by the agent (tool calls, retrieval, test execution, reflection/retry)
- \( \alpha \) = agent overhead multiplier (observed, not assumed). If no agent is used, α = 0.

**Policy:** If the execution involves an agent, the total cost \( c(U) \) is used as the observation; we do not treat each subtask as an independent task (to avoid double-counting).

**Interpretive note:** `agent_overhead_α` is recorded as a descriptive overhead measure. The authoritative cost observation is the total end-to-end cost of U. It must not be used to multiply already-summed subtask costs a second time in implementation.

---

## 6. Key Dependent Variables

| Variable | Definition |
| :--- | :--- |
| `min_cost` | Minimum observed API cost to achieve the quality threshold for a given task-date |
| `min_tier` | Lowest model tier (T1–T3) that achieves the quality threshold |
| `tier_share` | Proportion of tasks in each tier achieving the threshold |
| `ccr_task` | Task-count weighted downward transition probability (L4→L3, L3→L2, etc.) over 6-month rolling windows |
| `cost_deflated` | API cost deflated by hardware performance-per-dollar trend (Epoch AI GPU price/FLOP index) |

---

## 7. Empirical Model (Fixed Effects Regression)

To isolate the effect of model tier and time, we estimate:

$$
\ln(\text{cost}_{i,t}) = \beta_1 \cdot \text{Tier}_{i,t} + \beta_2 \cdot \text{Time}_t + \gamma_i + \epsilon_{i,t}
$$

where:
- \( i \) = task (fixed effect, absorbing task-level difficulty)
- \( t \) = month (2024–2026)
- \( \text{Tier}_{i,t} \) = ordinal variable (1, 2, 3) for the minimum tier that clears the quality threshold at that date
- \( \text{Time}_t \) = linear time trend (or monthly dummies)

**Interpretation:**
- \( \beta_1 < 0 \) implies that tasks are being solved by cheaper (lower-tier) models over time (Complexity Migration).
- \( \beta_2 \) captures hardware/algorithmic efficiency improvements common across all tasks.

**To test H4 (Compression Beyond Hardware):** We compare the observed cost decline against a counterfactual where only hardware performance-per-dollar improves (i.e., \( \beta_1 = 0 \)). If observed decline > hardware-only decline, H4 is supported.

---

## 8. Complexity Compression Rate (CCR) Estimation

We estimate CCR using **6-month rolling windows**:

$$
CCR_t = \sum_{i>j} w_i \cdot P_{i \rightarrow j, t}
$$

where \( P_{i \rightarrow j, t} \) is the empirical probability that a task requiring tier i at time t-6 can be solved by tier j (j < i) at time t.

We compute two versions:
- **CCR_task** (weighted by task count)
- **CCR_compute** (weighted by compute cost of the original high-tier pathway)

---

## 9. Minimum Detectable Effect / Kill Criteria (Pre-registered)

**Minimum effect threshold:** For H4 to be considered supported, the deflated cost decline (after removing hardware gains) must be at least **15% per year** on average across the 2024–2026 period.

**Kill Criteria (Falsification conditions):**

The pilot is considered a *falsification* of DACDM’s core mechanism if ANY of the following are observed in the final data:

| Criterion | Description |
| :--- | :--- |
| **K1** | No statistically significant downward migration in tier (β₁ ≥ 0, p > 0.05) |
| **K2** | The observed cost decline is **less than or equal to** the hardware-only counterfactual across two consecutive years |
| **K3** | The frontier tier (T3) share of tasks achieving the quality threshold does **not decline** over the 24-month window |
| **K4** | More than 30% of tasks in the dataset are flagged for data contamination (excluded) |

**If K1–K3 are met:** The pilot will be published as a *null result* with the title:  
> *"Complexity Compression in AI Coding Tasks: A Null Finding with Infrastructure Implications"*  

**If H2/H4 are supported:** The pilot will be published as the first empirical validation of DACDM.

---

## 10. Uncertainty Quantification (Bootstrap)

We use **non-parametric bootstrap** (1,000 replications) to construct 95% confidence intervals for:
- \( \beta_1 \) and \( \beta_2 \) coefficients
- CCR_t at each rolling window
- CACP index (if computed)

Confidence intervals are reported alongside point estimates. All p-values are two-sided.

---

## 11. Data Sources

| Source | Use |
| :--- | :--- |
| HumanEval / MBPP (OpenAI, Google) | Task database |
| LeetCode Weekly Contest archive | Timestamped hard tasks |
| Epoch AI API pricing database | Historical model pricing |
| Epoch AI GPU performance/$ trends | Hardware counterfactual |
| Model provider API logs (simulated/own queries) | Cost, tokens, latency |
| HuggingFace Open LLM Leaderboard | Model capability ranking |
| PaperWithCode / official model cards | Training cutoff dates for contamination filter |

**Proprietary telemetry disclaimer:** Where exact reasoning token counts are unavailable (e.g., closed APIs), we record the field as `NA` and conduct sensitivity analysis excluding these observations.

---

## 12. Data Dictionary (Pilot Version)

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique task identifier (benchmark + problem ID) |
| `task_tier` | categorical | Easy / Medium / Hard |
| `date` | date | Execution date (YYYY-MM) |
| `model` | string | Full model name |
| `model_tier` | categorical | T1 / T2 / T3 |
| `pass_1` | float | Pass@1 score (0–1) |
| `input_tokens` | integer | Number of input tokens |
| `output_tokens` | integer | Number of output tokens |
| `reasoning_tokens` | integer | Reasoning tokens (if observable; NA otherwise) |
| `tool_calls` | integer | Number of tool calls made |
| `retries` | integer | Number of retry attempts |
| `latency_sec` | float | End-to-end latency in seconds |
| `api_cost_usd` | float | Total API cost in USD |
| `agent_overhead_α` | float | Observed agent overhead multiplier |
| `meets_threshold` | boolean | Whether Pass@1 ≥ fixed threshold |
| `min_tier_this_date` | categorical | Lowest tier achieving threshold for that task-date |
| `hardware_perf_index` | float | Epoch AI GPU performance per $ (normalized to 2024=1) |
| `exclude_contamination` | boolean | Excluded if release date > training cutoff |
| `source_url` | string | URL to benchmark / problem statement |
| `notes` | string | Free text |

---

## 13. Execution Timeline

| Phase | Timeline | Deliverable |
| :--- | :--- | :--- |
| Data collection & cleaning | 2026 Q4 – 2027 Q1 | Curated panel dataset |
| Model inference & cost logging | 2027 Q1 – Q2 | Full panel with min_tier per task-date |
| Analysis & bootstrap | 2027 Q2 | Regression results, CCR curves |
| Draft report | 2027 Q3 | Pilot working paper |
| Submission | 2027 Q4 | Null or validation result |

---

## 14. Amendment Policy

**This protocol is frozen as of 2026-08-14.**

No amendments will be made after this date unless:

1. A critical data error is discovered in the data sources (e.g., mislabeled benchmark tasks), and
2. The error is objectively verifiable by an independent reviewer.

Any amendment will be documented with a timestamp, rationale, and effect on results. Post-hoc adjustments to the kill criteria or minimum effect threshold are **expressly forbidden**.

---

## References

- Chen, M. et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*.
- Epoch AI (2026). Trends in Artificial Intelligence.
- OpenAI (2024). HumanEval dataset.
- Austin, J. et al. (2021). Program Synthesis with Large Language Models. *arXiv:2108.07732*.

---

**Sign-off:**

Conceptual Framework Author: SAN CHAU HUNG / 辛秋雄  
Protocol Prepared: 2026-08-14  
Version: 1.0 (Frozen)
