# Fractal Intelligence root-first construction prompt

You are constructing a provisional Fractal Intelligence problem-solving graph.
Its purpose is not to store ordinary solution routines. It must represent a
reusable hierarchy of conceptual abstraction through which concrete problems
are understood before they are solved.

The one supplied node, `solver-0001` (`RootSolver`), is the universal boundary
for Problem Solving. It is the highest abstraction in this graph. No narrower
node may remain outside it.

## The required movement

For every concrete problem, reason in two directions.

### 1. Climb upward first

Before choosing a solution or downward decomposition, begin with the specific
problem and repeatedly ask:

- What am I ultimately trying to do, and why?
- What more general class of problem or reusable capability is this an instance
  of?
- Does that abstraction already exist in the graph?
- If not, does creating it expose a genuinely more general way to understand
  this and other problems?

Continue until the chain reaches `solver-0001`. Record the concise public chain
in `abstraction_ascent`, ordered from the most specific capability upward to
`RootSolver`. Every step must say why the next node is more general and what the
more abstract perspective changes about the later decomposition.

Every ascent edge must be conceptually adjacent. Do not jump from a narrow
problem-specific node straight to a very broad umbrella merely because the
umbrella is true. Ask what reusable invariant lies between them and whether
viewing the problem through it changes the children that become visible.

Do not stop after inventing one convenient parent. At every proposed
`specialization` attachment—not only directly below `RootSolver`—perform a
sibling-formation test:

1. Inspect the proposed parent's existing children and the nodes introduced by
   earlier cases in this batch.
2. Ask which of them share a reusable capability or invariant with the new
   node, at a level narrower and more informative than the proposed parent.
3. If such a level would change routing or reveal a shared conceptual carve,
   create or reuse that intermediate parent, connect both the old and new
   specializations beneath it, and route this problem through it now.
4. Apply the same test recursively to that intermediate parent on the way to
   `RootSolver`.

A broad umbrella accumulating many unrelated direct specializations is evidence
that the ascent stopped too early. A direct attachment is justified only when
no intermediate abstraction would change the carve; “this is one form of the
parent” is not a sufficient explanation. Do not invent hollow folders merely
to make the tree look balanced: the intermediate must alter what becomes
visible or reusable.

`RootSolver` is maximally general, so a direct specialization beneath it should
normally express one of the broadest differentiated modes or objects of problem
solving, not a narrow family discovered from one or two cases. Ask what all
candidate families are ultimately doing: for example shaping a system,
explaining a phenomenon, choosing under uncertainty, diagnosing a failure, or
creating an expression. These are illustrations of the level, not categories
to copy. A valid node at this level may be a passive membrane or router: it need
not perform domain work itself if crossing it genuinely changes the viewpoint
from which its descendants are carved. Routing through such a level has no
assumed cost, so do not omit it merely because a shorter path is possible.

An abstraction is not useful merely because it groups labels. It must express a
bounded outward capability, reveal a reusable invariant, or change which
dimensions become visible. Do not create domain buckets, conventional
departments, or hollow categories just to shorten the root level.

### 2. Traverse downward and decompose

After the ascent is complete, traverse from `RootSolver` down the exact reverse
of that abstraction chain before branching into the concrete decomposition.
The first invocation must therefore reuse `solver-0001`; only it may have
`parent_id = ROOT` and `edge_kind = root`.

The invocation array serializes a graph, not execution time. The reverse ascent
must exist as an unbroken parent chain, but RootSolver's other constitutive
branches may appear before or after that chain in the array.

The input catalog identifies `required_root_dimensions`: the direct
constitutive dimensions Sol derived from Problem Solving before seeing the
problem stream. They are not decorative. Invoke every one as a direct
`composition` child of the case's RootSolver invocation and state its concrete,
problem-local contribution. They govern how the whole problem is resolved. Use
the rest of `bootstrap_scaffold` wherever its contract fits. Do not create
domain-specific synonyms for scaffold capabilities merely to make the route
look tailored. If experience shows a bootstrap boundary is wrong, revise it
explicitly; otherwise let this general structure govern the problem-local
carve.

Do not let the universal Problem-Solving scaffold replace decomposition of the
thing itself. The paper's restaurant example makes two cuts: what `Creation` is
made of and what a `Restaurant` is made of. Likewise, after reaching the most
specific node in `abstraction_ascent`, decompose that subject or capability into
its own constitutive conceptual dimensions with the four tests. Invoke at least
two differentiated `composition` children beneath the specific composite. They
must answer “what is this thing made of?”, not restate the generic scaffold or
list implementation steps. The specific node's synthesis must explain the
higher-level capability that emerges from their interaction.

“At least two” is only a validator floor, not a target. Use as many independent
dimensions as completeness requires; do not compress a concept merely to keep
the graph small.

At each selected abstraction, let that perspective govern the next children.
Ask what the parent concept is made of, not what sequence of familiar tasks a
person or institution would perform. Screen conceptual children with the
paper's four questions:

1. Necessity: would the parent fail without this dimension?
2. Independence: can this dimension vary without merely duplicating another?
3. Universality: does the dimension belong to the concept rather than one
   conventional implementation?
4. Completeness: do the children together span what the parent must resolve?

The paper's economy example shows the intended difference. A routine approach
lists activities such as gather data, draft policy, implement, and evaluate. A
conceptual carve asks what every economy is made of and proposes Selection,
Distribution, Valuation, Coordination, and Stability. Likewise, creating a
restaurant is not fundamentally the sequence secure funding, hire, permit, and
open: `Creation` can be examined through Intent, Form, Realization, Fit, and
Viability, while `Restaurant` can be examined through Nourishment, Experience,
Flow, Economics, and Identity. These are examples of the level and direction of
thought, not categories to copy into this graph.

The paper also proposes Scope, Evidence, Constraints, Stakeholders, Mechanism,
and Dynamics as one General Problem-Solving Protocol. Treat that as an
author-proposed comparison and fallback hypothesis, not a protected or supplied
six-node skeleton. Derive the bootstrap carve yourself with the four tests; it
may recover, revise, or replace those dimensions.

Recurse only while another level adds useful specificity or exposes a better
carve. A simple problem may remain shallow. Higher abstraction is mandatory;
gratuitous depth is not.

## Graph semantics

- A node is a bounded conceptual capability. It may be a leaf `solver`, a
  `composite`, an `abstraction_parent`, or a `passive` routing concept.
- Node kind is descriptive only. The relationship belongs to the edge: use
  `specialization` when the child is a kind or realization of the parent, and
  `composition` when the child is a necessary differentiated contribution to
  the parent's outward capability. A node may have both kinds of outgoing edge.
- A composite is more than a folder. It routes, constrains, integrates, and
  synthesizes its children into one capability visible from above.
- The same node may serve several parents without changing its canonical
  contract. Put the different role on each edge and invocation.
- Reuse by operational capability and boundary, not wording or domain. Create a
  node only when no existing contract fits.
- Before creating any node, compare its complete proposed contract against the
  highlighted bootstrap scaffold and the whole node index. For a proposed
  specialization, run the sibling-formation test above. For a proposed
  constitutive child, reuse an existing capability under a new parent-relative
  role when its boundary fits; if a near-match exposes a genuinely shared
  invariant, generalize or revise it instead of minting a domain synonym.
- A change of domain is not evidence that the capability changed. Actively
  compare the current proposal with nodes introduced by earlier cases in the
  same batch as well as stable catalog nodes. If an earlier family was named or
  bounded too narrowly for an invariant now visible in another domain, revise
  it or create a shared parent above both; do not preserve two domain-labelled
  families merely because the first observation was provisional.
- `topology_edges` are committed before the case's invocations. Use them to
  attach any newly discovered abstraction both upward toward `RootSolver` and
  downward toward what it organizes, so the same problem can traverse it.
- Every persistent node must remain reachable from `solver-0001`. There must be
  no other top-level root, decorative parent, disconnected node, or cycle.
- Keep public explanations concise. Do not reveal private chain-of-thought.

For every problem, return a useful concrete proposal, but spend the reasoning
budget on ascent, framing, and conceptual structure rather than repeating the
problem. The public JSON is a compact structural record, not an essay. Use
precise clauses: normally no more than 18 words per node-contract field, edge
role/rationale, or ascent judgment; 14 words per invocation role/contribution;
35 words for framing or synthesis; and 45 words for the final proposal. These
are compression targets, not permission to omit a necessary distinction or
constituent.

The controller checks ordering, stable references, typed edges, root
connectivity, ascent/route correspondence, uniqueness, and acyclicity. It does
not decide whether an abstraction is insightful; that semantic judgment is
yours. Do not inspect files, browse, or call tools. Return schema-constrained
JSON directly.
