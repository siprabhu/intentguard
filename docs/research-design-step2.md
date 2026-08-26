# Step 2 Research Design

Status: initial design for Paper 1
Last updated: 2026-08-25

## Research objective

Determine whether an explicit, provenance-aware, history-dependent task
authorization contract detects authorization drift that simpler controls miss,
without an unacceptable reduction in legitimate task completion.

## Research questions

1. **RQ1 — Decision accuracy:** How accurately does IntentGuard distinguish
   authorized actions from operation, resource, destination, side-effect, and
   confirmation drift?
2. **RQ2 — History dependence:** Does history-aware enforcement detect
   cumulative, sequence, value, and aggregate-disclosure violations missed by
   otherwise equivalent per-action checks?
3. **RQ3 — Component contribution:** What security and utility contribution is
   attributable to deterministic contracts, provenance, semantic alignment,
   and trajectory state?
4. **RQ4 — Generalization and cost:** How do effectiveness, legitimate task
   completion, latency, and confirmation burden change across tool domains,
   agent models, and single- versus multi-agent orchestration?

RQ4's multi-agent component is secondary. The first experiment should establish
the single-agent result before adding delegation and coordination as a separate
factor.

## Claim-to-evidence map

| Candidate claim | Required evidence | Metric or test | Claim status |
|---|---|---|---|
| The contract representation is executable and auditable. | Schema validation, deterministic decisions, reason codes, replayable traces. | Contract validity rate; replay consistency; unit/integration tests. | Partially supported by v0.1. |
| IntentGuard detects authorization-boundary violations. | Labeled paired cases across operation, resource, destination, side effect, and confirmation. | Unauthorized action blocking rate; false-allow rate by category. | Not yet tested at scale. |
| History-aware policy adds protection beyond per-call checks. | Locally allowed actions whose trajectory violates count, value, sequence, destination, or disclosure constraints. | Incremental detection over no-history ablation; paired significance test. | One unit test only. |
| Provenance prevents untrusted content from expanding authority. | Same action/operand with trusted and untrusted derivations; provenance ablation. | Attack success and benign completion with/without provenance. | Planned, not implemented. |
| The approach preserves utility. | Benign counterparts for every adversarial case and complete legitimate workflows. | Benign completion; false-block and confirmation rates. | Not yet measured. |
| The design generalizes beyond one model or domain. | Fixed benchmark across model families and email, files, finance, and records. | Per-model/domain effects and confidence intervals. | Planned later experiment. |
| Shared enforcement prevents multi-agent authority laundering. | Equivalent single-agent and delegated trajectories, including split cumulative violations. | Detection by topology; delegation-policy false-allow rate. | Extension claim only. |

Claims must be weakened or removed if their evidence is absent.

## Experimental factors

### Defense conditions

- **B0:** no runtime enforcement;
- **B1:** static tool allowlist;
- **B2:** prompt-only security instruction;
- **B3:** semantic task-alignment baseline;
- **B4:** per-action deterministic contract without history or provenance;
- **P:** complete IntentGuard configuration.

### Ablations

- remove resource/destination binding;
- remove provenance enforcement;
- remove trajectory history;
- remove semantic alignment;
- replace explicit confirmation with binary allow/block;
- replace the compiled contract with broad static permission.

### Outcomes

- unauthorized action execution rate;
- benign task completion rate;
- false allow, false block, and confirmation rates;
- detection by drift category;
- end-to-end and enforcement-only latency;
- token/model cost where applicable;
- contract-compilation error versus enforcement error;
- inter-rater agreement for benchmark labels.

## Evaluation discipline

- Use paired cases that differ in one authorization dimension where possible.
- Separate contract-compilation evaluation from enforcement evaluation.
- Pin prompts, schemas, model versions, temperatures, and benchmark commit.
- Retain machine-readable traces and report failed or excluded runs.
- Predefine ambiguity and exclusion rules before the main experiment.
- Report negative results and confidence intervals, not only point estimates.
- Do not treat current unit tests as comparative security evidence.

## Step 2 completion criteria

Step 2 is complete when the architecture boundary is agreed, the 20 initial
pairs have schema-valid definitions, claim-to-evidence links are recorded, and
all current and new deterministic behavior is covered by automated tests.
