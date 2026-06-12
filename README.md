# Fractal Intelligence: Conceptual Decomposition as Problem-Solving Infrastructure

[![Paper](https://img.shields.io/badge/Paper-PDF-red)](fractal-intelligence.pdf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19462645.svg)](https://doi.org/10.5281/zenodo.19462645)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Instead of asking how a human would solve a problem, this paper asks what the problem is *made of* — and decomposes it into concepts rather than tasks: the dimensions of the thing itself, which recur across domains where steps do not. Each concept becomes a node behind a uniform five-surface contract (the **Solver**), so a whole collective presents to its parent as a single node — specialists all the way down — and any reasoner (a model, a human, a further subtree) can stand behind one.

The same boundary that composes also isolates: a generator runs at its extreme without softening for the critic that judges it, and rejection forces a re-carve rather than a retry. Concepts that recur become permanent, content-addressed infrastructure (**reasoning highways**), so reasoning accumulates across problems instead of being rebuilt each time.

The paper argues and probes this rather than proves it: companion experiments lend the isolation and reframing claims preliminary support, and a prototype shows the contract composes. The decisive test is whether decomposed solving outperforms the conventional approach at matched compute; the deeper question is whether independent attempts converge on the same concepts. Should both hold, the result is not a faster pipeline but a shared, persistent substrate: an *internet of reasoning*.

**Paper:** [`fractal-intelligence.pdf`](fractal-intelligence.pdf)

## Key Ideas

- **Concepts over tasks** — task decompositions dissolve after execution; conceptual decompositions (what a problem *is made of*) persist and transfer across domains
- **The Solver Contract** — a five-surface interface (Manifest, Execute, Consult, Verify, Feedback) composing heterogeneous, mutually untrusting reasoners
- **Cognitive isolation** — competing modes (generation, verification, critique, empathy) behind typed boundaries so they cannot suppress each other; rejection forces structural reframing, not token-level compromise
- **The Theory of Depth** — a marginal-value rule deciding, at every node, whether decomposing deeper is worth its cost
- **Reasoning highways** — recurring concepts crystallize as content-addressed (Sema) infrastructure, reused across unrelated problems
- **Two decisive tests** — matched-compute performance against the conventional approach, and convergence of independent decompositions on the same concepts

## Repository Contents

- [`fractal-intelligence.tex`](fractal-intelligence.tex) / [`fractal-intelligence.pdf`](fractal-intelligence.pdf) — the paper
- [`prototype/`](prototype/) — the simulation reported in the paper: planning engine, graph layer (`ust.db`, 456 nodes / 582 edges), analysis scripts, and an interactive 3D visualization (`index.html`)
- [`references.bib`](references.bib) — bibliography

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

See [`CITATION.cff`](CITATION.cff) for the machine-readable version (GitHub
renders a "Cite this repository" button from it).

## License

MIT License
