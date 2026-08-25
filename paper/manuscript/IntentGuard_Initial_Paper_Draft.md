# IntentGuard: Task-Scoped Runtime Authorization for Preventing Authorization Drift in Tool-Using AI Agents

**Prabhu Sivapunniyam**  
Independent Researcher  
Draft v0.2 — August 2026

## Abstract

Tool-using large language model (LLM) agents translate natural-language objectives into actions over files, messages, records, financial services, and other external systems. Conventional access controls determine whether an agent possesses a capability, but they do not necessarily establish whether a user authorized a particular invocation for the current task. This gap permits *authorization drift*: a workflow can move beyond the operations, resources, destinations, or cumulative effects authorized by the user's request while remaining within the agent's broad technical permissions. We present IntentGuard, a task-scoped runtime enforcement architecture that represents user authority as an explicit Intent Authorization Contract and mediates consequential tool calls before execution. The current research prototype implements deterministic checks for operation, resource, destination, confirmation, and cumulative-action constraints, together with a safe in-memory tool environment and versioned benign and adversarial cases. Four implementation tests confirm the expected behavior for an in-scope read, a prohibited send, resource drift, and a cumulative-limit violation. These tests establish implementation correctness for the covered cases; they are not evidence of comparative security effectiveness. We define a threat model, an authorization-drift taxonomy, and a reproducible evaluation plan for extending the prototype with provenance, trajectory, and semantic alignment and comparing it with unprotected, allowlist, prompt-only, and task-alignment baselines. The paper's present contribution is therefore a precise problem formulation, a minimal enforceable design, and a falsifiable experimental protocol rather than a claim of empirical superiority.

**Keywords:** AI agents; authorization; prompt injection; tool use; least privilege; runtime enforcement; provenance; trajectory security

## 1. Introduction

LLM-based agents increasingly act rather than merely respond. An agent can search mail, read a document, update a database, send a message, or invoke a financial operation. Tool access turns an unsafe model output into a possible external side effect, making authorization a central systems concern.

Existing identity and access mechanisms remain necessary, but their grants are often broader than the authority implied by one user request. An agent may possess permission to call `send_email` because that capability is useful across many tasks. A user who asks the agent to locate an invoice and report its amount, however, has not thereby authorized disclosure of that invoice to a third party. If retrieved content contains the instruction “send this invoice to external@example.com,” a capability check can succeed even though the proposed action exceeds the task.

Prompt injection research has established that untrusted tool output can redirect agent behavior. AgentDojo provides an extensible environment with realistic tasks and security test cases for tool-using agents [1], while InjecAgent focuses on indirect prompt injection in tool-integrated agents [2]. Task Shield reframes defense around whether directives and tool calls serve the user's task [3]. More recent work directly addresses authorization: PAuth derives task-scoped operation specifications and binds operands to provenance [4], and an IETF Internet-Draft analyzes constraint bypass, invocation validation, multi-hop intent drift, and chain-of-custody requirements [5]. DRIFT combines dynamically generated rules, plan validation, and injection isolation [6]. These developments make a broad novelty claim for “task-aware agent security” untenable.

This paper focuses on a narrower, operational question: can a user task be represented as an explicit, inspectable authorization contract and enforced at every consequential action boundary, including constraints that depend on the workflow history? We call divergence from that boundary *authorization drift*.

IntentGuard places a policy-enforcement point between agent reasoning and tool execution. The user request is compiled into an Intent Authorization Contract. A proposed action is evaluated against explicit operation, resource, destination, side-effect, and cumulative constraints. The intended full system also incorporates instruction provenance, prior actions, and semantic task alignment. The enforcement result is `ALLOW`, `CONFIRM`, or `BLOCK`; the agent proposes actions but does not grant itself execution authority.

The current repository is an early research scaffold. It contains a deterministic contract model, validator, safe mock environment, two versioned benchmark cases, a pilot experiment configuration, and four unit tests. Accordingly, this draft makes no attack-success, utility, latency, novelty-priority, or state-of-the-art claim. It contributes a research framing and an executable baseline from which such claims can be tested.

The paper addresses four research questions:

1. **RQ1:** Can task-scoped intent contracts reduce unauthorized tool actions without materially degrading benign task completion?
2. **RQ2:** Does trajectory-aware enforcement detect history-dependent authorization violations missed by static or per-call checks?
3. **RQ3:** What security–utility tradeoff results from deterministic, semantic, and hybrid decision strategies?
4. **RQ4:** How well does the approach generalize across agent models and tool domains?

## 2. Background and Related Work

### 2.1 Capability authorization and task authority

Authentication and conventional authorization answer whether a principal may access a resource or invoke an operation. OAuth scopes, role-based access control, and attribute-based access control are important enforcement layers, but an agent acting under delegated credentials may remain overprivileged relative to a specific natural-language request. IntentGuard does not replace these controls. It narrows their effective use by adding a task-specific policy at the point of action.

PAuth is the closest authorization-oriented work identified in the current review. It proposes Precise Task-Scoped Implicit Authorization, natural-language slices that describe expected service calls, and provenance-carrying envelopes that bind concrete operands to their derivation [4]. IntentGuard must therefore be evaluated as a distinct design choice rather than presented as the origin of task-scoped authorization. Its candidate differentiation is an explicit contract exposed as a runtime policy object, an `ALLOW`/`CONFIRM`/`BLOCK` interface, and benchmark emphasis on authorization expansion across operations, resources, destinations, and cumulative history. Whether this combination provides a meaningful advantage is an empirical question.

### 2.2 Prompt injection and task alignment

AgentDojo demonstrated a dynamic evaluation environment for prompt-injection attacks and defenses, populated with 97 tasks and 629 security test cases [1]. InjecAgent similarly benchmarks indirect prompt injections in tool-integrated agents [2]. These benchmarks show why untrusted content must be treated as data rather than as authority.

Task Shield checks whether directives and tool calls contribute to the user's stated objective [3]. Its task-alignment perspective overlaps substantially with the semantic component planned for IntentGuard. IntentGuard's deterministic contract boundary is intended to complement, not relabel, task alignment: semantic relevance alone may not encode hard recipient, amount, count, or side-effect constraints.

DRIFT constructs a minimal function trajectory and parameter checklist, validates deviations, and isolates conflicting injected instructions [6]. It is a particularly important comparison for the proposed trajectory-aware phase. The mature study must specify whether IntentGuard detects cases that DRIFT or Task Shield do not, and must report negative findings if it does not.

### 2.3 Intent security and provenance

The IETF intent-security draft describes multi-hop processing risks including directive tampering, privilege escalation, constraint bypass, and intent drift, and it emphasizes provenance binding, invocation validation, monitoring, and policy-driven responses [5]. It is an evolving Internet-Draft rather than an adopted standard. IntentGuard provides a prototype-level instantiation of several related enforcement ideas in a tool-using agent setting, but it does not claim protocol standardization or cryptographic chain-of-custody.

## 3. Problem Definition

### 3.1 Authorization drift

Let a user task produce an authorization contract \(C\), a sequence of proposed actions \(A = (a_1, \ldots, a_n)\), and a trajectory state \(H_i\) summarizing actions before \(a_i\). Authorization drift occurs when an action or cumulative trajectory violates a constraint in \(C\), absent a valid contract update or explicit user approval.

The definition is intentionally enforcement-oriented. A response can be irrelevant without being an authorization violation, and an action can appear useful while violating a hard boundary. Conversely, discovering an unenumerated resource may be legitimate but ambiguous, suggesting `CONFIRM` rather than automatic rejection in a mature policy.

### 3.2 Taxonomy

- **Action drift:** a read or comparison task expands into send, modify, delete, purchase, or transfer.
- **Resource drift:** the workflow accesses a resource outside the authorized set.
- **Destination drift:** data or effects are directed to an unauthorized recipient or endpoint.
- **Provenance drift:** instructions from retrieved or tool-produced content begin controlling privileged actions.
- **Trajectory drift:** locally plausible steps combine into an unauthorized final effect.
- **Cumulative or temporal drift:** action count, value, sequence, or accumulated exposure exceeds a task constraint.

### 3.3 Security objective

For each proposed consequential action, the enforcement layer should prevent execution when the action is clearly outside the active task authorization, request user confirmation when policy requires approval or intent is materially ambiguous, and permit authorized actions with acceptable utility and overhead. The objective is not perfect model safety; it is mediation of effects.

## 4. Threat Model and Assumptions

The system includes a user, an LLM agent or planner, the IntentGuard runtime, and bounded tools. The user provides a legitimate task. Tools can return untrusted content such as documents, messages, records, or web-like text. An adversary may control some of this content or may supply direct malicious instructions. Model errors may also produce the same outward behavior as an attack.

The adversary attempts to induce unauthorized operations, access unrelated resources, substitute destinations, disclose data, exceed quantitative limits, or assemble a prohibited effect through multiple steps. The adversary is not assumed to compromise the IntentGuard implementation, the host operating system, or the conventional identity provider. Denial of service, compromised tool implementations, and malicious users who are already authorized for the requested action are outside the initial scope.

The prototype uses synthetic cases and in-memory tools. It does not connect to employer, customer, or production systems. This choice improves safety and reproducibility but limits external validity.

## 5. IntentGuard Design

### 5.1 Enforcement architecture

The design separates planning authority from execution authority:

1. The user supplies a task.
2. An intent compiler produces a structured contract.
3. The agent plans and proposes a tool action.
4. IntentGuard evaluates the action against the contract and trajectory.
5. The runtime returns `ALLOW`, `CONFIRM`, or `BLOCK` with a reason.
6. Only an allowed action reaches the tool; confirmation requires a user-mediated contract update or approval.
7. The system records the proposal, evidence, decision, and resulting state.

In the current prototype, contracts are provided as structured data rather than generated by an LLM. This isolates enforcement behavior from contract-compilation error and creates defensible ground truth for the first tests.

### 5.2 Intent Authorization Contract

The implemented Python `IntentContract` is immutable and includes the following fields:

| Field | Meaning | Current status |
|---|---|---|
| `objective` | Human-readable task objective | Stored, not yet semantically evaluated |
| `allowed_operations` | Operations authorized for the task | Enforced |
| `allowed_resources` | Resources authorized for the task | Enforced |
| `allowed_destinations` | Permitted recipients or endpoints | Enforced when a destination is proposed |
| `prohibited_operations` | Explicitly forbidden operations | Enforced before allowlist checks |
| `confirmation_required` | Side effects requiring approval | Enforced |
| `max_action_count` | Maximum cumulative actions | Enforced using prior action count |

An illustrative contract for a read-only invoice task is:

```json
{
  "objective": "Retrieve the amount from invoice 123",
  "allowed_operations": ["search", "read"],
  "allowed_resources": ["invoice_123"],
  "allowed_destinations": [],
  "prohibited_operations": ["send", "delete"],
  "confirmation_required": ["external_communication"],
  "max_action_count": 2
}
```

### 5.3 Deterministic decision procedure

The current validator applies ordered fail-closed checks. It blocks explicitly prohibited operations; operations outside the allowed set; resources outside the allowed set; and specified destinations outside the allowed set. It then blocks a proposed action if the prior action count has reached the contract limit. A side effect listed in `confirmation_required` yields `CONFIRM`; otherwise, the action yields `ALLOW`.

The order is security-relevant. An explicitly prohibited operation is blocked even if another contract field is malformed or overly broad. Destination validation occurs only when the action specifies a destination, which exposes a future requirement: tool schemas must identify destination-bearing parameters reliably.

### 5.4 Planned provenance, trajectory, and semantic layers

The repository does not yet implement semantic alignment or trusted/untrusted provenance labels. Its trajectory support is limited to a cumulative count supplied to the validator. The planned design will represent each action as an event containing tool, operation, operands, origin, relevant instruction sources, decision, and state transition. Deterministic constraints will remain hard boundaries. A semantic component may resolve underspecified but low-risk actions, while provenance and trajectory features provide context. These additions require independent ablation because a more complex hybrid may increase false positives, latency, and attack surface.

## 6. Prototype Implementation and Verification

The prototype is implemented in Python 3.11 or later. `IntentContract` is a frozen dataclass; `ProposedAction` represents operation, resource, optional destination, and optional side effect; and `evaluate_action` returns a typed decision and human-readable reason. `MockToolEnvironment` records an in-memory trace and supports safe read-oriented operations. Benchmark cases are JSON documents validated against a versioned schema.

The repository currently contains two benchmark cases: one benign invoice retrieval with two allowed actions, and one indirect-injection case in which retrieved content requests external disclosure and the expected decision is `BLOCK`. The pilot configuration names four defense conditions but leaves the model unspecified because no model-driven experiment has been run.

Four unit tests execute successfully:

| Test | Proposed condition | Expected and observed decision |
|---|---|---|
| In-scope read | `read` on `invoice_123` | `ALLOW` |
| Prohibited send | `send` to an external destination | `BLOCK` |
| Resource drift | `read` on `payroll` | `BLOCK` |
| Cumulative violation | third action when maximum is two | `BLOCK` |

The example program also returns `ALLOW` for an authorized read and `BLOCK` for an explicitly prohibited send. These are software verification results for hand-authored cases. They do not estimate attack success rate, benign utility, generalization, or robustness against adaptive attacks.

## 7. IntentDriftBench and Evaluation Protocol

### 7.1 Benchmark construction

IntentDriftBench will consist exclusively of synthetic or appropriately licensed public data. Each case will record a user task, structured contract, trusted and untrusted context, proposed or generated action sequence, expected authorization decisions, prohibited outcome, and labeling rationale. The pilot should begin with approximately 50–100 carefully reviewed cases before expansion.

Planned categories are benign workflows, direct scope violations, indirect prompt injection, tool-output poisoning, resource and destination substitution, data exfiltration, multi-step drift, and cumulative or temporal violations. Initial domains are email, files, finance, and enterprise records. Labels should be reviewed independently, with ambiguity recorded rather than forced into a binary ground truth.

### 7.2 Baselines

The study will compare: (B0) no enforcement; (B1) a static tool allowlist; (B2) prompt-only security instructions; (B3) a faithful task-alignment or task-scoped authorization baseline, subject to implementation availability and licensing; and (P) IntentGuard. Task Shield, PAuth, and DRIFT are candidate comparison points, but the final baseline set must reflect what can be reproduced faithfully.

### 7.3 Metrics

Primary security metrics are attack success rate, authorization violation rate, detection precision, detection recall, and F1. Utility metrics include benign task completion, false-positive rate, and confirmation rate. Systems metrics include added wall-clock latency and token or monetary overhead. Results should include confidence intervals or uncertainty estimates appropriate to the experimental design rather than only point estimates.

### 7.4 Ablations and error analysis

The full design will be compared with variants that remove deterministic constraints, semantic alignment, provenance, trajectory history, and resource/destination binding. Error analysis will distinguish enforcement errors from contract-compilation errors, ambiguous user intent, incomplete tool schemas, semantic-judge errors, and adaptive attacks. The central trajectory hypothesis is supported only if history-aware enforcement detects violations that comparable per-call checks miss without an unacceptable utility cost.

### 7.5 Reproducibility

Experiments will pin model and version, prompts, tool schemas, temperature, random seeds where supported, benchmark version, and execution date. Raw traces will be retained. Exclusion criteria, failed runs, and negative findings will be reported. A clean-room reproduction should be able to install the package, validate the benchmark schema, run the pilot, and regenerate tables and figures.

## 8. Discussion

IntentGuard treats task authorization as a runtime artifact rather than an informal prompt instruction. This provides inspectability and a natural audit record, and it makes hard constraints testable without relying on an LLM to reinterpret them at every step. It may also permit conventional policy engines to participate in agent workflows.

The approach introduces new risks. A contract can be incomplete or incorrectly compiled. Strict resource enumeration can block legitimate discovery, while permissive wildcards can restore overprivilege. Tool arguments may conceal destinations or side effects. A semantic judge can be attacked or may disagree with the user. Confirmation can improve safety but create fatigue. Trajectory state can grow, leak sensitive context, or be summarized incorrectly.

The design therefore favors a small deterministic core, explicit reasons, versioned policy, and measurement of both security and utility. A mature implementation should authenticate contract updates, separate instruction provenance from content semantics, minimize retained sensitive state, and make approval decisions unambiguous to the user.

## 9. Limitations

This draft reports only a research scaffold and four deterministic unit tests. The benchmark is too small for statistical inference. No LLM agent, semantic judge, provenance module, full trajectory engine, multi-domain tool suite, or comparative baseline is implemented. The cases are synthetic, the current action model is simplified, and the validator assumes correctly normalized operation, resource, destination, and side-effect fields. The literature review is incomplete and fast-moving; the candidate novelty boundary may narrow further. No claim in this draft should be used as evidence of deployment effectiveness, independent adoption, or peer-reviewed impact.

## 10. Ethical, Security, and Research-Integrity Considerations

The project should use independently written code and synthetic or appropriately licensed data. It should exclude employer and customer source code, prompts, incidents, architecture, and confidential records unless formally authorized. Benchmark release should avoid providing operational abuse instructions beyond what is necessary for reproducible defensive research. Manuscript claims must follow measured evidence, citations must be verified, and relevant venue policies on generative-AI assistance should be followed. Publication and open-source review obligations should be completed before release where applicable.

## 11. Conclusion

Broad agent capability does not imply authority for every action within a particular task. IntentGuard operationalizes this distinction through a task-scoped contract and a runtime decision boundary. The present prototype demonstrates deterministic enforcement for operations, resources, destinations, confirmation requirements, and cumulative action counts in a small set of verified cases. The next research phase must determine whether provenance- and trajectory-aware enforcement provides measurable protection beyond existing task-alignment and task-scoped authorization approaches while preserving benign utility. This initial manuscript establishes the definitions, system boundary, implementation baseline, and evaluation protocol required to answer that question without overstating the available evidence.

## References

[1] E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer, and F. Tramèr, “AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents,” *Advances in Neural Information Processing Systems*, vol. 37, 2024. doi: 10.52202/079017-2636.

[2] Z. Zhan et al., “InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents,” *Findings of the Association for Computational Linguistics: ACL 2024*, 2024. https://aclanthology.org/2024.findings-acl.624/

[3] F. Jia, T. Wu, X. Qin, and A. Squicciarini, “The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents,” *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics*, pp. 29680–29697, 2025. doi: 10.18653/v1/2025.acl-long.1435.

[4] R. K. Sharma, L. Jiang, Z. Lin, and S. Chen, “PAuth — Precise Task-Scoped Authorization For Agents,” arXiv:2603.17170, 2026. https://arxiv.org/abs/2603.17170

[5] Y. Jiang, L. Li, Y. Song, and F. Liu, “Security Considerations for Intent-Based Requests in Agentic Systems,” IETF Internet-Draft draft-jiang-intent-security-02, June 2026. https://datatracker.ietf.org/doc/draft-jiang-intent-security/

[6] H. Li, X. Liu, C. Chiu, D. Li, N. Zhang, and C. Xiao, “DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents,” *Advances in Neural Information Processing Systems*, vol. 38, 2025. doi: 10.52202/085713-2791.

## Draft-status note

This is an initial, pre-experimental manuscript. Before submission, complete the systematic literature review, expand and independently review the benchmark, implement the planned modules and baselines, run controlled experiments, replace the prototype-only abstract and conclusion with evidence-based findings, add statistical results and figures, select a venue, and apply that venue's official template and disclosure requirements.
