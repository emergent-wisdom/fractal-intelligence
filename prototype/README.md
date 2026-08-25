# Superseded archival artifact — original Gemini 3 Flash run

This directory contains the planning artifact released with the earlier version
of the Fractal Intelligence paper. It is retained for reproducibility, error
provenance, and comparison only. It is **not the current canonical
demonstration**.

The current construction artifact is
[`../experiments/seed-free-sol-fast-v2/`](../experiments/seed-free-sol-fast-v2/).

## Why this artifact was superseded

A retrospective audit found that the original runner initialized an unintended
29-node persistent scaffold before the first problem was processed: six
top-level nodes from the proposed General Problem-Solving Protocol and 23
pre-decomposed children. The runner also protected the top-level seeds. Of 606
saved cross-domain reuse actions, 483 (80%) routed through those initial nodes.
The resulting reuse is therefore dominated by supplied structure and cannot be
used as evidence that the problem stream independently discovered the
hierarchy.

The harness also described child outputs inside Gemini planning calls rather
than executing independent child Solvers, and it logged structural conflicts
without enforcing semantic repair. Its defensible evidential scope is limited
to showing that heterogeneous problems can be routed through and mutate a
supplied persistent graph. It does not demonstrate emergent decomposition,
independent nested execution, learning, solution quality, or compounding.

The replacement construction starts with only `RootSolver` as authored
persistent graph state and requires upward abstraction before downward
composition. It remains a structural probe, not an outcome experiment.

## Reproducing the archived record

- `python3 seed_dependence.py` recomputes and checks the reported historical
  statistics from the committed data.
- `python3 analyze.py` prints the artifact overview.
- From the repository root, run
  `python3 -m http.server 8000 --directory prototype` and open
  `http://127.0.0.1:8000/` to inspect the visualization.

`problems.json` remains at this historical path because the canonical Sol run
records it as the source corpus. The saved data files should be treated as an
archival record rather than edited into a new result.
