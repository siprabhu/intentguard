# IntentGuard Literature and Novelty Review

Status: working review for Paper 1  
Verification date: 2026-08-25  
Primary-source matrix: `docs/literature-matrix.csv` and `docs/literature-matrix.xlsx`

## Review question

What contribution can IntentGuard make beyond existing work on task-scoped authorization, least-privilege tool policy, prompt-injection defense, provenance, information-flow control, and trajectory-aware runtime validation for tool-using AI agents?

## Current evidence base

The expanded matrix contains 23 primary sources from 2023–2026. Sources were selected for direct overlap with at least one of these dimensions:

- authorization derived from a user task;
- least-privilege tool selection or tool-call policy;
- runtime interception before consequential action;
- instruction or operand provenance;
- multi-step, trajectory, cumulative, or temporal reasoning;
- prompt injection and tool-output poisoning;
- agent-security benchmark design.

This is a focused closest-work review, not yet a systematic review. Before submission, record search strings, databases, inclusion/exclusion rules, screening decisions, and citation chaining.

## Findings by research cluster

### 1. Task-scoped authorization is established prior work

PAuth directly argues that operator-level permissions overprivilege agents relative to the concrete operations implied by a natural-language task. It introduces natural-language slices and provenance-carrying envelopes. Progent generates fine-grained privilege policies from user queries and enforces them deterministically. MiniScope reconstructs permission hierarchies and applies a mobile-style permission model. AuthBench evaluates whether coding agents can infer file-level least-privilege boundaries.

**Implication:** IntentGuard must not claim that deriving or enforcing permissions from a user task is novel.

### 2. Runtime action mediation is also established

Progent enforces policies at tool calls. AARM specifies interception before action execution, session-context accumulation, intent/policy evaluation, and authorization decisions. SEAgent monitors agent-tool interactions through an information-flow graph and applies mandatory access control. CaMeL prevents untrusted data from influencing control flow and uses capabilities to restrict data flows.

**Implication:** Placing a guard between agent reasoning and tool execution is a sound design choice, but it is not by itself a research contribution.

### 3. Semantic task alignment has a strong direct baseline

Task Shield evaluates whether directives and tool calls serve the user's objective. DRIFT constructs a minimal function trajectory and parameter checklist, then validates deviations. Progent also generates policies from the user query.

**Implication:** The planned semantic component should be evaluated against a faithful task-alignment baseline. Calling an LLM judge “intent alignment” is insufficient differentiation.

### 4. Provenance and information flow are mature comparison dimensions

PAuth binds operand values to symbolic provenance. Fides provides a formal information-flow model with confidentiality and integrity labels. CaMeL separates trusted control flow from untrusted data. The Instruction Hierarchy trains models to prioritize system and user instructions over tool output. The IETF intent-security draft treats provenance and chain-of-custody as explicit security requirements.

**Implication:** IntentGuard's provenance module should reuse precise terminology, define its trust labels and propagation semantics, and avoid claiming provenance tracking as new. A simple source label is weaker than PAuth envelopes or Fides information-flow guarantees.

### 5. Trajectory-aware security is no longer an open field by itself

DRIFT validates deviations from a planned function trajectory. AARM accumulates session context. The IETF draft explicitly analyzes multi-hop intent drift. AgentHazard evaluates harmful behavior produced by sequences of locally plausible actions. AgentDojo, ASB, AgentHarm, and other environments execute multi-step tasks even when their scoring is not specifically a cumulative authorization policy.

**Implication:** IntentGuard must define exactly what its history-dependent constraints detect beyond planned-trajectory deviation. Count, amount, sequence, destination accumulation, and cross-resource disclosure constraints are promising, but each requires comparative cases and ablation evidence.

### 6. Benchmark differentiation is possible but must be narrow

AgentDojo and InjecAgent provide strong prompt-injection environments. ASB and AgentSecBench cover broad attack surfaces. AgentHarm studies malicious multi-step objectives. AgentHazard emphasizes harm emerging from accumulated actions. AuthBench focuses permission-boundary inference.

**Implication:** IntentDriftBench should not be presented as another general agent-security benchmark. Its defensible purpose is to isolate *authorization-boundary* failures, including benign-versus-adversarial pairs that differ only in operation, resource, destination, side effect, or cumulative state.

## Provisional novelty boundary

IntentGuard should **not** claim novelty for any of the following individually:

- task-scoped or natural-language-derived authorization;
- least-privilege tool policy;
- runtime action interception;
- semantic task/action alignment;
- provenance or information-flow tracking;
- trajectory deviation monitoring;
- agent prompt-injection benchmarking.

A potentially defensible contribution, subject to implementation and experiments, is:

> IntentGuard operationalizes task authorization as an explicit, auditable contract spanning operation, resource, destination, side-effect, confirmation, and cumulative constraints; mediates actions with ALLOW, CONFIRM, or BLOCK decisions; and evaluates this contract model using paired, history-dependent authorization-drift cases across heterogeneous tool domains.

This statement is a research hypothesis, not yet a novelty or superiority claim.

## Required direct comparisons

| Priority | Work | Why it is required |
|---|---|---|
| P0 | PAuth | Closest task-scoped authorization and operand-provenance work |
| P0 | Progent | Closest deterministic, task-derived tool-policy enforcement |
| P0 | DRIFT | Closest dynamic trajectory and deviation-validation approach |
| P0 | MiniScope | Closest automatic least-privilege tool authorization framework |
| P0 | Task Shield | Closest semantic task-alignment baseline |
| P1 | Fides | Strong provenance and information-flow comparison |
| P1 | CaMeL | Strong control/data-flow and capability-based defense |
| P1 | AARM | Overlapping runtime boundary and intent-drift specification |
| P1 | IETF intent-security draft | Overlapping terminology, threats, and multi-hop requirements |
| P1 | AgentHazard | Closest benchmark overlap for cumulative multi-step harm |
| P1 | AuthBench | Strong methodology for policy sufficiency versus tightness |

## Design consequences for IntentGuard

1. **Keep the deterministic contract core.** This remains useful and auditable, even though deterministic policy enforcement is not new.
2. **Specify contract-update semantics.** Define who can expand a contract, how confirmation is recorded, and how stale authority expires.
3. **Model cumulative constraints explicitly.** Add typed constraints for counts, values, sequences, aggregate disclosure, and time windows rather than only an action counter.
4. **Separate provenance from semantics.** Record source and trust labels independently of an LLM's judgment about relevance.
5. **Create paired benchmark cases.** For each adversarial case, include a minimally different authorized counterpart to measure whether the defense recognizes permission rather than surface danger.
6. **Report compiler and enforcer errors separately.** A correct validator cannot repair an incorrectly inferred contract.
7. **Use strongest comparable baselines.** At minimum: static allowlist, Task Shield-like semantic alignment, Progent/PAuth-inspired task policy, and the complete IntentGuard configuration.

## Immediate follow-up work

- Read the full text and implementation artifacts for the P0 sources.
- Add methodology columns for code availability, license, dataset availability, and reproducibility status.
- Create a claim-to-evidence table for each proposed paper contribution.
- Revise the manuscript's Related Work and Contributions sections after the P0 review.
- Design the first 20 paired benchmark cases around operation, resource, destination, and cumulative differences.

## Primary source links

The complete row-level source URLs are stored in the matrix. Highest-priority links:

- PAuth: https://arxiv.org/abs/2603.17170
- Progent: https://arxiv.org/abs/2504.11703
- DRIFT: https://proceedings.neurips.cc/paper_files/paper/2025/hash/77f3b26c7907aa27b207df9b9d43f29a-Abstract-Conference.html
- MiniScope: https://arxiv.org/abs/2512.11147
- Task Shield: https://aclanthology.org/2025.acl-long.1435/
- Fides: https://arxiv.org/abs/2505.23643
- CaMeL: https://arxiv.org/abs/2503.18813
- AARM: https://arxiv.org/abs/2602.09433
- IETF intent security: https://datatracker.ietf.org/doc/draft-jiang-intent-security/
- AgentHazard: https://arxiv.org/abs/2604.02947
- AuthBench: https://arxiv.org/abs/2605.14859
