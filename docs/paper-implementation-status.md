# Paper implementation and verification

The October 2 reviewer revision includes 41 tests, 44 synthetic cases, and 69
proposals. Current evidence is `trajectory_benchmark_results.json` and
`workflow_timing_results.json` under `paper/manuscript/`. Earlier runtime and
predicate snapshots are historical. The revised PDF is
`output/pdf/IntentGuard_IEEE_6Page_Reviewer_Revision.pdf`; the old PDF was locked
and remains the previous version.

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
| Reproducible replay | `experiments/run_benchmark.py` | Five local controls, expected/actual decisions, mock effects, input/source hashes, nonzero exit on disagreement. |

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
python experiments/measure_runtime.py
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

Whole-runtime timings include initialization, validation, locking, history,
traces, and three mock handlers, with preconstructed contracts/proposals.
There are 2,000 samples per condition, no model or network. At one resource,
full runtime p50/p95/p99 is 17.9/26.6/45.9 microseconds. These are descriptive
single-machine measurements, not agent-loop overhead.

## Current fixed-proposal results

All 41 tests passed. P01-P15, the two original cases, and T01-T06 yield 44 cases,
69 proposals, and 47 authorized proposals.

| Local policy | Fully matching cases | Matching decisions | Unauthorized executions | Authorized executions |
|---|---:|---:|---:|---:|
| No enforcement | 22/44 | 47/69 | 22 | 47/47 |
| Operation allowlist | 27/44 | 52/69 | 17 | 47/47 |
| No history | 37/44 | 62/69 | 7 | 47/47 |
| Count only | 38/44 | 63/69 | 6 | 47/47 |
| IntentGuard | 44/44 | 69/69 | 0 | 47/47 |

The full policy blocks 20 and suspends two proposals. All five policies share
trusted operand checks and report no mock tool errors. Richer history rejects
six violations admitted by count-only enforcement. Implemented trajectory fields
are `operation_limits`, `resource_limits`, `operation_sequence`, and
`max_distinct_destinations`; tests live in `tests/test_trajectory.py`.

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
