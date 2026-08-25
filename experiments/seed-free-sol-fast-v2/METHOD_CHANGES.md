# Mid-run method changes

The canonical 100-problem artifact is an adaptive construction run. It must not
be described as a single frozen-method or preregistered evaluation.

## Pre-run development

The prompt and harness were iteratively developed with several local rehearsals
and pilots using problems from the same 100-problem corpus. These included three
five-problem rehearsals, one stopped 40-case run, and two ten-problem pilots. The
ten problems in the two immediate pilots became the first ten cases of the
canonical run. The final run is therefore a transparent construction artifact,
not a held-out test of a method developed elsewhere.

## Before case batch 1

The semantic method was fixed before the canonical run began:

- mandatory specific-to-Root abstraction ascent;
- a contrastive broad-mode test before direct Root specialization;
- recursive sibling formation at every specialization attachment;
- cross-domain contract comparison rather than domain-name matching;
- reverse traversal from Root after ascent;
- all direct bootstrap dimensions applied at Root;
- a separate four-test decomposition of the thing itself;
- typed composition/specialization edges, multi-parent reuse, and rooted-DAG
  validation.

Bootstrap and the first ten cases used the same schema and controller semantics
as the rest of the run.

The bootstrap was blind to the 100 problem texts, not to the theory prompt. It
saw the paper-derived four tests, worked economy and restaurant examples, the
author-proposed General Problem-Solving Protocol, and illustrative broad modes.
RootSolver itself was authored; the 24 non-root bootstrap nodes were model
derived.

## Change after the accepted ten-case checkpoint

The first checkpoint took 429.285 seconds and produced 101,121 bytes of public
response JSON. After inspecting its semantic structure, two efficiency changes
were made before batch 2:

1. Checkpoint size changed from 10 to 20 cases. This is recorded in
   `state.config.batch_size_history`. The final batch contains 10 cases because
   only 10 remained.
2. The output-style paragraph in `BATCH_PROMPT.md` changed. Batch 1 used:

   > For every problem, return a useful concrete proposal, but spend the
   > reasoning budget on ascent, framing, and conceptual structure rather than
   > repeating the problem. Roughly 50--80 words is enough for the final
   > proposed solution, and an abstraction-only invocation may use a single
   > clause for its contribution.

   Batches 2--6 used the current compactness targets: normally at most 18 words
   per node-contract/edge/ascent field, 14 per invocation role/contribution, 35
   for framing/synthesis, and 45 for the proposal. Those targets explicitly did
   not cap node count, constituent count, or semantic distinctions.

The runner's projection calculation was also changed to report average seconds
per accepted problem and to record an intentional resume-time batch-size
change. No code in `apply_bootstrap`, `apply_case`, `apply_batch`, graph
validation, or `response.schema.json` was changed after case construction began.
The accepted bootstrap and first ten cases were not regenerated or edited.

## Call and context boundary

The run comprises seven sequential ephemeral Codex CLI calls: one bootstrap and
six problem batches of 10, 20, 20, 20, 20, and 10 cases. Calls did not retain a
conversation. Each problem call received a compact reconstruction of the graph
plus all problem texts in that batch. The prompt instructed ordered processing
without using later cases as evidence, and the controller enforced reference
order, but the later texts were visible in the same context.

The reconstruction included all typed edges; a complete bootstrap scaffold;
every node's ID, name, kind, and capability clipped to 180 characters; and full
contracts for at most 120 relevance-ranked nodes. Starting with batch 3, this
meant that some prior contracts were not available in full.

## Consequence

The state is a valid append-only record of one adaptive construction process,
and all public outputs and timings are retained. It is suitable for inspecting
whether the procedure can form abstraction layers and persistent reuse. It is
not suitable for a claim that one fixed prompt/batch configuration achieved the
reported result. A future outcome benchmark or strict reproducibility study
should freeze prompt, schema, runner hashes, problem order, batch size, and
semantic audit criteria before its first model call. This state also omits the
Codex CLI version, token usage, exact backend model snapshot, sampling settings
or seed, catalog-detail limit, and effective timeout. The timeout must have been
greater than 631.521 seconds, but its exact value has not been recovered. Since
only schema-constrained public JSON was retained, semantic no-lookahead and
no-tool compliance are instructed properties rather than independently auditable
facts.
