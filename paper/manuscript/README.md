# Manuscript workspace

## Current IEEE-style revision

The September 30, 2026 revision follows the supplied six-page, two-column
manuscript reference. A target conference has not yet been selected, so this is
a review draft rather than a certified venue submission.

- `IntentGuard_IEEE_Draft.md`: revised prose and figure insertion markers.
- `IntentGuard_IEEE_Draft.tex`: standalone IEEEtran source with inline TikZ and
  PGFPlots figures; no external image or bibliography files are required.
- `../../output/pdf/IntentGuard_IEEE_6Page_Draft.pdf`: six-page review PDF.
- `measure_draft.py`: four-case diagnostic replay and local timing procedure.
- `runtime_benchmark_results.json`: 32-case, 36-proposal replay with full traces
  and source/input hashes used in this revision.
- `runtime_timing_results.json`: current predicate timing snapshot used in plots.
- `sample_contract.json`: executable worked contract shown in Listing 1.
- `draft_measurements.json`: historical four-case measurement snapshot, no longer
  used by the current manuscript builder.
- `build_ieee_draft.py`: generates the review PDF and LaTeX source from the
  revised prose and retained measurements.

The six-page PDF and its prose now describe the guarded runtime, 28 passing
tests, 15 benchmark pairs plus two original fixtures, and current predicate
timings. The worked contract, execution algorithm, figures, abstract, results,
and limitations are synchronized with that implementation. See
`../../docs/paper-implementation-status.md` for the claim-to-code mapping.

Run `python paper/manuscript/build_ieee_draft.py` from the repository root using
a runtime with ReportLab installed. Re-running `measure_draft.py` writes fresh
measurements to `results/processed/current_timing.json`. The original
`draft_measurements.json` is retained as historical evidence. To revise the
paper's measurements, copy reviewed run outputs into the two `runtime_*` snapshot
files and update numerical prose together. The builder checks retained source
hashes before generating the PDF and LaTeX, preventing stale snapshots from
silently being used with changed implementation code.
The original Markdown and Word drafts remain available as historical versions.

## Verification and limitations

All 28 automated tests passed during this revision. All six rendered PDF
pages were visually inspected. The PDF contains an architecture diagram,
decision flowchart, diagnostic comparison, resource-set scaling curve, and
timing-stability plot. The last plot is explicitly not algorithmic convergence.
The benchmarks are synthetic mock executions; timing measures only the
predicate. Neither establishes general agent security effectiveness.

The review PDF is generated with ReportLab and is not an export of the LaTeX
source. The built-in LaTeX editor was opened, but compilation failed before
processing the document with `Unable to find standard directories for platform`.
LaTeX compilation, pagination, and final venue compliance remain unverified.
The LaTeX source uses IEEEtran's natural pagination; it may differ from the
review PDF's six explicitly balanced pages.
