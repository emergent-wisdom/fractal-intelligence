# Mandatory-abstraction Sol construction

This experiment constructs a provisional Fractal Intelligence planning graph
from 100 heterogeneous problems. It was designed after the earlier fast run
showed a central failure: problems could satisfy the format while attaching
flat, problem-specific branches beneath an overly broad parent. Here,
abstraction is a required operation rather than optional prompting style.

The artifact is a machine-generated planning and topology demonstration. It is
not an outcome benchmark and does not claim that the generated ontology is
correct.

## Construction procedure

The controller supplies one authored persistent node, `solver-0001`
(`RootSolver`), as the universal boundary for Problem Solving.

1. A `gpt-5.6-sol`/medium bootstrap call sees RootSolver and the complete theory
   prompt, but no text from the 100-problem stream, and derives a provisional
   first-principles decomposition of Problem Solving. The prompt includes the
   paper's four tests, economy and restaurant examples, the author-proposed
   General Problem-Solving Protocol, and broad-mode illustrations. The bootstrap
   is therefore problem-blind, not theory-free or taxonomy-unprimed.
2. For each concrete problem, Sol must climb upward first: repeatedly ask what
   more general reusable capability the problem instantiates until the chain
   reaches RootSolver.
3. Every proposed specialization attachment receives a sibling-formation test.
   The model must insert an informative intermediate parent when a shared
   invariant changes routing or the later carve. A direct Root child must be a
   contrastive broad mode of resolution, not a narrow family.
4. The case then traverses the exact reverse chain from Root downward. Every
   blind-bootstrap root dimension contributes to the case.
5. Separately, the most-specific subject is decomposed into what that thing is
   made of. Its parent synthesis states the outward capability produced by the
   interaction of those conceptual children.
6. Nodes may recur under several parents with different edge roles. New
   topology is installed before the same case traverses it. Contracts may be
   revised, though the canonical run made no revisions.

Sol decides the semantics: names, boundaries, abstraction depth, decomposition,
reuse, and solution. The deterministic controller validates stable references,
typed edges, one rooted connected DAG, exact ascent/descent correspondence,
mandatory root dimensions, at least two thing-specific constituents, and
atomic checkpoints. It does not validate whether an abstraction is true or
useful.

The construction used seven sequential ephemeral Codex CLI calls: one bootstrap
and six problem batches. No call resumed or persisted a CLI conversation. Each
problem call received a rehydrated catalog and all 10 or 20 ordered problem texts in its batch.
The prompt instructed Sol to process them sequentially and not use later cases as
evidence, and references could only point backward, but the controller cannot
verify semantic non-lookahead inside one call.

Catalog rehydration includes every node's ID, name, kind, and capability clipped
to 180 characters; every typed edge; complete contracts for the bootstrap
scaffold; and complete contracts for at most 120 relevance-ranked candidates.
From batch 3 onward, some existing non-bootstrap contracts were therefore
available only through the clipped index. Global reuse is model-proposed, not a
controller-verified proof that every reused contract fits.

Only schema-constrained public JSON is saved. No raw event stream, private
reasoning trace, reviewer trace, stdout, or stderr is part of the run artifact.
Consequently, compliance with the no-lookahead and no-tool instructions is not
independently auditable from the published files.

The retained artifact does not record the historical authentication method, the
effective local Codex-memory setting, or the complete request envelope. A
post-hoc scan of every retained JSON string found no user-specific identifiers,
local paths, credential patterns, or memory/profile references. This supports a
privacy check on the public outputs but cannot retrospectively prove that no
client-side context influenced generation.

## Canonical 100-problem run

The canonical run is
`runs/sol-mandatory-abstraction-100-2026-08-25/state.json`. Its exact problem
order, resulting graph state, model configuration, response paths, batch
partition, and timing are recorded in that file.

This was an adaptive construction run, not a frozen or preregistered evaluation.
The prompt and harness were developed through several earlier local pilots using
problems from this same corpus, including cases reused at the beginning of the
canonical run. The 100 cases are therefore not a held-out evaluation set.
After the first ten-case checkpoint was accepted and semantically inspected, the
abstraction algorithm and controller acceptance rules were kept fixed, but the
public-output verbosity targets were shortened and later checkpoint size changed
from 10 to 20. The final ten cases used size 10 because only ten remained. The
exact mid-run change and its implications are recorded in
[METHOD_CHANGES.md](METHOD_CHANGES.md).

- Model: `gpt-5.6-sol`
- Bootstrap effort: medium
- Problem-batch effort: low
- Batch sizes: 10, 20, 20, 20, 20, 10
- Semantic reviewer calls: 0
- Bootstrap: 116.960 seconds
- Six problem calls: 3,040.251 seconds
- Total model-call time: 3,157.211 seconds (52m 37.2s)
- End-to-end state time: 3,362 seconds (56m 02s), from `created_at` to
  `updated_at`
- Final graph: 311 nodes, 441 composition edges, 162 specialization edges
- Root composition: six Sol-derived general problem-solving dimensions
- Root specialization: `System Shaping`, `Expression Creation`, and
  `Warranted Knowledge Formation`

The run missed its 30-minute model-call target by 22m 37.2s. That failure is
retained and reported rather than normalized away.

Raw invocation counts overstate learning because every case must invoke
RootSolver and all six root dimensions. Excluding those 700 forced invocations,
the run records 500 reuses and 286 creations (63.6% reuse). Of 417
thing-specific constituent invocations, 290 reuse an existing node (69.5%).
Ninety-nine of 286 problem-created nodes recur, 66 across domains, and 78
problem-created nodes have more than one persistent parent.

See [AUDIT.md](AUDIT.md) for structural results, semantic strengths, and known
boundary failures. The unedited canonical run should be published with that
audit and the method-change record; do not silently repair its ontology.

The state records the problem-source hash, model name, reasoning-effort labels,
problem order, batch partition, and response paths. It does not record hashes of
the prompt, runner, or schema used by each call; the Codex CLI version; token
usage; an exact backend model snapshot; sampling settings or seed; the
`catalog_detail_limit`; or the effective call timeout. Because two accepted calls
lasted more than the runner's current 600-second default, the canonical timeout
was necessarily greater than 631.521 seconds, but its exact value has not been
recovered. The artifact is not bitwise reproducible.

## Illustrative run or resume

From the `fractal-intelligence` repository root, with the Codex CLI already
authenticated:

```sh
python3 experiments/seed-free-sol-fast-v2/batch_runner.py \
  --run-dir experiments/seed-free-sol-fast-v2/runs/my-run \
  --count 100 \
  --batch-size 20 \
  --max-new-batches 1
```

Remove `--max-new-batches 1` to resume after inspecting the accepted
checkpoint. Reuse the same problem selection, model, effort, and batch size.
An intentional checkpoint-size change must be explicit with
`--allow-batch-size-change`; the state records the change.

This command illustrates the current harness; it does not reproduce the adaptive
canonical trajectory. That run used the non-random order recorded in
`config.problem_ids`, beginning with five same-domain pairs presented in two
interleaved rounds. Its first checkpoint used `--batch-size 10`; later
checkpoints used 20, with an explicit `--allow-batch-size-change` on resume. Exact
reconstruction also requires the pre-change output paragraph preserved in
[METHOD_CHANGES.md](METHOD_CHANGES.md), the recorded problem-ID list, and an
unrecorded timeout above 631.521 seconds. These records support procedural
inspection, not exact replay.

## Viewer

Serve this experiment directory:

```sh
python3 -m http.server 9880 --directory experiments/seed-free-sol-fast-v2
```

Open:

`http://127.0.0.1:9880/viewer.html?state=runs/sol-mandatory-abstraction-100-2026-08-25/state.json`

Time 0 shows only the real persistent RootSolver. The blind bootstrap is a
separate step, followed by cases in actual processing order. The animation
filters nodes and edges by their observed creation step, so interleaved problem
IDs cannot reveal future nodes. For each problem, the detail panel exposes the
upward abstraction chain, a nested tree reconstructed from the recorded
parent-linked invocations, the thing-specific constituents, and the declared
parent synthesis. Its allocation bars count the invocation records contained in
each subtree; they are not token or compute budgets and do not recreate the
superseded artifact's model-proposed marginal-value scores.
