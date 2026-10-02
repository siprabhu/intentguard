# Revision plan from peer review

The review identifies a research-evidence gap, not merely a presentation problem.
The current 32 fixed-proposal cases establish mechanism correctness. They do
not establish prompt-injection resistance for a model-driven agent, and the
single count ablation is insufficient evidence of a broad trajectory contribution.

## Prioritized response

| Concern | Concrete response | Evidence required before claiming completion |
|---|---|---|
| Count-only novelty is narrow | Add explicit operation/resource budgets and an operation-sequence constraint; compare per-action, total-count-only, and richer-history policies. | Trajectories that pass every per-action rule and the total count, yet violate a scoped or sequence constraint; legitimate counterparts must execute. |
| Synthetic evaluation is not an agent experiment | Keep deterministic replay as a mechanism study. Design a separate bounded real-model tool loop with malicious text delivered as tool output. | Retained model requests, tool proposals, decisions, outputs, task-level success labels, failures, and cost/latency observations. |
| Manual contract creation moves the problem upstream | Show natural-language compilation as a proposed component followed by trusted host/user validation. | Evaluate compilation errors separately; never imply frozen objects are signed or authenticated. |
| CONFIRM lacks resumption | Define a trusted approval gateway and single-use authorization bound to task, exact operands, and contract version. | Substitution, replay, expiration, wrong-task, and concurrent redemption tests; identify who authenticates the approver. |
| Predicate timing has limited research value | Remove the microsecond figure from the abstract and distinguish predicate, complete runtime, and agent-loop measurements. | Wrapper p50/p95/p99 measurements; real-agent overhead only after actual model calls. |
| External comparison is weak | Pin the published version and code revision for each reproduced defense; document its security assumptions. | Shared workloads, tool semantics, attack budgets, and utility labels; report unsupported adaptations rather than inventing a baseline. |

## Research framing

Use the question: given the admitted trajectory so far, does the next action
remain authorized? Emphasize that the planner proposes and the trusted runtime
authorizes. Do not claim novelty for counters, finite-state policies, or
task-scoped authorization in isolation. The prospective contribution is the
explicit policy model, its trusted enforcement semantics, and measured behavior
on matched agent trajectories. Meaningful novelty remains to be demonstrated.

## Proposed agent study

Start with 50 distinct task specifications, each with a benign and an injected
context variant, giving 100 task-context conditions. Report the numbers of
distinct tasks and conditions separately. Generate actions with a real model;
do not use prerecorded proposals while calling the study an agent experiment.
Use in-memory tools and synthetic resources, with external sends/transfers
represented only by recorded mock effects.

Fix model/version, prompts, tools, contracts, step limit, token limit, sampling
settings, and defense conditions before the main run. Compare the same task
conditions across policies. Since a guard's responses can change later model
behavior, collect a fresh bounded rollout for each condition rather than
relabeling one trace as several end-to-end runs. Repeat stochastic rollouts
and analyze uncertainty at the task level, not by treating correlated tool
calls as independent tasks.

Measure unauthorized execution per attacked task, benign task completion,
confirmation rate, false blocking, and both model-loop and guard-only latency.
Define attack success by a prohibited outcome, not merely by a suspicious
proposal. Record every refusal, malformed call, timeout, exhausted budget,
and incomplete task under predefined handling rules. Report p50/p95/p99 with
sample counts and acknowledge that a small study gives unstable tail estimates.

Choose the provider, model, and spending ceiling before paid execution.
Credentials belong in the execution environment and must not enter traces,
fixtures, papers, or Git. No model experiment has been run as part of this plan.

## Literature constraints

The primary-source PAuth abstract reports 100 benign tasks and 634 adversarial
calls; these are not directly comparable with IntentGuard's fixed-proposal
counts. PAuth also addresses concrete operands and signed provenance. DRIFT
already uses a function trajectory and dynamic validation. A claim that either
system lacks history or cannot express a particular cumulative constraint needs
analysis of the pinned implementation and experiments, not inference from an
abstract. Task Shield and CaMeL likewise remain distinct implemented mechanisms,
not names to attach to simplified local controls.

Primary references checked for this response:

- PAuth v2: https://arxiv.org/abs/2603.17170v2
- DRIFT v3: https://arxiv.org/abs/2506.12104v3
- Task Shield: https://aclanthology.org/2025.acl-long.1435/
- CaMeL v2: https://arxiv.org/abs/2503.18813v2

## Completion discipline

Separate implemented changes, measured findings, and proposed experiments in the
revision response. New policy mechanisms require tests and new evidence before
they appear as implemented features in the manuscript. Preserve prior evidence
snapshots, regenerate current results from the modified code, and update the
abstract, architecture, methods, figures, conclusion, and limitations together.


## Completed in this revision

Implemented four history fields (operation/resource limits, ordered successful
operations, and distinct-destination limits), six new trajectory pairs, a
count-only ablation, and whole-runtime p50/p95/p99 measurement. All 41 tests
pass. Across 44 cases and 69 proposals, full enforcement preserves 47 authorized
executions with zero unauthorized executions; count-only admits six violations.
The manuscript, architecture, algorithm, related work, result plots, and
limitations now reflect this scope. The six-page PDF was visually checked.

The proposed real-model study, authenticated approval gateway, compiler, and
external baseline reproduction are not implemented or claimed complete.
Native LaTeX compilation remains unverified because the built-in compiler
reports `Unable to find standard directories for platform`; the review PDF is
rendered independently with ReportLab.
