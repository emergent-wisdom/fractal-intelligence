"""
Analyze the solver tree and produce stats for the paper.
Run after solver.py completes.
"""

import json
import os
from collections import Counter

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, "tree.json")) as f:
    tree = json.load(f)
with open(os.path.join(script_dir, "stats.json")) as f:
    stats = json.load(f)

print("=" * 70)
print("FRACTAL INTELLIGENCE PROTOTYPE — ANALYSIS")
print("=" * 70)

print(f"\n=== OVERVIEW ===")
print(f"Problems processed: {len(tree['routing_paths'])}")
print(f"Total solver nodes: {len(tree['nodes'])}")
print(f"Total edges: {len(tree['edges'])}")
print(f"Total reuse events: {stats['total_reuse_events']}")

# Reuse curve
rc = stats["reuse_curve"]
first20 = [r["reuse_pct"] for r in rc[:20]]
last20 = [r["reuse_pct"] for r in rc[-20:]]
print(f"\nAvg reuse (first 20 problems): {sum(first20)/len(first20)*100:.1f}%")
print(f"Avg reuse (last 20 problems):  {sum(last20)/len(last20)*100:.1f}%")

# Depth
depths = [n["depth"] for n in tree["nodes"]]
dc = Counter(depths)
print(f"\n=== DEPTH DISTRIBUTION ===")
for d in sorted(dc.keys()):
    print(f"  Depth {d}: {dc[d]} nodes")

# Domains
all_domains = set()
for n in tree["nodes"]:
    all_domains.update(n["feedback"]["domains_served"])
print(f"\nDomains covered: {len(all_domains)}")

# Canonical path-ledger highways. Final node counters contain resumption history
# that is absent from the 100 saved paths, so they are not interchangeable.
path_appearances = Counter()
path_domains = {}
for path in tree["routing_paths"]:
    for event in path["path"]:
        concept = event["concept"]
        path_appearances[concept] += 1
        path_domains.setdefault(concept, set()).add(path["domain"])

highways = sorted(
    path_appearances,
    key=lambda c: (-len(path_domains[c]), -path_appearances[c], c),
)
print(f"\n=== TOP 20 REASONING HIGHWAYS (CANONICAL SAVED PATHS) ===")
for concept in highways[:20]:
    print(f"  {concept:40s} {path_appearances[concept]:3d}x across {len(path_domains[concept]):2d} domains")

# Multi-domain nodes
multi = [n for n in tree["nodes"] if len(n["feedback"]["domains_served"]) >= 5]
print(f"\nNodes serving 5+ domains: {len(multi)} of {len(tree['nodes'])} ({len(multi)/len(tree['nodes'])*100:.0f}%)")

# Budget
budgets = stats["budget_allocation"]
avg_budget = sum(b["budget"] for b in budgets) / len(budgets)
avg_spent = sum(b["spent"] for b in budgets) / len(budgets)
print(f"\n=== BUDGET ===")
print(f"Avg budget: {avg_budget:.1f}, Avg spent: {avg_spent:.1f}, Utilization: {avg_spent/avg_budget*100:.1f}%")
tight = [b for b in budgets if b["budget"] <= 5]
print(f"Tight budget problems (≤5): {len(tight)}")

# Cross-domain examples
print(f"\n=== CROSS-DOMAIN REUSE EXAMPLES ===")
for concept in highways[:5]:
    print(f"  {concept} ({len(path_domains[concept])} domains, {path_appearances[concept]}x):")
    examples = [
        path for path in tree["routing_paths"]
        if any(event["concept"] == concept for event in path["path"])
    ]
    for path in examples[:3]:
        print(f"    #{path['problem_id']} ({path['domain']}): {path['problem_text'][:55]}")
    print()

# Reuse curve for paper
print(f"=== REUSE CURVE (every 10th problem) ===")
for r in rc[::10]:
    print(f"  Problem {r['problem']:3d}: {r['reuse_pct']*100:5.1f}% reuse")

print(f"\n{'=' * 70}")
print("Done.")
