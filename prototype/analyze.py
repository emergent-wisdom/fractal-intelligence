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

# Top highways
print(f"\n=== TOP 20 REASONING HIGHWAYS ===")
for h in stats["top_highways"][:20]:
    print(f"  {h['concept']:40s} {h['times_invoked']:3d}x across {h['domains']:2d} domains")

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
for n in sorted(tree["nodes"], key=lambda x: -len(x["feedback"]["domains_served"]))[:5]:
    doms = n["feedback"]["domains_served"]
    print(f"  {n['concept']} ({len(doms)} domains, {n['feedback']['times_invoked']}x):")
    for pid in n["feedback"]["problems_routed"][:3]:
        rp = next((r for r in tree["routing_paths"] if r["problem_id"] == pid), None)
        if rp:
            print(f"    #{pid} ({rp['domain']}): {rp['problem_text'][:55]}")
    print()

# Reuse curve for paper
print(f"=== REUSE CURVE (every 10th problem) ===")
for r in rc[::10]:
    print(f"  Problem {r['problem']:3d}: {r['reuse_pct']*100:5.1f}% reuse")

print(f"\n{'=' * 70}")
print("Done.")
