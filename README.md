# IntentGuard

IntentGuard is a research prototype for task-scoped runtime authorization in
tool-using AI agents. It distinguishes broad technical capability from the
operations, resources, destinations, and side effects authorized for one user
task.

> Status: executable deterministic research prototype. Local mock benchmarks
> are available; no model-driven or production security claims are established.

## Quick start

```powershell
python -m unittest discover -s tests -v
python experiments/run_benchmark.py
python examples/demo.py
```

Python 3.11+ is sufficient for the tests and benchmark; no API key, model, or
third-party package is required. The benchmark exits nonzero if IntentGuard
disagrees with any case label or a mock tool fails. Traces and source/input hashes
are written to `results/processed/deterministic.json`.

The suite includes deterministic decision tests, malformed-input tests,
execution-boundary tests, concurrency/count enforcement, and runner regression
tests. The benchmark contains P01-P15 (30 paired members) plus the two original
cases, totaling 32 cases and 36 proposed actions. Labels have not been
independently reviewed. Tool execution is simulated entirely in memory.

See [the paper implementation report](docs/paper-implementation-status.md) for
the claim-to-code mapping, measured results, commands, and remaining work.

## Initial research questions

1. Can task-scoped intent contracts reduce unauthorized tool actions without
   materially reducing legitimate task completion?
2. Does trajectory-aware enforcement detect multi-step violations missed by
   static or per-call authorization?
3. What security/utility tradeoff results from deterministic, semantic, and
   hybrid authorization decisions?
4. How well does the approach generalize across models and tool domains?

## Repository map

- `src/intentguard/`: runtime and contract implementation
- `benchmark/`: versioned benign and adversarial cases
- `experiments/`: configurations and runners
- `results/`: generated outputs (raw results are ignored by Git)
- `docs/`: architecture, threat model, and research protocol
- `paper/`: manuscript sources and generated figures/tables

## Research integrity

Use synthetic or appropriately licensed public data only. Do not add employer,
customer, or other confidential material. Verify novelty and citations before
making publication claims. See `docs/data-governance.md`.
