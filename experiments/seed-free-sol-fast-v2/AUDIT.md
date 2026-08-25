# Audit of the mandatory-abstraction 100-problem run

This audit accompanies the unedited canonical state at
`runs/sol-mandatory-abstraction-100-2026-08-25/state.json`.

State SHA-256:
`969e7625adc5f1ea7a9b5250283ffc6fe9347c4eb6018a45f46b609736333620`

The run was adaptive rather than method-frozen. After the first ten cases, only
serialization targets, checkpoint size, and timing projection mechanics were
changed; semantic construction and acceptance rules were not. See
[METHOD_CHANGES.md](METHOD_CHANGES.md). This limits its use as a controlled
benchmark but does not erase its value as a transparent construction record.

The method was also tuned in earlier local pilots on problems drawn from the same
100-problem corpus. The canonical cases are not a held-out evaluation set.

## Verdict

The run is suitable as a provisional, failure-inclusive planning/topology
demonstration. Across seven ephemeral calls to one model, it records mandatory
abstraction ascent, a rooted hierarchy, conceptual decomposition, persistent
reuse, multi-parent roles, and declared parent synthesis.

It does not establish that Fractal Intelligence improves solution quality, that
the generated ontology is correct, that the graph learned from observed
outcomes, or that independently executing children caused an operational
capability to emerge.

## Structural validation

Independent recomputation found no structural errors:

- 100 registered and accepted cases, each unique
- 311 nodes and 603 typed edges
- exactly one zero-incoming node: `solver-0001` (`RootSolver`)
- all 311 nodes reachable from RootSolver
- no cycles, self-loops, dangling references, duplicate node IDs/names,
  duplicate typed edges, or composition/specialization conflicts
- every ascent begins at a specific capability, reaches RootSolver, and is
  traversed downward through the exact reverse parent chain
- all six bootstrap root dimensions are directly invoked in every case
- every case has at least two differentiated constituents beneath its specific
  composite
- all 579 case topology proposals were added; none was silently skipped
- all seven referenced structured response files exist and parse
- no raw/private trace files or trace-like response fields are present

Ascent length is normally substantial: 39 cases use four nodes, 51 use five,
eight use six, and one uses seven. Only one case uses three.

## Evidence of accumulation

The graph contains strong evidence of nontrivial reuse, after excluding forced
Root/scaffold invocations:

- 500 non-forced reuse invocations versus 286 creations (63.6% reuse)
- 290 of 417 thing-specific constituent invocations reuse existing nodes
  (69.5%)
- 285 of those 290 reused constituents were created in an earlier batch
- 99 of 286 problem-created nodes recur; 66 recur across domains
- 78 problem-created nodes have more than one persistent parent

Examples include:

- `Evidence Traceability`: 18 parents across 10 domains
- `Failure Containment`: 16 parents across eight domains
- `Commercial Viability`: 12 parents across six domains
- `Feedback Legibility`: 12 parents across seven domains
- `Operational Observability`: 10 parents across five domains

The run also forms higher parents retrospectively. For example, later cases
place earlier capabilities beneath `Strategy Game Design`,
`Evidence-Embedded Performance System`, and `Living-System Stewardship`.

Growth changes as infrastructure accumulates. The bootstrap creates 24 non-root
nodes, yielding 25 total; the six case batches create 63, 93, 25, 27, 35, and 43
nodes. Batches three and four therefore solve 40 additional problems while
creating only 52 nodes, primarily recombining existing capabilities.

## Semantic strengths

RootSolver has six blind-bootstrap composition dimensions:

- Problem Constitution
- Explanatory Understanding
- Resolution Synthesis
- Resolution Commitment
- Resolution Realization
- Resolution Regulation

Problem experience adds only three direct specialization modes:

- `System Shaping` — 91 cases across 19 domains
- `Expression Creation` — five cases
- `Warranted Knowledge Formation` — four cases across two domains

Below those modes, recurring families include `Institutional Arrangement
Design`, `Built-Environment System Shaping`, `Service System Shaping`,
`Organizational Capability Transformation`, `Software System Shaping`,
`Talent Development System Design`, and `Regional Infrastructure System
Design`.

Each case also supplies a separate ontology of its specific subject and a
public synthesis of how the children jointly realize the parent capability.
This is evidence of declared conceptual composition and nested encapsulation,
not independent execution.

## Known semantic failures

The main defect is boundary leakage. The run made zero contract revisions even
as cross-domain evidence accumulated. Several underlying affinities are useful,
but the canonical contract retained first-domain wording too narrow for later
reuse:

- `Population Movement Capacity` is evacuation/person-flow bounded but is
  reused for earthquake supply distribution.
- `Evidence Traceability` is editorial/publication bounded but is reused in
  markets, music, agriculture, logistics, healthcare, and software.
- `Network Accessibility` is rail/station/ridership bounded but is reused for
  irrigation, freight, transit, and farm supply chains.
- `Regional Value Distribution` is infrastructure-incidence bounded but is
  reused for trade agreements, wildlife corridors, and rewilding.
- `Cooperative Tension Regulation` is player/session bounded but is reused for
  adaptive music.

The hierarchy also contains at least one clear higher-parent error:
`Talent Development System Design` sits beneath `Organizational Capability
Transformation`. This sends childhood emotional regulation, financial
literacy, adult literacy, home fermentation, and mentorship through an
organizational-transformation frame. A broader capability-development or
system-learning parent was warranted.

Other cautions:

- newsroom verification remains solely beneath `Service System Shaping` after
  `Warranted Knowledge Formation` appears;
- 36 of 59 abstraction parents currently serve only one case and remain
  unvalidated hypotheses;
- 14 of 18 deeper bootstrap nodes are never invoked, so the run demonstrates
  guaranteed use of the six direct root dimensions, not routine traversal of
  the entire bootstrap scaffold;
- 187 of 286 problem-created nodes remain single-case;
- append-only formation can preserve an earlier direct shortcut after a later
  parent is added, producing visually redundant but valid multi-parent routes.

These findings should remain beside the raw run. They are evidence about what
the current construction procedure gets right and where semantic boundary
revision is still missing.

## Methodological limitations

- The authored RootSolver was the only persistent input node. The problem-blind
  bootstrap nevertheless saw the full theory prompt: the four tests, worked
  economy and restaurant examples, author-proposed protocol labels, and
  broad-mode illustrations. Its topology is model-derived but not unprimed.
- Calls were ephemeral and no call resumed or persisted a CLI conversation;
  graph state was rehydrated between calls. A single batch call saw all 10 or 20 problem texts.
  Sequential no-lookahead was instructed and backward references were enforced,
  but semantic non-lookahead cannot be verified.
- The artifact does not record the historical authentication method, effective
  local Codex-memory setting, or complete request envelope. A post-hoc scan of
  all retained JSON found no user-specific identifiers, local paths, credential
  patterns, or memory/profile references, but absolute exclusion of injected
  client-side context cannot be established retrospectively.
- The catalog exposed all node identities, clipped capabilities, typed edges,
  and bootstrap contracts, but complete contracts for only 120 ranked candidates.
  Beginning with batch 3, the model could not inspect every existing contract in
  full. Cross-domain reuse counts are structural model proposals, not validated
  contract equivalences.
- The controller checks graph and serialization invariants, not the truth,
  usefulness, completeness, contract compatibility, or solution quality of the
  model's semantic judgments.
- Only schema-constrained final JSON was retained. No raw event or reasoning
  trace permits independent verification of no-lookahead or no-tool compliance.
- The state omits per-call prompt, runner, and schema hashes; CLI version; token
  usage; backend model snapshot; sampling settings or seed; catalog-detail
  limit; and timeout. The problem source is hashed, but exact replay is not
  possible. The timeout was necessarily above 631.521 seconds because two calls
  exceeded the current 600-second default; its exact value is unrecovered.

## Timing

- Blind bootstrap: 116.960 seconds
- Problem calls: 429.285, 631.521, 492.789, 491.253, 620.600, and 374.803
  seconds
- Accumulated model-call time: 3,157.211 seconds (52m 37.2s)
- End-to-end state time: 3,362 seconds (56m 02s)

The run exceeded its 30-minute model-call target by 22m 37.2s (75.4%). Runtime
should be reported as a failed design target, not as evidence against or for the
theory.
