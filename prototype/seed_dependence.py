#!/usr/bin/env python3
"""
seed_dependence.py -- Reproducibility audit for the Fractal Intelligence paper.

WHY THIS SCRIPT EXISTS
----------------------
The prototype (solver.py) is a STOCHASTIC, LLM-driven simulation. It calls a
language model and uses random.choice() with no fixed seed, so re-running it
produces a different graph every time. The committed artifacts -- tree.json and
stats.json -- are therefore the *canonical record* of the single run the paper
reports, not a computation that can be re-derived bit-for-bit.

This script does NOT re-run the prototype. It recomputes every quantitative
claim in the paper directly from that committed record and checks each value
against the number printed in the paper. If a reader edits the paper or swaps in
a new run, this script tells them immediately which claims no longer hold.

All numbers are derived from tree.json (nodes + routing_paths). stats.json is
used only as an independent cross-check of the reuse ledger.

NOTE on two different "activation" counts:
  * Per-problem ledger = sum of routing-path lengths = 1132. This is what the
    paper's reuse statistics use (every node visited while solving the 100
    problems, labelled "created" or "reused").
  * tree.json sum(times_invoked) = 1260 is larger because times_invoked also
    counts the invocations that built the 57-node seed skeleton BEFORE any
    problem ran. The paper deliberately reports the per-problem ledger.

Run:   python3 seed_dependence.py
Exit:  0 if every claim matches the paper, 1 otherwise.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
tree = json.load(open(os.path.join(HERE, "tree.json")))
nodes = tree["nodes"]
edges = tree["edges"]
paths = tree["routing_paths"]

dom = lambda n: len(n["feedback"]["domains_served"])        # noqa: E731
inv = lambda n: n["feedback"]["times_invoked"]              # noqa: E731
is_seed = lambda n: n["created_by_problem"] == 0            # noqa: E731  (skeleton: built before problems)
by_concept = {n["concept"]: n for n in nodes}
seed = [n for n in nodes if is_seed(n)]

# ---- reuse ledger, derived from routing-path actions ------------------------
acts = [e for p in paths for e in p["path"]]
total_act = len(acts)
reused = sum(1 for e in acts if e.get("action") == "reused")
reuse_rate = reused / total_act

paths_sorted = sorted(paths, key=lambda p: p["problem_id"])
def _prob_reuse(p):
    pl = p["path"]
    return (sum(1 for e in pl if e.get("action") == "reused") / len(pl)) if pl else 0.0
first20 = sum(_prob_reuse(p) for p in paths_sorted[:20]) / 20
last20 = sum(_prob_reuse(p) for p in paths_sorted[-20:]) / 20

# ---- cross-domain concentration on the seed skeleton ------------------------
def share(threshold, restrict):
    """Invocations on solvers serving >= threshold domains; restricted subset / all."""
    pool = [n for n in nodes if dom(n) >= threshold]
    denom = sum(inv(n) for n in pool)
    if restrict == "skeleton":
        num = sum(inv(n) for n in pool if is_seed(n))
    elif restrict == "six":
        num = sum(inv(n) for n in pool if is_seed(n) and n["depth"] == 1)
    else:
        num = denom
    return num, denom

sk3_num, sk3_den = share(3, "skeleton")
sk5_num, sk5_den = share(5, "skeleton")
six3_num, _ = share(3, "six")

# ---- busiest cross-domain highways ------------------------------------------
busiest = sorted(nodes, key=lambda n: (-dom(n), -inv(n)))[:15]
busiest_seeded = sum(1 for n in busiest if is_seed(n))
busiest_exceptions = [n["concept"] for n in busiest if not is_seed(n)]
ge6_deep = [n for n in nodes if dom(n) >= 6 and n["depth"] >= 2]
ge6_deep_seeded = sum(1 for n in ge6_deep if is_seed(n))

# ---- worked cross-domain example, Sec. prototype (StabilityRegulationSolver) -
srs = by_concept.get("StabilityRegulationSolver")
def routed_by(node_id, problem_id):
    p = next((p for p in paths if p["problem_id"] == problem_id), None)
    return bool(p) and any(e.get("node") == node_id for e in p["path"])

# ---- checks -----------------------------------------------------------------
checks = []
def chk(label, got, want, ok=None):
    ok = (got == want) if ok is None else ok
    checks.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, paper says {want!r}")

print("=" * 72)
print("FRACTAL INTELLIGENCE -- REPRODUCIBILITY AUDIT (paper numbers vs. tree.json)")
print("=" * 72)

print("\n-- Graph structure (Sec. prototype) --")
chk("total nodes", len(nodes), 456)
chk("total edges", len(edges), 582)

print("\n-- Seed skeleton: created_by_problem == 0 (Sec. limitations, Seed Dependence) --")
chk("skeleton nodes", len(seed), 57)
chk("depth-1 seeds", sum(1 for n in seed if n["depth"] == 1), 6)
chk("deeper pre-decomposed descendants", sum(1 for n in seed if n["depth"] >= 2), 51)
chk("skeleton spans depths 1-4 (max depth)", max(n["depth"] for n in seed), 4)

print("\n-- Reuse, per-problem routing-path ledger (prototype / Seed Dependence) --")
chk("total activations", total_act, 1132)
chk("reused activations", reused, 730)
chk("reuse rate rounds to 64%", round(reuse_rate * 100), 64)
chk("first-20 reuse rounds to 63%", round(first20 * 100), 63)
chk("last-20 reuse rounds to 63%", round(last20 * 100), 63)

print("\n-- Cross-domain concentration on the skeleton (Seed Dependence) --")
chk(">=3 domains: skeleton/total invocations", f"{sk3_num}/{sk3_den}", "560/716")
chk(">=3 domains: skeleton share rounds to 78%", round(sk3_num / sk3_den * 100), 78)
chk(">=5 domains: skeleton share rounds to 92%", round(sk5_num / sk5_den * 100), 92)
chk(">=3 domains: six-seeds-only share rounds to 38%", round(six3_num / sk3_den * 100), 38)

print("\n-- Busiest cross-domain highways (Seed Dependence / prototype) --")
chk("seeded among the 15 most cross-domain solvers", busiest_seeded, 14)
chk("the lone problem-created exception", busiest_exceptions, ["DistributionProtocolSolver"])
chk("sub-concepts below depth-1 serving >=6 domains", len(ge6_deep), 15)
chk("  of which from the pre-seeded skeleton", ge6_deep_seeded, 13)

print("\n-- Named highways: invocations x domains (prototype) --")
for name, ti, dd in [("MechanismSolver", 78, 20), ("StakeholderSolver", 51, 19),
                     ("IncentiveAlignmentSolver", 30, 17), ("AdjustmentLoopSolver", 29, 15),
                     ("ComponentArchitectureSolver", 34, 13)]:
    n = by_concept[name]
    chk(name, f"{inv(n)}x/{dom(n)}dom", f"{ti}x/{dd}dom")

print("\n-- Worked cross-domain example, Sec. prototype: StabilityRegulationSolver --")
chk("SRS is seeded (created before any problem ran)", is_seed(srs), True)
chk("SRS domains served", dom(srs), 5)
chk("SRS routed by #4 'Stabilize a currency during hyperinflation'", routed_by(srs["id"], 4), True)
chk("SRS routed by #51 (child emotional regulation)", routed_by(srs["id"], 51), True)

try:
    stats = json.load(open(os.path.join(HERE, "stats.json")))
    print("\n-- Independent cross-check vs stats.json --")
    chk("stats.total_reuse_events == path-derived reused", stats["total_reuse_events"], reused)
    chk("stats.total_nodes", stats["total_nodes"], 456)
    chk("stats.total_edges", stats["total_edges"], 582)
    print(f"  (info) path-action histogram: {dict(Counter(e.get('action') for e in acts))}")
except FileNotFoundError:
    print("\n(stats.json not found -- skipping cross-check)")

print("\n" + "=" * 72)
ok = all(checks)
print(f"RESULT: {sum(checks)}/{len(checks)} checks passed -- {'ALL CLAIMS MATCH' if ok else 'MISMATCH FOUND'}")
print("=" * 72)
sys.exit(0 if ok else 1)
