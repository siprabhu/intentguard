# IntentGuard

IntentGuard is a research prototype for task-scoped runtime authorization in
tool-using AI agents. It distinguishes broad technical capability from the
operations, resources, destinations, and side effects authorized for one user
task.

> Status: early research scaffold. This repository contains no experimental
> performance claims.

## Quick start

```powershell
python -m unittest discover -s tests -v
python examples/demo.py
```

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

