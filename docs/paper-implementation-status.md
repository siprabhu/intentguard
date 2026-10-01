# Paper implementation and verification

The six-page manuscript now incorporates this implementation: guarded execution,
28 automated tests, 32 cases, 36 proposals, and refreshed predicate timings.
Its original four-case measurements remain historical artifacts. Current paper
snapshots are retained in `paper/manuscript/runtime_benchmark_results.json` and
`paper/manuscript/runtime_timing_results.json`.

## Implemented and executable

| Paper mechanism | Code | Verification |
|---|---|---|
| Validated immutable contract | `src/intentguard/intent/contract.py` | Rejects missing/unknown fields, invalid identifiers, duplicate entries, invalid limits; copies mutable input collections. |
| Typed proposal and ordered policy | `src/intentguard/guard/authorization.py` | Operation, resource, destination, approval, deny precedence, and count boundaries; malformed proposals and history rejected. |
| Execution mediation | `src/intentguard/guard/runtime.py` | Only ALLOW invokes registered handlers; BLOCK and CONFIRM never execute. |
| Tool operand and side-effect metadata | `ToolSpec` in the runtime | Missing destinations and conflicting metadata rejected; omitted side effects derived from trusted registry. |
| Shared task count | `GuardedRuntime` | Authorization, charging, and execution serialized by a task lock; 40 concurrent calls under a budget of two admit exactly two. |
| Failure accounting | `ExecutionResult` and runtime trace | Failed admitted calls consume budget and retain error metadata; blocked and suspended calls consume none. |
| P01-P15 | `benchmark/deterministic/pairs.json` | 30 synthetic paired members covering operation, resource, destination, confirmation, and count. |
| Reproducible replay | `experiments/run_benchmark.py` | Four local controls, expected/actual decisions, mock effects, input/source hashes, nonzero exit on disagreement. |

The runtime is an in-process trusted-host component. The caller must not give
untrusted planner code access to its internals or direct tool credentials. A
frozen dataclass and Python lock do not isolate a compromised process. The lock
is held across bounded tool execution; this design prioritizes correctness over
parallel network throughput. Runtime records are snapshots, not cryptographic
or durable audit records.

CONFIRM currently suspends execution. There is no approval API or fabricated
authentication layer: authenticated, operand-bound approval remains future work.
The pure predicate still cannot infer a missing destination or side effect from
an operation name; the trusted runtime registry supplies that knowledge.

## Run the evaluation

From the repository root with Python 3.11 or newer:

```powershell
python -m unittest discover -s tests -v
python experiments/run_benchmark.py
python paper/manuscript/measure_draft.py
```

If `python` is not on PATH in this Codex workspace, use:

```powershell
& 'C:/Users/sipra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s tests -v
& 'C:/Users/sipra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' experiments/run_benchmark.py
```

No model, API key, network service, or third-party package is required. The
benchmark validates its executable case model, including equal action/label
lengths and unique IDs. JSON Schema documents describe the interchange shape;
the runner's Python validation additionally enforces cross-field constraints.
The benchmark writes `results/processed/deterministic.json` (ignored by Git).
`generate_deterministic_pairs.py` regenerates the committed cases; the tests
check that these fixtures remain synchronized with their declared design.

Timing runs write `results/processed/current_timing.json`, leaving the original
paper's measurement snapshot intact. They measure the predicate, not the new
execution wrapper. Timing remains machine- and run-dependent.

## Current fixed-proposal results

All 28 automated tests passed on CPython 3.12.14. The existing four-case
diagnostic also retained its 1/4, 2/4, 3/4, and 4/4 control results. Fresh timing
measurements were saved separately from the historical paper snapshot.

The default run includes the 30 paired members and the two original cases:
32 cases, 36 proposals, and 20 authorized proposals.

| Local policy | Fully matching cases | Matching decisions | Unauthorized mock executions | Authorized mock executions |
|---|---:|---:|---:|---:|
| No enforcement | 16/32 | 20/36 | 16 | 20/20 |
| Operation allowlist | 21/32 | 25/36 | 11 | 20/20 |
| Contract without history | 31/32 | 35/36 | 1 | 20/20 |
| IntentGuard | 32/32 | 36/36 | 0 | 20/20 |

IntentGuard suspends two confirmation-required proposals. These proposals are
counted as unauthorized if a control executes them before approval. None of the
four policies reports mock tool errors. All policies share the same trusted
tool-schema checks, so these controls isolate policy differences rather than
tool parsing. The unrestricted and operation-only controls intentionally lack
resource/destination/approval/count restrictions.

These are branch-oriented synthetic checks, not independent evidence of general
attack resistance or a comparison with Task Shield, PAuth, DRIFT, or CaMeL.
Untrusted content in the original injection fixture is metadata; proposals are
fixed, not generated by a model reacting to that content. Cases are labeled by
the fixture author and have not received independent review.

## Remaining research

P16-P20 require aggregate-value, aggregate-disclosure, bound-approval sequence,
provenance, and authenticated multi-agent mechanisms. Other open work includes
model-driven proposals, contract compilation, semantic alignment, durable state,
adaptive attacks, independently reviewed labels, and reproduced published
baselines. The implementation does not silently mark these planned capabilities
as complete. Future changes must update the manuscript's architecture,
experimental section, charts, and limitations together.
