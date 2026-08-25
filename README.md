# Fractal Intelligence: Conceptual Decomposition as Problem-Solving Infrastructure

[![Paper](https://img.shields.io/badge/Paper-PDF-red)](fractal-intelligence.pdf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19462645.svg)](https://doi.org/10.5281/zenodo.19462645)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

This paper introduces **fractal intelligence** as a theoretical category: cumulative intelligence that recursively restructures problems into conceptual parts, preserves useful reasoning structures beyond the tasks that produced them, and reuses or revises those structures across problems, domains, and scales.

The paper then develops one possible realization. In the **Solver architecture**, a concrete problem first climbs through adjacent conceptual abstractions to `RootSolver`, retraces that route, and asks what the specific capability is *made of*, not only how a human would solve it. Specialization edges locate kinds; composition edges bind differentiated contributions. Each concept-defined Solver exposes a uniform five-surface contract, allowing specialists to compose recursively while remaining isolated behind typed boundaries. Recurring structures can become content-addressed infrastructure (**reasoning highways**) so reasoning accumulates rather than being rebuilt each time.

The paper argues and probes this rather than proves it. Companion experiments provide preliminary evidence about isolation and reframing; the canonical mandatory-abstraction construction demonstrates model-authored rooted graph construction and cross-domain structural reuse. A superseded seeded artifact is retained only for reproducibility and error provenance. The decisive tests are whether fresh conceptual carves outperform equally persistent conventional solving at matched compute and memory, whether independently derived carves reveal recurring invariants or complementary utility, and whether reuse improves subsequent problem solving. Should those tests succeed, retained solution structures could form an *internet of reasoning*.

**Paper:** [`fractal-intelligence.pdf`](fractal-intelligence.pdf)

## Key Ideas

- **Concepts over tasks** — changing the carve can expose candidate mechanisms an inherited task framing leaves unseen; persistent concepts may also transfer farther across domains
- **Upward first, then downward** — every concrete problem must locate itself through adjacent abstractions to the root before the exact route is traversed and the specific capability is decomposed
- **The Solver Contract** — a five-surface interface (Manifest, Execute, Consult, Verify, Feedback) composing heterogeneous, mutually untrusting reasoners
- **Cognitive isolation** — competing modes (generation, verification, critique, empathy) behind typed boundaries so they cannot suppress each other; rejection forces structural reframing, not token-level compromise
- **The Theory of Depth** — a marginal-value rule deciding, at every node, whether decomposing deeper is worth its cost
- **Reasoning highways** — recurring structures can be promoted into content-addressed Sema specifications and reused across unrelated problems
- **Three decisive tests** — matched-compute-and-memory performance; invariant convergence or complementary utility among independently derived carves; and improvement of subsequent problem solving through reuse

## Repository Contents

- [`fractal-intelligence.tex`](fractal-intelligence.tex) / [`fractal-intelligence.pdf`](fractal-intelligence.pdf) — the paper
- [`experiments/seed-free-sol-fast-v2/`](experiments/seed-free-sol-fast-v2/) — the **canonical current construction artifact**: a 100-problem mandatory-abstraction run with public prompt, controller, schema, audit, method-change record, structured outputs, graph state, and viewer; no private reasoning traces
- [`prototype/`](prototype/) — the **superseded Gemini archive**, retained for reproducibility and error provenance; its unintended 29-node startup scaffold made the reported reuse seed-dominated
- [`SEMANTIC_PRESERVATION.md`](SEMANTIC_PRESERVATION.md) — the concept-level regression checklist for future consolidation and claim-calibration passes
- [`references.bib`](references.bib) — bibliography

The companion [Fractal Intelligence Protocol](https://github.com/emergent-wisdom/fractal-intelligence-protocol) v0.2.0 is an experimental reference implementation of selected Solver-architecture mechanisms, including typed delegation, deterministic acceptance gates, the four-test procedure, reviewed mandatory-abstraction topology artifacts, and a matched-budget evaluation harness. It is an executable research substrate, not an outcome study.

## Reproducing

- **Paper:** `./compile.sh` (pdflatex + bibtex).
- **Current mandatory-abstraction artifact:** `experiments/seed-free-sol-fast-v2/AUDIT.md` independently recomputes its structural results and records semantic failures; `METHOD_CHANGES.md` records the adaptive mid-run changes. Serve `experiments/seed-free-sol-fast-v2/` and open `viewer.html?state=runs/sol-mandatory-abstraction-100-2026-08-25/state.json` to inspect observed graph growth. The historically stable corpus remains at `prototype/problems.json`, which is also the path recorded in the immutable run metadata.
- **Archived Gemini numbers:** `python3 prototype/seed_dependence.py` re-derives the superseded artifact's figures from committed data and checks each one (59/59 passing); `python3 prototype/analyze.py` prints the overview. Both scripts use only the Python standard library and do not modify the data.
- **Archived Gemini visualization:** `python3 -m http.server 8000 --directory prototype`, then open `http://127.0.0.1:8000/`. The page reconstructs observed growth of the final surviving topology. Its pinned graph and chart libraries load from public CDNs, so the interactive view requires an internet connection.
- **Regenerating the archived Gemini artifact:** `prototype/solver.py` requires `numpy`, `google-genai`, `sentence-transformers`, `networkx`, and `GEMINI_API_KEY` in the environment or an ignored `prototype/.env` file. Regeneration is stochastic and will not reproduce the committed graph exactly.

## Dated Edits

Material additions are recorded by edit date. Purely editorial changes are omitted; unlisted mechanisms and claims were present in the April 7, 2026 publication.

**August 25, 2026 edit**
- *Mandatory Abstraction Before Decomposition*: a specific-to-Root genus-and-differentia ascent with parent/sibling search, exact reverse traversal, typed specialization/composition edges, and explicit parent synthesis before the four-test carve.
- A corrected 100-problem construction artifact using GPT-5.6 Sol, replacing the unintended seeded Gemini construction as the canonical demonstration and reported as a failure-inclusive structural probe rather than an outcome benchmark.
- *Bootstrapping from the System's Own Derivations* (§7): the archive's evaluated solution graphs — dead ends included — as a training corpus for the decomposition faculty itself, amortizing the method into weights.
- The evolutionary-encapsulation rationale developed in *Evolutionary Encapsulation and Emergence in Reverse*: representation and interface compression as a complementary architectural motif, major transitions as a design precedent, boundary assignment beginning at the root Solver, recursive closure of the five-surface Solver Contract, and contract-bounded Solvers as artificial cell-like units.
- The capability-riding answer to the bitter-lesson objection (Limitations): the architecture's human-authored layer is a minimal coordination protocol, its content is model-generated, and its end product compiles into subsequent model generations.
- A third decisive test: whether reuse improves subsequent problem solving.

**June 12, 2026 edit**
- Fractal intelligence defined as a general category, with the Solver architecture as one candidate realization.

**April 7, 2026 publication** — the four-test decomposition algorithm, the five-surface Solver Contract with acceptance gates, the Theory of Depth, joint training through gate signals, the ten protocols, and the planning prototype.

## Citing

```bibtex
@misc{westerberg2026fractal,
  title        = {Fractal Intelligence: Conceptual Decomposition as Problem-Solving Infrastructure},
  author       = {Westerberg, Henrik},
  year         = {2026},
  month        = apr,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.19462645},
  url          = {https://doi.org/10.5281/zenodo.19462645}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata (GitHub
renders a "Cite this repository" button from it).

## License

MIT License
