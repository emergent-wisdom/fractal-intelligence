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

This script does NOT re-run the prototype. It recomputes the quantitative
claims audited below directly from that committed record and checks each value
against the number printed in the paper. If a reader edits the paper or swaps in
a new run, this script tells them immediately which claims no longer hold.

All numbers are derived from tree.json (nodes + routing_paths). stats.json is
used only as an independent cross-check of the reuse ledger.

NOTE on two different activity records:
  * Per-problem ledger = sum of routing-path lengths = 1132. This is what the
    paper's reuse statistics use (every node visited while solving the 100
    problems, labelled "created" or "reused").
  * tree.json sum(times_invoked) = 1260. This equals 1203 stored
    problems_routed references plus one birth baseline for each of the 57 nodes
    whose created_by_problem field is zero. The 1203 route references exceed
    the saved path ledger by 71, reflecting run/resumption history not present
    in the canonical 100 saved paths. These counters are therefore reported
    only as cumulative stored activity, never as a subset of the 1132 actions.

PROVENANCE CAVEAT:
  created_by_problem == 0 does not mean "created before the run." Both initial
  seeding and later maintenance used zero as a default. Node IDs are monotonic,
  so for this committed artifact the first problem-attributed node provides the
  cutoff: solver_0001--solver_0029 are the initial skeleton; the other 28
  surviving zero-origin nodes are maintenance output. Future runs should record
  an explicit creation phase rather than relying on this reconstruction.

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
node_num = lambda n: int(n["id"].split("_")[1])              # noqa: E731
first_problem_node = min(node_num(n) for n in nodes if n["created_by_problem"] > 0)
is_initial = lambda n: node_num(n) < first_problem_node      # noqa: E731
is_maintenance = lambda n: (                                # noqa: E731
    n["created_by_problem"] == 0 and not is_initial(n)
)
is_top_seed = lambda n: 1 <= node_num(n) <= 6               # noqa: E731
by_concept = {n["concept"]: n for n in nodes}
initial = [n for n in nodes if is_initial(n)]
maintenance = [n for n in nodes if is_maintenance(n)]
problem_created = [n for n in nodes if n["created_by_problem"] > 0]

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

def path_activity(concept):
    """Appearances and distinct domains in the canonical saved path ledger."""
    appearances = [
        (p["domain"], e)
        for p in paths
        for e in p["path"]
        if e.get("concept") == concept
    ]
    return len(appearances), len({domain for domain, _ in appearances})

path_appearances = Counter()
path_reuses = Counter()
path_domains = {}
for p in paths:
    for e in p["path"]:
        concept = e.get("concept")
        path_appearances[concept] += 1
        if e.get("action") == "reused":
            path_reuses[concept] += 1
        path_domains.setdefault(concept, set()).add(p["domain"])

initial_concepts = {n["concept"] for n in initial}
maintenance_concepts = {n["concept"] for n in maintenance}

def concept_cohort(concept):
    if concept in initial_concepts:
        return "initial"
    if concept in maintenance_concepts:
        return "maintenance"
    return "problem"

def path_reuse_share(threshold, cohort):
    """Canonical reuse actions on concepts appearing in >= threshold domains."""
    pool = [c for c, domains in path_domains.items() if len(domains) >= threshold]
    denom = sum(path_reuses[c] for c in pool)
    num = sum(path_reuses[c] for c in pool if concept_cohort(c) == cohort)
    return num, denom

# ---- cross-domain concentration in final stored node counters ---------------
def share(threshold, restrict):
    """Stored activity on nodes serving >= threshold domains; subset / all."""
    pool = [n for n in nodes if dom(n) >= threshold]
    denom = sum(inv(n) for n in pool)
    if restrict == "initial":
        num = sum(inv(n) for n in pool if is_initial(n))
    elif restrict == "maintenance":
        num = sum(inv(n) for n in pool if is_maintenance(n))
    elif restrict == "six":
        num = sum(inv(n) for n in pool if is_top_seed(n))
    else:
        num = denom
    return num, denom

initial3_num, initial3_den = share(3, "initial")
maintenance3_num, _ = share(3, "maintenance")
initial5_num, initial5_den = share(5, "initial")
six3_num, _ = share(3, "six")

# ---- canonical path-ledger cross-domain concentration and highways ----------
path_initial3_num, path_initial3_den = path_reuse_share(3, "initial")
path_maintenance3_num, _ = path_reuse_share(3, "maintenance")
path_problem3_num, _ = path_reuse_share(3, "problem")
path_initial5_num, path_initial5_den = path_reuse_share(5, "initial")
path_top6_num = sum(
    path_reuses[n["concept"]]
    for n in initial
    if is_top_seed(n) and len(path_domains.get(n["concept"], set())) >= 3
)

busiest_concepts = sorted(
    path_appearances,
    key=lambda c: (-len(path_domains[c]), -path_appearances[c], c),
)[:15]
busiest_initial = sum(
    1 for c in busiest_concepts if concept_cohort(c) == "initial"
)
busiest_exceptions = [
    c for c in busiest_concepts if concept_cohort(c) != "initial"
]
ge6_deep_concepts = [
    c for c, domains in path_domains.items()
    if len(domains) >= 6 and c in by_concept and by_concept[c]["depth"] >= 2
]
ge6_deep_initial = sum(
    1 for c in ge6_deep_concepts if concept_cohort(c) == "initial"
)

# ---- final-snapshot provenance and counter integrity ------------------------
stored_invocations = sum(inv(n) for n in nodes)
stored_route_refs = sum(len(n["feedback"]["problems_routed"]) for n in nodes)
zero_origin = [n for n in nodes if n["created_by_problem"] == 0]
depth_counts = Counter(n["depth"] for n in nodes)
depth2_single_invocation = sum(
    1 for n in nodes if n["depth"] == 2 and inv(n) == 1
)
trace_actions = Counter(
    t.get("action") for p in paths for t in p.get("trace", [])
)
budget_used = sum(p["budget_used"] for p in paths)
budget_available = sum(p["budget"] for p in paths)
top_seed_ids = {n["id"] for n in initial if is_top_seed(n)}
path_seed_sets = [
    {e.get("node") for e in p["path"] if e.get("node") in top_seed_ids}
    for p in paths
]
domain_seed_sets = {}
for p, seed_ids in zip(paths, path_seed_sets):
    domain_seed_sets.setdefault(p["domain"], set()).update(seed_ids)

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

print("\n-- Provenance split (Sec. prototype / Seed Dependence) --")
chk("first problem-attributed node number", first_problem_node, 30)
chk("initial pre-problem nodes", len(initial), 29)
chk("protected depth-1 seeds", sum(1 for n in initial if is_top_seed(n)), 6)
chk("initial descendants", sum(1 for n in initial if not is_top_seed(n)), 23)
chk("surviving maintenance-created nodes", len(maintenance), 28)
chk("problem-created nodes", len(problem_created), 399)
chk("all zero-origin nodes (initial + maintenance)", len(zero_origin), 57)
chk("maintenance average domains served", round(sum(dom(n) for n in maintenance) / len(maintenance), 2), 0.46)
chk("maintenance nodes serving <=1 domain", sum(1 for n in maintenance if dom(n) <= 1), 27)
chk("maintenance nodes with stored invocation count 1", sum(1 for n in maintenance if inv(n) == 1), 17)

print("\n-- Reuse, per-problem routing-path ledger (prototype / Seed Dependence) --")
chk("total activations", total_act, 1132)
chk("reused activations", reused, 730)
chk("reuse rate rounds to 64%", round(reuse_rate * 100), 64)
chk("first-20 reuse rounds to 63%", round(first20 * 100), 63)
chk("last-20 reuse rounds to 63%", round(last20 * 100), 63)

print("\n-- Stored-counter integrity (prototype limitations) --")
chk("sum(times_invoked)", stored_invocations, 1260)
chk("stored problems_routed references", stored_route_refs, 1203)
chk("zero-origin birth baselines", stored_invocations - stored_route_refs, 57)
chk("route references absent from saved path ledger", stored_route_refs - total_act, 71)

print("\n-- Final graph depth distribution (prototype) --")
chk("depths 1..6", [depth_counts[d] for d in range(1, 7)], [6, 93, 225, 127, 4, 1])
chk("depth-2 nodes with stored invocation count 1", depth2_single_invocation, 69)

print("\n-- Marginal-value and budget ledger (prototype) --")
chk("MVR decisions", trace_actions["mvr_approved"] + trace_actions["mvr_override"], 875)
chk("MVR approvals", trace_actions["mvr_approved"], 851)
chk("MVR overrides", trace_actions["mvr_override"], 24)
chk("recorded restructuring events", trace_actions["restructure"], 43)
chk("aggregate budget used/available", f"{budget_used}/{budget_available}", "1132/1428")
chk("budget utilization rounds to 79%", round(budget_used / budget_available * 100), 79)

print("\n-- Direct routing through the six top-level seeds (General Protocol) --")
chk("problems invoking at least one top seed", sum(bool(s) for s in path_seed_sets), 76)
chk("problems invoking all six top seeds", sum(s == top_seed_ids for s in path_seed_sets), 0)
chk("domains collectively exercising all six top seeds",
    sum(s == top_seed_ids for s in domain_seed_sets.values()), 4)

print("\n-- Cross-domain concentration in stored counters (Seed Dependence) --")
chk(">=3 domains: initial/total stored activity", f"{initial3_num}/{initial3_den}", "556/716")
chk(">=3 domains: initial share rounds to 78%", round(initial3_num / initial3_den * 100), 78)
chk(">=3 domains: maintenance/total stored activity", f"{maintenance3_num}/{initial3_den}", "4/716")
chk(">=5 domains: initial share rounds to 92%", round(initial5_num / initial5_den * 100), 92)
chk(">=3 domains: six-seeds-only share rounds to 38%", round(six3_num / initial3_den * 100), 38)

print("\n-- Canonical cross-domain reuse in saved paths (Seed Dependence) --")
chk(">=3 path domains: initial/total reuse actions", f"{path_initial3_num}/{path_initial3_den}", "483/606")
chk(">=3 path domains: initial share rounds to 80%", round(path_initial3_num / path_initial3_den * 100), 80)
chk(">=3 path domains: maintenance reuse actions", f"{path_maintenance3_num}/{path_initial3_den}", "3/606")
chk(">=3 path domains: problem-created reuse actions", f"{path_problem3_num}/{path_initial3_den}", "120/606")
chk(">=5 path domains: initial share rounds to 93%", round(path_initial5_num / path_initial5_den * 100), 93)
chk(">=3 path domains: six-seeds-only share rounds to 39%", round(path_top6_num / path_initial3_den * 100), 39)

print("\n-- Busiest canonical path-ledger highways (Seed Dependence / prototype) --")
chk("initial among the 15 most cross-domain solvers", busiest_initial, 14)
chk("the lone problem-created exception", busiest_exceptions, ["DistributionProtocolSolver"])
chk("sub-concepts below depth-1 serving >=6 domains", len(ge6_deep_concepts), 14)
chk("  of which from the initial skeleton", ge6_deep_initial, 12)

print("\n-- Named highways: canonical path appearances x domains (prototype) --")
for name, ti, dd in [("MechanismSolver", 71, 20), ("StakeholderSolver", 48, 18),
                     ("IncentiveAlignmentSolver", 28, 16), ("AdjustmentLoopSolver", 25, 15),
                     ("ComponentArchitectureSolver", 30, 13)]:
    got_ti, got_dd = path_activity(name)
    chk(name, f"{got_ti}x/{got_dd}dom", f"{ti}x/{dd}dom")

print("\n-- Worked cross-domain example, Sec. prototype: StabilityRegulationSolver --")
chk("SRS is initial (created before any problem ran)", is_initial(srs), True)
chk("SRS path-ledger domains served", path_activity("StabilityRegulationSolver")[1], 5)
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
