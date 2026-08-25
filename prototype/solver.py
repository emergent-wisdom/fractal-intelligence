"""
Fractal Intelligence Prototype — Solver v4 (Graph + Embeddings)

Architecture:
  - SQLite graph with auto-embeddings for semantic matching
  - Skeleton view shows LLM the tree structure
  - Semantic search surfaces relevant candidates
  - LLM plans, graph executes with reuse + restructuring
  - MVR verification, structural checks

4 LLM calls per problem:
  1. Plan (skeleton + semantic candidates)
  2. MVR verification
  3. Structural verification
  4. Verify surface for new nodes
"""

import json
import random
import time
import os
from graph import SolverGraph
from google import genai


def load_gemini_api_key() -> str:
    """Read GEMINI_API_KEY from the environment or an ignored local .env file."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == "GEMINI_API_KEY":
                    api_key = value.strip().strip("\"'")
                    if api_key:
                        return api_key

    raise RuntimeError(
        "Set GEMINI_API_KEY in the environment or in prototype/.env before regenerating the run."
    )


client = genai.Client(api_key=load_gemini_api_key())
MODEL = "gemini-3-flash-preview"
THETA = 0.25
MAX_DEPTH = 4


def call_llm(prompt: str, system: str = "", max_tokens: int = 8192) -> dict | None:
    for attempt in range(3):
        try:
            full = f"{system}\n\n{prompt}" if system else prompt
            resp = client.models.generate_content(
                model=MODEL, contents=full,
                config={"max_output_tokens": max_tokens, "response_mime_type": "application/json"},
            )
            text = resp.text.strip()
            return extract_json(text)
        except Exception as e:
            print(f"    LLM attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
    return None


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text: text = text[:text.rfind("```")]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON", text, 0)
    depth = 0; in_str = False; esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc: esc = False; continue
        if c == '\\': esc = True; continue
        if c == '"': in_str = not in_str; continue
        if in_str: continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                try: return json.loads(text[start:i+1])
                except: break
    raise json.JSONDecodeError("Could not extract JSON", text, 0)


# ================================================================
# CALL 1: Plan
# ================================================================

def plan_problem(problem_text: str, domain: str, graph: SolverGraph, budget: int) -> dict | None:
    skeleton = graph.get_skeleton()

    # Semantic search for relevant existing solvers
    candidates = graph.semantic_search(problem_text, limit=8, min_similarity=0.25)
    candidate_details = ""
    if candidates:
        candidate_details = "\n=== MOST RELEVANT EXISTING SOLVERS ===\n"
        candidate_details += "\n\n".join(
            graph.get_node_detail(c["node"]["id"]) for c in candidates[:5]
        )

    system = """You are the RootSolver in a Fractal Intelligence system.

The Universal Solver Tree (UST) organizes all problem-solving knowledge as a tree
where DEPTH = SPECIFICITY:
  Depth 1: FIXED universal concepts (the 6 seeds — never create new ones here)
  Depth 2: Already decomposed sub-concepts (reuse these — they apply to MANY domains)
  Depth 3: Domain-general specializations — still transferable across domains.
           Name these so they'd make sense in ANY domain.
           Good: "RiskQuantificationSolver" Bad: "CurrencyDevaluationRiskSolver"
  Depth 4+: Domain-specific problem solving — THIS is where the real work happens.
           Here you CAN be specific: "CentralBankIndependenceSolver", "TriageProtocolSolver"
           These are the leaves where concrete problem-solving detail lives.

RULES:
1. ALWAYS START from the existing depth-1 solvers. They are universal — every problem
   activates several of them. Routing through depth-1 is FREE (no budget cost).
2. REUSE existing solvers at ANY depth by their [solver_XXXX] ID. Cross-domain reuse is
   the whole point — a FeedbackRegulationSolver created for economics works for education too.
3. CREATE new solvers ONLY under existing parents. New solvers must be CHILDREN, not new roots.
   Name them DOMAIN-GENERALLY: "FeedbackRegulationSolver" not "HospitalFeedbackSolver".
   Ask: would this name make sense in a completely different domain?
4. Budget is spent on depth (creating children), not on top-level routing.
5. NEVER create new depth-1 solvers. The 6 universal seeds are fixed.
6. NEVER restructure depth-1 seeds — they cannot be merged, moved, or re-parented.
7. ALL names: PascalCase ending with "Solver". NO underscores.
8. EVERY new solver MUST include "bounds" (what's in scope) and "not_in_scope" (what's excluded).

The FOUR TESTS for every new solver:
- Necessary: does the parent collapse without it?
- Independent: can it change without affecting siblings?
- Universal: does every instance of the parent have this dimension?
- Complete: do all siblings together cover the parent?

Each field: 2-3 sentences. Be substantive about WHY.

Return ONLY valid JSON:
{
  "opening_narrative": "What makes this problem interesting",
  "plan": [
    {
      "solver": "SomethingSolver",
      "reuse_id": "solver_XXXX or null if new",
      "description": "structural question addressed (REQUIRED for new solvers)",
      "why_needed": "why this problem needs this dimension",
      "what_it_produces": "CONCRETE output for THIS problem — what does this solver decide, recommend, or produce? Be specific: numbers, criteria, designs, not abstractions.",
      "bounds": "what is in scope (REQUIRED for new solvers)",
      "not_in_scope": "what is excluded (REQUIRED for new solvers)",
      "children": [same structure]
    }
  ],
  "restructure": [
    {
      "action": "add_parent|merge|split",
      "new_parent": "ParentSolver (for add_parent — must end with Solver)",
      "description": "unifying concept",
      "bounds": "in scope",
      "not_in_scope": "excluded",
      "children_ids": ["solver_XXXX (NEVER include depth-1 seed solvers)"],
      "keep_id": "solver_XXXX (for merge)",
      "absorb_id": "solver_YYYY (for merge — NEVER a depth-1 seed)",
      "split_id": "solver_XXXX (for split — NEVER a depth-1 seed)",
      "split_into": [{"concept": "NameSolver", "description": "...", "bounds": "...", "not_in_scope": "..."}],
      "why": "why this restructuring is needed"
    }
  ],
  "closing_narrative": "How combined outputs solve the problem"
}"""

    prompt = f"""Problem: "{problem_text}"
Domain: {domain}
Budget: {budget}

=== UNIVERSAL SOLVER TREE ===
{skeleton}
{candidate_details}"""

    return call_llm(prompt, system)


# ================================================================
# CALL 2: MVR verification
# ================================================================

def verify_mvr(plan_items: list, problem_text: str, domain: str, budget: int, trace: list) -> list:
    nodes_to_check = []

    def collect(items, d=1):
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("children"):
                nodes_to_check.append((item, d))
                collect(item["children"], d + 1)
    collect(plan_items)

    if not nodes_to_check:
        return plan_items

    check_list = "\n".join(
        f"- {item.get('solver', '')}: {(item.get('description') or '')[:80]} ({len(item.get('children', []))} children)"
        for item, d in nodes_to_check
    )

    result = call_llm(
        f"""Problem: "{problem_text}" (Domain: {domain}), Budget: {budget}

Solvers requesting decomposition:
{check_list}""",
        system="""Estimate the marginal value of decomposing each solver further.
Return JSON:
{"estimates": [{"solver": "Name", "quality_gain": 0.0-1.0, "cost": 1-3, "reasoning": "one sentence"}]}""",
        max_tokens=2048
    )

    if not result or not isinstance(result, dict) or "estimates" not in result:
        return plan_items

    estimate_map = {e["solver"]: e for e in result["estimates"]}

    for item, depth in nodes_to_check:
        name = item.get("solver", "")
        est = estimate_map.get(name, {})
        qg = est.get("quality_gain", 0.5)
        cost = max(est.get("cost", 1), 1)
        ratio = qg / cost
        reasoning = est.get("reasoning", "")

        if ratio < THETA:
            item["children"] = []
            msg = f"MVR override: {name} dV/dC = {qg:.2f}/{cost} = {ratio:.2f} < θ — executing directly. {reasoning}"
            print(f"  {msg}")
            trace.append({"depth": 0, "action": "mvr_override", "narrative": msg})
        else:
            msg = f"MVR approved: {name} (dV/dC = {qg:.2f}/{cost} = {ratio:.2f} > θ). {reasoning}"
            print(f"  {msg}")
            trace.append({"depth": 0, "action": "mvr_approved", "narrative": msg})

    return plan_items


# ================================================================
# CALL 3: Structural verification
# ================================================================

def structural_verify(plan: list, problem_text: str, domain: str, trace: list):
    if not plan:
        return

    solver_info = json.dumps([
        {"solver": item.get("solver", ""), "description": item.get("description", "")}
        for item in plan
    ], indent=2)

    result = call_llm(
        f"""Problem: "{problem_text}" (Domain: {domain})

Sub-concepts:
{solver_info}""",
        system="""Perform THREE checks:
1. ROUTING: Generate 3 concrete tasks for this specific problem. Check each routes to
   exactly one sub-concept. If they all route cleanly, say so. If there's a real conflict, explain it.
2. LEAKY SEAMS: Does any sub-concept encode assumptions belonging to a sibling?
   Return 0 if none. Only flag genuine architectural leaks, not minor overlaps.
3. COMPLETENESS: Is there a missing dimension? Return null if complete. High bar.

Return JSON:
{"routing": [{"task": "...", "routes_to": "...", "status": "clean|conflict|gap", "explanation": "..."}],
 "leaky_seams": [{"source": "...", "assumption": "...", "belongs_to": "...", "explanation": "..."}],
 "missing_dimension": null}""",
        max_tokens=4096
    )

    if not result or not isinstance(result, dict):
        print("  Structural verification skipped (invalid response)")
        return

    routing = result.get("routing", [])
    if not isinstance(routing, list):
        routing = []
    for r in routing:
        status = r.get("status", "clean")
        task = r.get("task", "")[:80]
        routes = r.get("routes_to", "")
        msg = f"Routing {status}: '{task}' → {routes}"
        print(f"  {msg}")
        trace.append({"depth": 0, "action": f"routing_{status}", "narrative": msg})

    leaky_seams = result.get("leaky_seams", [])
    if not isinstance(leaky_seams, list):
        leaky_seams = []
    for leak in leaky_seams:
        msg = f"Leaky seam: {leak.get('source', '')} assumes {leak.get('assumption', '')}, belongs to {leak.get('belongs_to', '')}"
        print(f"  {msg}")
        trace.append({"depth": 0, "action": "leaky_seam", "narrative": msg})

    missing = result.get("missing_dimension")
    if missing and isinstance(missing, dict) and missing.get("solver"):
        plan.append({
            "solver": missing["solver"], "reuse_id": None,
            "description": missing.get("description", ""),
            "why_needed": missing.get("why_needed", ""), "children": [],
        })
        msg = f"Completeness: added {missing['solver']}"
        print(f"  {msg}")
        trace.append({"depth": 0, "action": "completeness_addition", "narrative": msg})


# ================================================================
# Execute plan against graph
# ================================================================

def execute_plan(items: list, parent_id: str | None, graph: SolverGraph,
                 problem: dict, depth: int, budget: int, trace: list,
                 indent: str) -> int:
    """Execute plan using graph_batch — all operations atomic, no orphans possible."""
    if not items:
        return 0

    # Phase 1: Resolve all nodes (reuse or create) and collect batch operations
    ops = []
    node_log = []  # (node_id, reused, concept, item, depth)

    def resolve_and_collect(plan_items, par_id, d, remaining):
        used = 0
        for item in plan_items:
            if not isinstance(item, dict):
                continue
            if used >= remaining:
                break

            concept = item.get("solver", "")
            reuse_id = item.get("reuse_id")
            desc = item.get("description", "")

            node_id = None
            reused = False

            # Try explicit reuse
            if reuse_id and graph.get_node(reuse_id):
                node_id = reuse_id
                reused = True
                concept = graph.get_node(reuse_id)["concept"]
                ops.append({"action": "invoke", "node_id": node_id,
                            "domain": problem["domain"], "problem_id": problem["id"]})
            else:
                # Semantic search
                matches = graph.semantic_search(f"{concept}: {desc}", limit=1, min_similarity=0.65)
                if matches:
                    node_id = matches[0]["node"]["id"]
                    reused = True
                    concept = matches[0]["node"]["concept"]
                    ops.append({"action": "invoke", "node_id": node_id,
                                "domain": problem["domain"], "problem_id": problem["id"]})
                else:
                    # Create new — use batch index for references
                    create_idx = len(ops)
                    ops.append({"action": "create", "concept": concept, "description": desc,
                                "bounds": item.get("bounds", ""), "not_in_scope": item.get("not_in_scope", ""),
                                "depth": d, "problem_id": problem["id"], "domain": problem["domain"]})

            # Connect to parent
            if par_id:
                if node_id:  # known ID
                    ops.append({"action": "connect", "source": par_id, "target": node_id,
                                "problem_id": problem["id"]})
                else:  # new node, use reference
                    ops.append({"action": "connect", "source": par_id, "target": f"${create_idx}.id",
                                "problem_id": problem["id"]})

            # For new nodes, we need the ID after batch executes
            # For reused nodes, we have it now
            final_id = node_id  # may be None for new nodes (resolved after batch)
            # Keep the create operation's index, not the following connect index,
            # so the saved trace can recover the new node's actual ID.
            node_log.append((final_id, reused, concept, item, d, create_idx if not node_id else -1))
            used += 1

            # Recurse into children
            children = item.get("children", [])
            if children and d < MAX_DEPTH:
                child_parent = node_id if node_id else f"${create_idx}.id"
                sub_used = resolve_and_collect(children, child_parent, d + 1, remaining - used)
                used += sub_used

        return used

    budget_used = resolve_and_collect(items, parent_id, depth, budget)

    # Phase 2: Execute batch atomically
    result = graph.batch(ops, commit_message=f"Problem #{problem['id']}: {problem['problem'][:50]}")

    if result.get("orphans_removed"):
        print(f"  [batch] Removed {len(result['orphans_removed'])} orphan(s)")

    # Phase 3: Log results
    for final_id, reused, concept, item, d, create_op_idx in node_log:
        # Resolve ID for new nodes from batch results
        if final_id is None and create_op_idx >= 0:
            batch_result = result["results"][create_op_idx] if create_op_idx < len(result.get("results", [])) else {}
            final_id = batch_result.get("id", "?")

        action = "reused" if reused else "created"
        symbol = "♻" if reused else "✦"
        node = graph.get_node(final_id) if final_id else None
        why = item.get("why_needed", "")
        domains_note = f" ({node['times_invoked']}x, {len(node['domains_served'])}dom)" if node and reused else ""
        print(f"{indent}{'    ' * max(0, d - depth)}{symbol} {concept} [{action}]{domains_note}")
        if why:
            print(f"{indent}{'    ' * max(0, d - depth)}  → {why[:100]}")

        produces = item.get("what_it_produces", "")
        trace.append({
            "depth": d, "node": final_id, "concept": concept,
            "action": action,
            "narrative": f"{concept}: {why}{domains_note}",
            "why_needed": why,
            "what_it_produces": produces,
        })

    return budget_used


# ================================================================
# CALL 4: Batch verify new nodes
# ================================================================

def batch_verify(graph: SolverGraph, new_ids: list[str]):
    if not new_ids:
        return
    nodes = [graph.get_node(nid) for nid in new_ids]
    nodes = [n for n in nodes if n]
    node_list = "\n".join(f"- {n['concept']}: {n['description'][:100]}" for n in nodes)

    result = call_llm(
        f"Solvers:\n{node_list}",
        system='Generate 2-3 test questions per solver. Return JSON: {"verifications": [{"solver": "Name", "test_vectors": ["q1", "q2"]}]}',
        max_tokens=4096
    )
    if not result or not isinstance(result, dict):
        return
    verify_map = {v["solver"]: v.get("test_vectors", []) for v in result.get("verifications", [])}
    for n in nodes:
        vectors = verify_map.get(n["concept"], [])
        if vectors:
            graph.set_test_vectors(n["id"], vectors)


# ================================================================
# Process one problem
# ================================================================

def process_problem(problem: dict, graph: SolverGraph, routing_paths: list):
    budget = random.choice([8, 10, 10, 12, 12, 14, 16, 18, 20, 25])
    print(f"\n{'='*70}")
    print(f"Problem {problem['id']}: {problem['problem']}")
    print(f"Domain: {problem['domain']} | Budget: {budget}")
    print(f"{'='*70}")

    trace = []
    root_id = f"root_{problem['domain']}_{problem['id']}"

    # CALL 1: Plan
    print("  [Planning]")
    plan = plan_problem(problem["problem"], problem["domain"], graph, budget)

    if not plan or "plan" not in plan:
        print("  Plan failed, skipping.")
        trace.append({"depth": 0, "action": "receive", "narrative": f"Plan failed for: {problem['problem']}"})
        routing_paths.append({
            "problem_id": problem["id"], "domain": problem["domain"],
            "problem_text": problem["problem"], "path": [], "trace": trace,
            "budget": budget, "budget_used": 0,
        })
        return

    opening = plan.get("opening_narrative", "")
    closing = plan.get("closing_narrative", "")
    print(f"  {opening}")
    print(f"  Planned {len(plan['plan'])} solvers")
    trace.append({"depth": 0, "action": "receive",
                  "narrative": f"RootSolver: \"{problem['problem']}\" — {opening}"})

    # CALL 2: MVR
    print("  [MVR]")
    plan["plan"] = verify_mvr(plan["plan"], problem["problem"], problem["domain"], budget, trace)

    # CALL 3: Structural verification
    print("  [Structure]")
    structural_verify(plan["plan"], problem["problem"], problem["domain"], trace)

    # Execute
    print("  [Execute]")
    nodes_before = set(n["id"] for n in graph.get_all_nodes())
    budget_used = execute_plan(plan["plan"], None, graph, problem, 1, budget, trace, "  ")
    nodes_after = set(n["id"] for n in graph.get_all_nodes())
    new_ids = list(nodes_after - nodes_before)

    # Restructuring (with seed protection)
    SEED_IDS = {f"solver_{i:04d}" for i in range(1, 7)}  # solver_0001 through solver_0006

    for r in plan.get("restructure", []):
        if not isinstance(r, dict):
            continue
        action = r.get("action", "add_parent")
        why = r.get("why", "")

        if action == "add_parent":
            new_parent = r.get("new_parent", "")
            desc = r.get("description", "")
            children_ids = r.get("children_ids", [])
            # Protect seeds
            children_ids = [c for c in children_ids if c not in SEED_IDS]
            if new_parent and children_ids:
                pid = graph.add_parent(new_parent, desc, children_ids,
                                       problem["id"], problem["domain"])
                if pid:
                    msg = f"Restructure (add_parent): {new_parent} now parents {children_ids}. {why}"
                    print(f"  ↑ {msg}")
                    trace.append({"depth": 0, "action": "restructure", "narrative": msg})

        elif action == "merge":
            keep_id = r.get("keep_id", "")
            absorb_id = r.get("absorb_id", "")
            desc = r.get("description", "")
            if keep_id in SEED_IDS or absorb_id in SEED_IDS:
                print(f"    · Skipped merge: cannot merge seed solvers")
                continue
            if keep_id and absorb_id:
                keep_node = graph.get_node(keep_id)
                absorb_node = graph.get_node(absorb_id)
                if graph.merge_nodes(keep_id, absorb_id, desc):
                    msg = (f"Restructure (merge): {absorb_node['concept'] if absorb_node else absorb_id} "
                           f"absorbed into {keep_node['concept'] if keep_node else keep_id}. {why}")
                    print(f"  ⊕ {msg}")
                    trace.append({"depth": 0, "action": "restructure", "narrative": msg})

        elif action == "split":
            split_id = r.get("split_id", "")
            split_into = r.get("split_into", [])
            if split_id in SEED_IDS:
                print(f"    · Skipped split: cannot split seed solvers")
                continue
            if split_id and split_into:
                split_node = graph.get_node(split_id)
                new_ids = graph.split_node(split_id, split_into,
                                           problem["id"], problem["domain"])
                if new_ids:
                    names = [s["concept"] for s in split_into]
                    msg = (f"Restructure (split): {split_node['concept'] if split_node else split_id} "
                           f"split into {names}. {why}")
                    print(f"  ✂ {msg}")
                    trace.append({"depth": 0, "action": "restructure", "narrative": msg})

    # CALL 4: Verify new nodes
    if new_ids:
        print(f"  [Verify] {len(new_ids)} new nodes")
        batch_verify(graph, new_ids)

    reused = sum(1 for t in trace if t.get("action") == "reused")
    created = sum(1 for t in trace if t.get("action") == "created")
    trace.append({"depth": 0, "action": "complete", "narrative": closing or "Done."})
    trace.append({"depth": 0, "action": "summary",
                  "narrative": f"{created} new, {reused} reused. Budget: {budget_used}/{budget}."})

    print(f"\n  Summary: {created} new, {reused} reused, {budget_used}/{budget}")
    print(f"  Graph: {graph.node_count()} nodes, {graph.edge_count()} edges")

    routing_paths.append({
        "problem_id": problem["id"], "domain": problem["domain"],
        "problem_text": problem["problem"],
        "path": [t for t in trace if t.get("node")],
        "trace": trace, "budget": budget, "budget_used": budget_used,
    })


# ================================================================
# Stats & export
# ================================================================

def compute_stats(graph: SolverGraph, routing_paths: list) -> dict:
    nodes = graph.get_all_nodes()
    highways = sorted(nodes, key=lambda n: n["times_invoked"], reverse=True)
    top_highways = [
        {"concept": n["concept"], "times_invoked": n["times_invoked"],
         "domains": len(n["domains_served"]), "domain_list": n["domains_served"]}
        for n in highways[:30]
    ]
    reuse_curve = []
    for rp in routing_paths:
        path = rp["path"]
        total = len(path)
        reused = sum(1 for p in path if p.get("action") == "reused")
        reuse_pct = reused / total if total > 0 else 0
        reuse_curve.append({
            "problem": rp["problem_id"], "domain": rp["domain"],
            "new_nodes": total - reused, "reused_nodes": reused,
            "reuse_pct": round(reuse_pct, 3),
        })
    window = 10
    rolling_reuse = []
    for i, r in enumerate(reuse_curve):
        start = max(0, i - window + 1)
        avg = sum(w["reuse_pct"] for w in reuse_curve[start:i+1]) / (i - start + 1)
        rolling_reuse.append({"problem": r["problem"], "rolling_avg": round(avg, 3)})

    budget_allocation = [
        {"problem": rp["problem_id"], "budget": rp["budget"], "spent": rp["budget_used"]}
        for rp in routing_paths
    ]
    return {
        "total_nodes": len(nodes), "total_edges": graph.edge_count(),
        "total_reuse_events": sum(r["reused_nodes"] for r in reuse_curve),
        "top_highways": top_highways, "reuse_curve": reuse_curve,
        "rolling_reuse": rolling_reuse, "budget_allocation": budget_allocation,
    }


def save_outputs(graph: SolverGraph, routing_paths: list, script_dir: str):
    # tree.json for visualization
    tree_data = graph.export_tree_json()
    tree_data["routing_paths"] = routing_paths
    tree_data["_node_counter"] = graph.node_count()
    with open(os.path.join(script_dir, "tree.json"), "w") as f:
        json.dump(tree_data, f, indent=2)

    # stats.json
    stats = compute_stats(graph, routing_paths)
    with open(os.path.join(script_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)


# ================================================================
# Main
# ================================================================

UNIVERSAL_SEEDS = [
    ("ScopeSolver",
     "What is the problem? Boundaries, decomposition, framing. Every problem must be defined before it can be solved.",
     "Problem definition, boundary setting, decomposition into sub-problems, framing and reframing, scope management",
     "Solving the problem — only defining what it is and what it is not"),
    ("EvidenceSolver",
     "What do we know? Measurement, diagnosis, verification. Every problem has knowable and unknowable aspects.",
     "Data gathering, diagnostic measurement, baseline assessment, outcome verification, validity testing, progress tracking",
     "Designing solutions — only gathering and verifying information about the current and desired state"),
    ("ConstraintSolver",
     "What limits the solution? Resources, rules, ethics, physics, feasibility, time. Every problem has finite means.",
     "Resource limits, regulatory constraints, ethical boundaries, technical feasibility, administrative capacity, budget, time horizons",
     "Solution design — only the boundaries that the solution must operate within"),
    ("StakeholderSolver",
     "Who is involved and what do they need? Interests, incentives, coordination, legitimacy. Every problem affects people.",
     "Actor identification, interest mapping, incentive design, conflict resolution, coalition building, governance structures, legitimacy",
     "Technical design — only the human and institutional alignment dimension"),
    ("MechanismSolver",
     "How does the solution actually work? Design, causation, structure, implementation. Every solution has a 'how'.",
     "Causal design, system architecture, process design, tool selection, implementation strategy, operational logic",
     "Problem definition or evaluation — only the design of how the solution produces its effect"),
    ("DynamicsSolver",
     "How does the system change over time? Feedback, adaptation, resilience, learning. Every system exists in time.",
     "Feedback loops, adaptation mechanisms, resilience design, learning systems, evolutionary dynamics, monitoring",
     "Initial design — only how the system responds to change after deployment"),
]


def seed_universal_tree(graph: SolverGraph):
    """Initialize the UST: create depth-1 seeds, then decompose each into depth-2 sub-concepts."""
    print("  Seeding Universal Solver Tree...")
    seed_ids = []
    for concept, description, bounds, not_in_scope in UNIVERSAL_SEEDS:
        node_id = graph.create_node(concept, description, bounds=bounds,
                                     not_in_scope=not_in_scope, depth=1,
                                     origin="initial_seed")
        seed_ids.append((node_id, concept, description))
        print(f"    ✦ {concept} [{node_id}]")

    print(f"\n  Decomposing seeds into universal sub-concepts...")
    for node_id, concept, description in seed_ids:
        decompose_seed(graph, node_id, concept, description)

    print(f"\n  UST seeded: {graph.node_count()} nodes, {graph.edge_count()} edges\n")


def decompose_seed(graph: SolverGraph, seed_id: str, concept: str, description: str):
    """Apply the four tests to decompose a universal seed into its sub-concepts."""
    result = call_llm(
        f"""Decompose this universal concept into 3-5 sub-concepts using the four tests:

Concept: {concept}
Description: {description}

The four tests:
1. Necessity: if you removed this sub-concept, would {concept} collapse?
2. Independence: can this sub-concept change without affecting the others?
3. Universality: does EVERY instance of {concept} — in ANY domain — have this dimension?
4. Completeness: do all sub-concepts together fully cover {concept}?

These sub-concepts must be UNIVERSAL — they must apply to economics, education, healthcare,
game design, ecology, music, and every other domain equally.

NAMING: Use clear, descriptive names that a non-expert would understand.
Good: "DiagnosticAssessmentSolver", "OutcomeValidationSolver", "FeedbackRegulationSolver"
Bad: "SinkTopologySolver", "FlowSustenanceSolver", "DifferentialSolver"
The name should tell you WHAT the solver does, not use abstract jargon.

Return ONLY valid JSON:
{{
  "sub_concepts": [
    {{
      "solver": "SomethingSolver",
      "description": "the structural question this sub-concept addresses",
      "bounds": "what is in scope",
      "not_in_scope": "what is excluded",
      "four_tests": "one sentence: why this passes all four tests"
    }}
  ]
}}""",
        system="You are decomposing universal concepts. Think across ALL domains — not just one.",
        max_tokens=4096
    )

    if not result or not isinstance(result, dict) or "sub_concepts" not in result:
        print(f"      Failed to decompose {concept}")
        return

    for sc in result["sub_concepts"]:
        name = sc.get("solver", "")
        desc = sc.get("description", "")
        bounds = sc.get("bounds", desc)
        nis = sc.get("not_in_scope", "")
        if name:
            child_id = graph.create_node(name, desc, bounds=bounds,
                                          not_in_scope=nis, depth=2,
                                          origin="initial_seed")
            graph.add_edge(seed_id, child_id, 0)
            print(f"      ├── {name} [{child_id}]")


def maintenance_pass(graph: SolverGraph, routing_paths: list, checkpoint: int):
    """MetaObserverSolver: diagnose the tree and propose restructuring."""
    diag = graph.diagnose_tree()
    if not diag["issues"]:
        print("  [Maintenance] Tree is healthy.")
        return

    print(f"  [Maintenance] {diag['summary']}")

    # Format issues for LLM
    issues_text = json.dumps(diag["issues"], indent=2)
    skeleton = graph.get_skeleton()

    result = call_llm(
        f"""You are the MetaObserverSolver. The tree has structural issues.
Review each issue and decide what to do.

=== CURRENT TREE ===
{skeleton}

=== DETECTED ISSUES ===
{issues_text}

For each issue, decide: act on it or skip it.
Return JSON:
{{
  "actions": [
    {{
      "action": "merge|add_parent|split|skip",
      "keep_id": "solver_XXXX (for merge)",
      "absorb_id": "solver_YYYY (for merge)",
      "new_parent": "ParentSolverName (for add_parent)",
      "description": "...",
      "children_ids": ["solver_XXXX"] ,
      "split_id": "solver_XXXX (for split)",
      "split_into": [{{"concept": "NameSolver", "description": "..."}}],
      "why": "reasoning"
    }}
  ]
}}""",
        system="You are the MetaObserverSolver. Only act when the evidence is clear. Skip when uncertain. NEVER touch solver_0001 through solver_0006 — these are universal seeds that must remain at depth 1.",
        max_tokens=4096
    )

    if not result or not isinstance(result, dict):
        return

    SEED_IDS = {f"solver_{i:04d}" for i in range(1, 7)}

    for action in result.get("actions", []):
        if not isinstance(action, dict):
            continue
        act = action.get("action", "skip")
        why = action.get("why", "")

        if act == "merge":
            keep_id = action.get("keep_id", "")
            absorb_id = action.get("absorb_id", "")
            if keep_id in SEED_IDS or absorb_id in SEED_IDS:
                print(f"    · Blocked: cannot merge seed solvers")
                continue
            if keep_id and absorb_id:
                keep = graph.get_node(keep_id)
                absorb = graph.get_node(absorb_id)
                if graph.merge_nodes(keep_id, absorb_id, action.get("description", "")):
                    print(f"    ⊕ Merged {absorb['concept'] if absorb else absorb_id} → {keep['concept'] if keep else keep_id}. {why}")

        elif act == "add_parent":
            name = action.get("new_parent", "")
            desc = action.get("description", "")
            children = action.get("children_ids", [])
            if name and children:
                pid = graph.add_parent(
                    name, desc, children, origin="maintenance",
                    created_after_problem=checkpoint
                )
                if pid:
                    print(f"    ↑ Added parent {name} over {children}. {why}")

        elif act == "split":
            split_id = action.get("split_id", "")
            split_into = action.get("split_into", [])
            if split_id and split_into:
                node = graph.get_node(split_id)
                new_ids = graph.split_node(
                    split_id, split_into, origin="maintenance",
                    created_after_problem=checkpoint
                )
                if new_ids:
                    print(f"    ✂ Split {node['concept'] if node else split_id} → {[s['concept'] for s in split_into]}. {why}")

        elif act == "skip":
            print(f"    · Skipped: {why}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "ust.db")

    with open(os.path.join(script_dir, "problems.json")) as f:
        problems = json.load(f)

    # Check for resumption
    routing_path_file = os.path.join(script_dir, "routing_paths.json")
    if os.path.exists(routing_path_file) and os.path.exists(db_path):
        graph = SolverGraph(db_path)
        with open(routing_path_file) as f:
            routing_paths = json.load(f)
        processed_ids = {rp["problem_id"] for rp in routing_paths}
        print(f"Resuming: {len(processed_ids)} problems, {graph.node_count()} nodes")
    else:
        if os.path.exists(db_path):
            os.remove(db_path)
        graph = SolverGraph(db_path)
        routing_paths = []
        processed_ids = set()

    # Seed universal top-level concepts if tree is empty
    if graph.node_count() == 0:
        seed_universal_tree(graph)

    for problem in problems:
        if problem["id"] in processed_ids:
            continue

        for attempt in range(3):
            try:
                process_problem(problem, graph, routing_paths)
                break
            except Exception as e:
                print(f"  [ERROR] Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    print(f"  [SKIP] Problem {problem['id']} skipped after 3 failures")
                    routing_paths.append({
                        "problem_id": problem["id"], "domain": problem["domain"],
                        "problem_text": problem["problem"], "path": [], "trace": [
                            {"depth": 0, "action": "receive", "narrative": f"Failed: {e}"}
                        ], "budget": 0, "budget_used": 0,
                    })

        # Maintenance pass every 10 problems, starting after problem 20 (skip if > 95 to avoid timeout)
        if len(routing_paths) % 10 == 0 and len(routing_paths) >= 20 and len(routing_paths) <= 95:
            print(f"\n{'~'*70}")
            print(f"MAINTENANCE PASS (after {len(routing_paths)} problems)")
            print(f"{'~'*70}")
            maintenance_pass(graph, routing_paths, len(routing_paths))

        # Save after each problem
        with open(routing_path_file, "w") as f:
            json.dump(routing_paths, f, indent=2)
        save_outputs(graph, routing_paths, script_dir)

    print(f"\n{'='*70}")
    print(f"DONE: {graph.node_count()} nodes, {graph.edge_count()} edges")
    stats = compute_stats(graph, routing_paths)
    for h in stats["top_highways"][:10]:
        print(f"  {h['concept']}: {h['times_invoked']}x across {h['domains']} domains")

    graph.close()


if __name__ == "__main__":
    main()
