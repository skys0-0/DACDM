# Dynamic AI Compute Demand Model (DACDM): Complexity Migration, Cognitive Commoditization, and the Dynamics of AI Infrastructure Demand

**Author / Conceptual Originator:** SAN CHAU HUNG  
**Document type:** Conceptual working-paper framework  
**Version:** 1.0 — 14 August 2026

## Abstract

This paper proposes the Dynamic AI Compute Demand Model (DACDM), a research framework for explaining and forecasting artificial-intelligence compute demand when task difficulty is endogenous rather than fixed. Conventional infrastructure narratives often map adoption, token volume, or model scaling directly into accelerator and electricity demand. DACDM instead models a distribution of task-complexity states and allows tasks to migrate from difficult, exploratory states toward cheaper execution states through repetition, procedural memory, routing, caching, distillation, software optimization, and deterministic codification. At the same time, new human and machine activity creates novel high-complexity tasks, while test-time scaling and agentic workflows can increase compute per frontier task. The central empirical contest is therefore between Novel Complexity Creation and Complexity Compression. The paper specifies state variables, transition equations, testable hypotheses, a retrospective 2024–2026 research design, candidate data sources, falsification criteria, and an extension from effective compute demand to GPU capital stock and electricity constraints. The framework does not assert that GPU or electricity demand must decline. It provides a falsifiable mechanism for determining when AI activity can continue rising while marginal demand for frontier compute, GPU capacity, or electricity grows more slowly, plateaus, or falls.

**Keywords:** AI compute demand; complexity migration; procedural memory; knowledge distillation; model routing; GPU demand; inference economics; data-center electricity; cognitive commoditization

## 1. Research Question and Contribution

The primary research question is: How does aggregate AI compute demand evolve when repeated cognitive tasks become progressively cheaper to execute, while new high-complexity tasks continue to be created?

DACDM contributes a dynamic task-state framework. It distinguishes AI activity from effective compute demand, and effective compute demand from GPU purchases and electricity consumption. Its proposed novelty is not any single mechanism—distillation, routing, procedural memory, hardware efficiency, and test-time scaling are established research areas—but their integration into a common dynamic demand system with explicit complexity migration and novelty creation.

## 2. Conceptual Foundation

The framework begins from five observations supported by prior literature: (1) fixed-capability inference costs can fall rapidly; (2) knowledge distillation can transfer capabilities to smaller models; (3) routing can allocate easy queries to cheaper models; (4) procedural memory can reuse trajectories and procedures across analogous tasks; and (5) additional test-time compute can improve performance on difficult tasks. These mechanisms create opposing forces. Compression reduces compute required for previously solved task families, while frontier expansion creates or intensifies tasks that consume more compute.

## 3. Task Complexity States

Let N_i(t), i∈{1,…,5}, denote the stock or flow share of tasks at complexity level i at time t.

L1 — Codified/Routine: reliable retrieval, deterministic rules, cached answers, or trivial model inference.  
L2 — Established Method: known procedure with variable inputs and limited reasoning.  
L3 — Multi-step: planning, integration, tool use, or nontrivial verification.  
L4 — Exploratory: multiple uncertain solution paths, substantial search, experimentation, or adjudication.  
L5 — Frontier/Novel: no reliable procedure exists; solving the task may require method creation, extensive experimentation, or new knowledge.

Complexity is operational rather than semantic. A long summarization task can be L2, while a short unsolved mathematical prompt can be L5. Classification should therefore depend on novelty, reasoning depth, search-space size, uncertainty, verification cost, and the minimum reliable execution pathway available at that date.

## 4. Complexity Migration

Tasks may move downward in complexity as a system learns. Repetition can create reusable memories, procedures, routing policies, distilled models, caches, or deterministic code. Let M(t) be a transition matrix whose element P_ij(t) is the probability that a task family in state i at time t is executable at state j at t+1. Downward transitions such as P_43 or P_21 represent complexity compression. Upward transitions are allowed when environments change, requirements tighten, or prior procedures become invalid.

The task-state equation is:

N(t+1) = M(t)N(t) + A(t),

where A(t) represents newly arriving tasks. A_4(t) and A_5(t) are especially important because they measure novel high-complexity inflow.

## 5. Novel Complexity Creation vs. Complexity Compression

Define λ_N(t) as the rate at which new L4/L5 task families enter the system, and λ_C(t) as the rate at which existing high-complexity task families become reliably executable at lower complexity. The central structural hypothesis is not that λ_C must exceed λ_N. It is that the relative movement of these rates determines the growth of frontier-compute demand.

If λ_N > λ_C for a sustained period, frontier compute can expand rapidly even as old tasks become cheaper. If λ_C approaches or exceeds λ_N, total AI activity may continue to grow while frontier-compute demand grows more slowly or plateaus.

## 6. Compute Demand Equation

Let c_i(t) be raw compute required per task at complexity level i and E_i(t) be effective efficiency, incorporating hardware, model/algorithm, serving, routing, memory reuse, and software optimization. Let S_GPU,i(t) be the share of work in class i executed on general-purpose GPUs rather than CPUs, NPUs, TPUs, ASICs, caches, or deterministic software.

Effective GPU compute demand is:

G(t) = Σ_i [N_i(t) · c_i(t) · S_GPU,i(t) / E_i(t)].

This equation separates growth in task volume from changes in complexity mix, efficiency, and accelerator substitution.

## 7. Capacity, Utilization, and Capital Stock

Let u(t) denote utilization. Required installed effective capacity is K*(t)=G(t)/u(t). Let K(t) be installed GPU-equivalent capital stock and δ(t) its economic depreciation rate. Then:

K(t+1)=(1−δ(t))K(t)+I(t).

A simplified investment identity is:

I(t)=max[0, K*(t)−(1−δ(t))K(t)] + R(t),

where R(t) captures replacement demand. Economic depreciation can accelerate when newer accelerators deliver materially better performance per watt or per dollar, even if older devices remain technically functional. This allows GPU sales to remain strong temporarily even if structural compute-capacity growth slows.

## 8. Electricity Constraint

Let P(t) be power capacity available to AI/data-centre workloads and W(t) the power required per unit of deployed compute. Deployment is constrained by G_deployable(t) ≤ P(t)/W(t). Electricity price and grid availability should be treated separately: high electricity prices change operating economics, while unavailable grid capacity directly limits deployment. The IEA’s scenario work is useful because it explicitly varies AI uptake, efficiency, and bottlenecks rather than assuming a single path.

## 9. Testable Hypotheses

H1 — Workload Growth Deceleration: aggregate AI task volume continues to rise, but percentage growth declines as adoption matures.  
H2 — Complexity Migration: repeated task families exhibit statistically significant movement from higher-cost to lower-cost execution pathways over time.  
H3 — Frontier Share Decline: within mature task families, the share requiring frontier models declines.  
H4 — Compression Beyond Hardware: memory, routing, distillation, and software optimization explain material cost reductions beyond hardware performance-per-dollar improvements.  
H5 — GPU Elasticity Decline: the elasticity of GPU-equivalent installed capacity with respect to AI activity declines over time.  
H6 — Novelty Counterforce: rapid creation of new L4/L5 work can offset or dominate complexity compression.  
H7 — Replacement Wedge: GPU sales can temporarily diverge upward from structural capacity demand because energy efficiency and economic depreciation accelerate replacement.  
H8 — Power Bottleneck Interaction: constrained power can reduce deployable capacity while increasing the economic value of more energy-efficient accelerators.

## 10. Empirical Design: 2024–2026 Retrospective Panel

Construct a monthly or quarterly panel of stable task families: coding, summarization/extraction, research, customer service, quantitative reasoning, and agentic computer/tool use. For each date, estimate the lowest-cost execution pathway that clears a fixed quality threshold. Record model class, token use, reasoning/test-time compute, tool calls, latency, price, success rate, verification burden, use of memory/cache, and accelerator class when observable.

The key dependent variables are: minimum cost at fixed quality; minimum frontier-model share; effective compute proxy; complexity-state classification; and transition probability between states. A task family should not be reclassified as easier merely because a newer benchmark score is higher; the study must show that the same quality threshold can be met with a cheaper or structurally simpler pathway.

**Note on empirical implementation**: The framework’s empirical strategy is operationalized in a separate, pre-registered pilot protocol (`DACDM_Pilot_01_Protocol_v1.0`), which is timestamped and frozen prior to data collection. The pilot focuses on a single task domain (code generation) to test H2, H3, and H4 under controlled conditions. Results of the pilot will inform, but not retroactively alter, the core conceptual framework or the pre-registered protocol.

## 11. Identification Strategy

Three complementary designs are proposed. First, within-task longitudinal comparisons hold task family and quality threshold fixed while model and system technology change. Second, matched-pair comparisons contrast repeated task families with novel task families at the same date. Third, decomposition separates hardware improvement from software/system improvement using public accelerator performance-per-dollar trends.

Causal claims should remain conservative. API price reductions include competition, subsidies, utilization, and margin changes, so price is not identical to physical efficiency. The preferred outcome is a decomposition with sensitivity bands rather than a single point estimate.

## 12. Complexity Compression Rate (CCR)

Define CCR over a window as the weighted fraction of high-complexity workload that becomes executable at a lower complexity state while meeting the same quality threshold:

CCR_t = Σ_{i>j} w_i · P_{i→j,t}.

Weights can reflect task frequency, compute cost, or economic value. Separate CCR_task (task-count weighted) from CCR_compute (compute weighted). The latter is more relevant to infrastructure demand.

## 13. Complexity-Adjusted Compute Pressure (CACP)

A practical monitoring index is:

CACP_t = Growth(complexity-adjusted workload × GPU share) / Growth(effective efficiency × reuse).

CACP>1 indicates upward structural compute pressure; CACP≈1 indicates balance; CACP<1 indicates that efficiency/reuse is outrunning complexity-adjusted workload. The index should be estimated as a range because numerator and denominator are imperfectly observed.

## 14. Falsification Criteria

The framework should be rejected or materially revised if: (a) repeated task families do not migrate toward cheaper execution pathways after controlling for quality; (b) memory/routing/distillation savings are negligible relative to hardware gains; (c) the frontier-model share of mature tasks does not decline; (d) novelty creation persistently raises complexity-adjusted workload faster than all measured compression channels; or (e) CACP fails to explain GPU-capacity growth better than simpler adoption/token models out of sample.

## 15. Baselines for Comparison

Compare DACDM against at least three baselines: B1, token-volume growth; B2, user/adoption × average tokens per user; B3, capital-expenditure or accelerator-shipment trend extrapolation. Forecast evaluation should use rolling-origin backtests and metrics such as MAE/MAPE for capacity growth, directional accuracy for acceleration/deceleration, and calibration of prediction intervals.

## 16. Data Sources and Measurement Plan

Candidate public sources include model-provider API pricing and model cards; benchmark archives; Epoch AI hardware and inference-cost datasets; IEA data-centre electricity scenarios; public cloud/accelerator pricing; company disclosures; and peer-reviewed or preprint studies on routing, procedural memory, distillation, and test-time compute. Where proprietary telemetry is unavailable, the study should publish transparent proxy definitions and uncertainty intervals rather than fabricate monthly precision.

## 17. Risks and Limitations

Major limitations include selection bias in public benchmarks, API price subsidies, hidden provider utilization, unobserved proprietary accelerators, changing task definitions, benchmark contamination, endogenous demand created by falling prices (Jevons/rebound effects), and the possibility that agents create substantially more sub-tasks per user objective. Complexity classification itself can drift, so a frozen rubric and blinded re-rating protocol are required.

## 18. Expected Contributions

If supported, DACDM would contribute: (1) a distinction between AI activity and infrastructure demand; (2) a measurable Complexity Migration Curve; (3) a Complexity Compression Rate; (4) a decomposition of fixed-capability cost decline into hardware and system-learning channels; and (5) an explanation for how AI usage and revenue can rise while GPU-demand growth decelerates. The broader interpretation is an economics of cognitive commoditization: repeated cognitive work can move from expensive exploration toward cheaper reusable execution.

## 19. Research Status

**Research Status**: This document is a conceptual working-paper framework, not a validated forecasting model. It has not been empirically tested. The separate pilot protocol (`DACDM_Pilot_01_Protocol_v1.0`) is the first pre-registered attempt to subject H2–H4 to falsification. No claim of empirical support is made at this stage.

The component mechanisms are literature-supported, but the integrated macro-to-infrastructure relationship remains a hypothesis requiring data construction and backtesting. No claim of priority over independently developed unpublished work is made. The conceptual synthesis and DACDM formulation in this working document are attributed to SAN CHAU HUNG (辛秋雄), with AI-assisted drafting and literature synthesis.

## References

1. Epoch AI (2026). *How persistent is the inference cost burden?*. https://epoch.ai/gradient-updates/how-persistent-is-the-inference-cost-burden
2. Epoch AI (2026). *Trends in Artificial Intelligence*. https://epoch.ai/trends
3. Epoch AI (2026). *AI Chips: why they cost as much as a car, and why companies can't get enough*. https://epoch.ai/publications/chips-topic-overview
4. International Energy Agency (2025). *Energy and AI: Energy demand from AI*. https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai
5. Snell, C., Lee, J., Xu, K., & Kumar, A. (2024). *Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters. arXiv:2408.03314*. https://arxiv.org/abs/2408.03314
6. Yang, C. et al. (2024). *Survey on Knowledge Distillation for Large Language Models: Methods, Evaluation, and Application. arXiv:2407.01885*. https://arxiv.org/abs/2407.01885
7. Xu, X. et al. (2024). *A Survey on Knowledge Distillation of Large Language Models. arXiv:2402.13116*. https://arxiv.org/abs/2402.13116
8. Fang, R. et al. (2025). *Memp: Exploring Agent Procedural Memory. arXiv:2508.06433*. https://arxiv.org/abs/2508.06433
9. Ding, D. et al. (2025). *BEST-Route: Adaptive LLM Routing with Test-Time Optimal Compute. ICML 2025, PMLR 267*. https://proceedings.mlr.press/v267/ding25d.html
10. Forouzandeh, S. et al. (2025). *Learning Hierarchical Procedural Memory for LLM Agents through Bayesian Selection and Contrastive Refinement. arXiv:2512.18950*. https://arxiv.org/abs/2512.18950
11. Cao, Z. et al. (2025). *Remember Me, Refine Me: A Dynamic Procedural Memory Framework for Experience-Driven Agent Evolution. arXiv:2512.10696*. https://arxiv.org/abs/2512.10696

## Citation / 引用建議

Hung, S. C. (2026). *Dynamic AI Compute Demand Model (DACDM): Complexity Migration, Cognitive Commoditization, and the Dynamics of AI Infrastructure Demand*. Working paper framework, Version 1.0.
