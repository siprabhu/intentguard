# IntentGuard Architecture and Scope

Status: deterministic execution baseline implemented; extended architecture planned
Last updated: 2026-09-30

The current implementation adds a trusted tool registry, guarded in-memory
execution, serialized task counting, input validation, and a 32-case replay
runner. See `paper-implementation-status.md` for the current evidence. The
provenance, authenticated-approval, tamper-evident logging, and multi-agent
components described below remain architectural targets, not completed features.

## Architectural position

IntentGuard is a policy-enforcement boundary for tool-using AI systems. It is
not an agent framework and it is not another autonomous agent. One agent, an
agent team, or a deterministic workflow may propose an action, but the
proposer cannot grant itself execution authority. Every consequential action
must pass through the same trusted enforcement path before a bounded tool is
invoked.

The current implementation is a single-agent deterministic baseline. The
research architecture is multi-agent-compatible, but multi-agent delegation,
identity, and shared trajectory enforcement are planned work rather than
implemented features.

## Trust boundary

```text
Untrusted / fallible plane                  Trusted enforcement plane

User task
   |
Contract compiler (AI-assisted) --- proposed contract ---> Contract validator
   |                                                       + versioned store
Planner or agent team -------- proposed action event ----> Policy enforcer
   ^                                                       |  deterministic rules
   |                                                       |  provenance policy
Tool output / retrieved data <----- sanitized result -----|  trajectory policy
                                                           |  approval gateway
                                                           v
                                                     Bounded tool adapter
                                                           |
                                                    External system
```

LLM-generated plans, semantic judgments, retrieved content, tool outputs, and
messages from other agents are evidence, not authority. The deterministic
enforcer, validated contract, authenticated approval, trajectory state, and
tool adapter form the initial trusted computing base.

## Runtime flow

1. The user states an objective and any explicit constraints.
2. A contract compiler proposes a normalized Intent Authorization Contract.
3. Deterministic validation rejects malformed or internally inconsistent
   contracts. High-impact inferred permissions may require user confirmation.
4. An agent or workflow proposes a typed action event.
5. IntentGuard evaluates operation, resource, destination, side effect,
   provenance, delegation, and accumulated trajectory state.
6. The guard returns `ALLOW`, `CONFIRM`, or `BLOCK` with a reason code.
7. Only an allowed action reaches the bounded tool adapter.
8. The decision, action, result metadata, provenance, and state transition are
   appended to a tamper-evident audit trace.
9. A confirmation creates a narrow, authenticated contract update or one-time
   approval; it does not silently broaden the agent's authority.

## AI scope

AI may propose a contract from natural language, plan candidate tool calls,
extract structured operands, estimate semantic alignment for underspecified
low-risk cases, generate benchmark candidates, and explain decisions.

AI output is never the final authority for a hard constraint. An LLM cannot
override a prohibited operation, add a destination, rewrite history, approve
its own request, or erase provenance. Semantic scoring must be independently
measured and can influence policy only where the contract permits it.

## Agent scope

### Initial single-agent study

The first controlled study uses one planner/agent because it isolates the
effect of authorization. The agent receives a task and tool schemas, observes
synthetic tool output, and proposes actions. IntentGuard mediates them.

### Multi-agent extension

A later study may use a coordinator and specialist agents. Every action event
must then include authenticated principal and role identifiers, parent and
delegation identifiers, contract ID/version, requested operands, provenance,
trajectory ID, and a prior-state digest.

Delegation follows attenuation: a child receives a subset of the parent's
authority but cannot expand it. Cross-agent actions share one trajectory ledger
so splitting a prohibited outcome among agents does not bypass cumulative
limits. Inter-agent messages remain untrusted unless origin and delegation are
verified.

Multi-agent orchestration is therefore in experimental scope. Autonomous trust
negotiation, emergent organizations, open-ended agent discovery, and new
cryptographic identity protocols are outside the initial paper.

## Technical implementation scope

### Implemented deterministic baseline

- immutable Python `IntentContract` and typed `ProposedAction`;
- deterministic operation, resource, destination, confirmation, and action
  count checks;
- `ALLOW`, `CONFIRM`, and `BLOCK` decisions with reasons;
- safe in-memory tool environment;
- versioned JSON benchmark schema and initial cases;
- 28 unit, runtime, validation, and benchmark regression tests;
- trusted tool metadata, suspended confirmation, and blocked-execution checks;
- serialized task counting including concurrent calls and tool failures;
- P01-P15 synthetic pairs plus the two original cases;
- reproducible four-policy runner with machine-readable traces and source hashes.

### Step 2 target

- versioned contract schema with identifiers and update semantics;
- typed action and decision events;
- trajectory ledger with count, value, sequence, destination, and aggregate
  disclosure constraints;
- explicit instruction and operand provenance labels;
- authenticated confirmation records;
- benchmark runner and machine-readable result traces;
- paired benign/adversarial benchmark cases;
- ablation switches for deterministic, provenance, semantic, and history
  components.

### Later implementation

- model-backed contract compiler and semantic-alignment component;
- adapters for multiple model providers and agent frameworks;
- coordinator/specialist multi-agent experiments;
- persistent policy and audit stores;
- integration with conventional OAuth, RBAC, or ABAC enforcement;
- reproducible research baselines where licensing permits.

## Non-goals for the initial paper

- replacing authentication, OAuth, RBAC, ABAC, or operating-system security;
- proving that an LLM always infers the correct user intent;
- defending a compromised guard runtime or malicious tool adapter;
- preventing harm requested by an already-authorized malicious user;
- production deployment, performance, or compliance certification;
- claiming task-scoped authorization, provenance, or interception as novel.

## Research architecture principle

Keep the trusted center small and the integration edge broad. Agents, models,
and orchestration may vary; the same explicit contract, decision interface, and
history-aware semantics must remain testable across them.
