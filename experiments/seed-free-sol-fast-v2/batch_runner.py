#!/usr/bin/env python3
"""Fast, root-first Fractal Intelligence graph construction.

One model call decomposes Problem Solving itself beneath a universal root.
Subsequent calls process ordered problem batches by climbing from each concrete
problem to that root before traversing downward. The model owns semantic
judgment; this controller enforces the declared abstraction movement and graph
integrity.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_PROBLEMS = REPO / "prototype" / "problems.json"
PROMPT_FILE = HERE / "BATCH_PROMPT.md"
SCHEMA_FILE = HERE / "response.schema.json"
TARGET_SECONDS = 30 * 60
ROOT_ID = "solver-0001"


class HarnessError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def fail_unless(condition: bool, message: str) -> None:
    if not condition:
        raise HarnessError(message)


def clip(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def words(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) >= 4
    }


def find_codex(explicit: str | None) -> str:
    candidates = [
        explicit,
        shutil.which("codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise HarnessError("Could not find the Codex CLI; pass --codex PATH")


def empty_graph() -> dict[str, list[dict[str, Any]]]:
    return {"nodes": [], "composition_edges": [], "specialization_edges": []}


def root_node() -> dict[str, Any]:
    return {
        "id": ROOT_ID,
        "name": "RootSolver",
        "kind": "composite",
        "capability": (
            "Resolve any presented problem by locating it within the most general "
            "reusable structure of Problem Solving and routing downward through "
            "a conceptual decomposition."
        ),
        "accepts": (
            "Any situation, question, goal, discrepancy, or opportunity presented "
            "as requiring resolution."
        ),
        "produces": (
            "A bounded resolution synthesized from an abstraction-guided conceptual "
            "decomposition."
        ),
        "boundary": (
            "Owns the complete problem space; descendants expose narrower bounded "
            "capabilities while this node remains the universal ingress."
        ),
        "excludes": "Domain routines and fixed task sequences treated as universal structure.",
        "created_problem": None,
        "created_batch": 0,
        "invocations": [],
        "revisions": [],
    }


def root_graph() -> dict[str, list[dict[str, Any]]]:
    graph = empty_graph()
    graph["nodes"].append(root_node())
    return graph


def graph_counts(graph: dict[str, Any]) -> dict[str, int]:
    return {
        "nodes": len(graph["nodes"]),
        "composition_edges": len(graph["composition_edges"]),
        "specialization_edges": len(graph["specialization_edges"]),
    }


def node_by_id(graph: dict[str, Any], node_id: str) -> dict[str, Any]:
    for node in graph["nodes"]:
        if node["id"] == node_id:
            return node
    raise HarnessError(f"unknown node reference: {node_id}")


def resolve_ref(graph: dict[str, Any], temporary: dict[str, str], ref: str) -> str:
    if ref in temporary:
        return temporary[ref]
    node_by_id(graph, ref)
    return ref


def add_node(
    graph: dict[str, Any],
    temporary: dict[str, str],
    proposal: dict[str, Any],
    *,
    problem_id: int | None,
    batch_number: int,
) -> str:
    temp_id = proposal["temp_id"].strip()
    name = proposal["name"].strip()
    fail_unless(temp_id and temp_id not in temporary, f"duplicate/empty temp_id: {temp_id!r}")
    fail_unless(name, "node name must not be empty")
    existing_names = {node["name"].casefold() for node in graph["nodes"]}
    fail_unless(name.casefold() not in existing_names, f"duplicate node name: {name}")

    node_id = f"solver-{len(graph['nodes']) + 1:04d}"
    node = {
        "id": node_id,
        "name": name,
        "kind": proposal["kind"],
        "capability": proposal["capability"].strip(),
        "accepts": proposal["accepts"].strip(),
        "produces": proposal["produces"].strip(),
        "boundary": proposal["boundary"].strip(),
        "excludes": proposal["excludes"].strip(),
        "created_problem": problem_id,
        "created_batch": batch_number,
        "invocations": [],
        "revisions": [],
    }
    for field in ("capability", "accepts", "produces", "boundary", "excludes"):
        fail_unless(node[field], f"{name}: {field} must not be empty")
    graph["nodes"].append(node)
    temporary[temp_id] = node_id
    return node_id


def add_or_reuse_identical_node(
    graph: dict[str, Any],
    temporary: dict[str, str],
    proposal: dict[str, Any],
    *,
    problem_id: int | None,
    batch_number: int,
) -> str:
    temp_id = proposal["temp_id"].strip()
    if temp_id not in temporary:
        return add_node(
            graph,
            temporary,
            proposal,
            problem_id=problem_id,
            batch_number=batch_number,
        )
    node = node_by_id(graph, temporary[temp_id])
    fields = ("name", "kind", "capability", "accepts", "produces", "boundary", "excludes")
    fail_unless(
        all(node[field] == proposal[field].strip() for field in fields),
        f"temp_id {temp_id} was redeclared with a different contract",
    )
    return node["id"]


def existing_edge(
    graph: dict[str, Any], kind: str, parent: str, child: str
) -> dict[str, Any] | None:
    key = f"{kind}_edges"
    endpoint_name = "child" if kind == "composition" else "member"
    for edge in graph[key]:
        if edge["parent"] == parent and edge[endpoint_name] == child:
            return edge
    return None


def edge_child(edge: dict[str, Any], kind: str) -> str:
    return edge["child" if kind == "composition" else "member"]


def relation_between(
    graph: dict[str, Any], parent: str, child: str
) -> tuple[str, dict[str, Any]] | None:
    for kind in ("composition", "specialization"):
        edge = existing_edge(graph, kind, parent, child)
        if edge is not None:
            return kind, edge
    return None


def path_exists(graph: dict[str, Any], start: str, target: str) -> bool:
    adjacency = {node["id"]: [] for node in graph["nodes"]}
    for edge in graph["composition_edges"]:
        adjacency[edge["parent"]].append(edge["child"])
    for edge in graph["specialization_edges"]:
        adjacency[edge["parent"]].append(edge["member"])
    pending = [start]
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current not in seen:
            seen.add(current)
            pending.extend(adjacency[current])
    return False


def add_edge(
    graph: dict[str, Any],
    *,
    kind: str,
    parent: str,
    child: str,
    role: str,
    problem_id: int | None,
) -> str:
    fail_unless(kind in {"composition", "specialization"}, f"unknown edge kind: {kind}")
    fail_unless(role.strip(), f"empty {kind} role for {parent} -> {child}")
    fail_unless(parent != child, f"self-edge at {parent}")
    node_by_id(graph, parent)
    node_by_id(graph, child)
    prior = existing_edge(graph, kind, parent, child)
    if prior:
        prior.setdefault("observed_problems", [])
        if problem_id is not None and problem_id not in prior["observed_problems"]:
            prior["observed_problems"].append(problem_id)
        return "observed"

    other = relation_between(graph, parent, child)
    if other is not None:
        raise HarnessError(
            f"conflicting edge kinds for {parent} -> {child}: {other[0]} and {kind}"
        )

    if path_exists(graph, child, parent):
        return "cycle_skipped"

    edge_count = len(graph["composition_edges"]) + len(graph["specialization_edges"])
    edge = {
        "id": f"edge-{edge_count + 1:04d}",
        "parent": parent,
        "role" if kind == "composition" else "dispatch_basis": role.strip(),
        "first_problem": problem_id,
        "observed_problems": [] if problem_id is None else [problem_id],
    }
    edge["child" if kind == "composition" else "member"] = child
    graph[f"{kind}_edges"].append(edge)
    return "added"


def validate_acyclic(graph: dict[str, Any]) -> None:
    adjacency = {node["id"]: [] for node in graph["nodes"]}
    for edge in graph["composition_edges"]:
        adjacency[edge["parent"]].append(edge["child"])
    for edge in graph["specialization_edges"]:
        adjacency[edge["parent"]].append(edge["member"])

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise HarnessError(f"topology cycle reaches {node_id}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in adjacency[node_id]:
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in adjacency:
        visit(node_id)


def validate_graph(graph: dict[str, Any]) -> None:
    ids = [node["id"] for node in graph["nodes"]]
    names = [node["name"].casefold() for node in graph["nodes"]]
    fail_unless(len(ids) == len(set(ids)), "duplicate stable node ID")
    fail_unless(len(names) == len(set(names)), "duplicate stable node name")
    typed_pairs: set[tuple[str, str, str]] = set()
    relation_kinds: dict[tuple[str, str], str] = {}
    for kind, key, endpoint in (
        ("composition", "composition_edges", "child"),
        ("specialization", "specialization_edges", "member"),
    ):
        for edge in graph[key]:
            node_by_id(graph, edge["parent"])
            node_by_id(graph, edge[endpoint])
            pair = (edge["parent"], edge[endpoint])
            prior_kind = relation_kinds.get(pair)
            fail_unless(
                prior_kind is None or prior_kind == kind,
                f"conflicting edge kinds for {pair[0]} -> {pair[1]}: {prior_kind} and {kind}",
            )
            relation_kinds[pair] = kind
            typed_pair = (kind, *pair)
            fail_unless(typed_pair not in typed_pairs, f"duplicate typed edge {typed_pair}")
            typed_pairs.add(typed_pair)
    validate_acyclic(graph)


def validate_rooted(graph: dict[str, Any]) -> None:
    """Require one universal root and make every persistent node reachable from it."""
    node_by_id(graph, ROOT_ID)
    incoming = {node["id"]: 0 for node in graph["nodes"]}
    adjacency = {node["id"]: [] for node in graph["nodes"]}
    for kind, key in (("composition", "composition_edges"), ("specialization", "specialization_edges")):
        for edge in graph[key]:
            child = edge_child(edge, kind)
            incoming[child] += 1
            adjacency[edge["parent"]].append(child)
    roots = [node_id for node_id, count in incoming.items() if count == 0]
    fail_unless(roots == [ROOT_ID], f"expected only {ROOT_ID} at graph root, found {roots}")
    reachable: set[str] = set()
    pending = [ROOT_ID]
    while pending:
        current = pending.pop()
        if current not in reachable:
            reachable.add(current)
            pending.extend(adjacency[current])
    missing = sorted(set(adjacency) - reachable)
    fail_unless(not missing, f"persistent nodes disconnected from {ROOT_ID}: {missing}")


def bootstrap_root_dimensions(graph: dict[str, Any]) -> list[str]:
    """Direct constitutive dimensions Sol derived before seeing any problem."""
    return [
        edge["child"]
        for edge in graph["composition_edges"]
        if edge["parent"] == ROOT_ID and edge["first_problem"] is None
    ]


def checkpoint(state: dict[str, Any], label: str, problem_id: int | None) -> None:
    state["checkpoints"].append(
        {
            "index": len(state["checkpoints"]),
            "label": label,
            "problem_id": problem_id,
            "counts": graph_counts(state["graph"]),
        }
    )


def apply_edge_proposal(
    graph: dict[str, Any],
    temporary: dict[str, str],
    edge: dict[str, Any],
    *,
    problem_id: int | None,
) -> dict[str, Any]:
    parent_id = resolve_ref(graph, temporary, edge["parent_ref"])
    child_id = resolve_ref(graph, temporary, edge["child_ref"])
    result = add_edge(
        graph,
        kind=edge["kind"],
        parent=parent_id,
        child=child_id,
        role=edge["role"],
        problem_id=problem_id,
    )
    fail_unless(result != "cycle_skipped", f"topology cycle proposed at {parent_id} -> {child_id}")
    return {
        "kind": edge["kind"],
        "parent_id": parent_id,
        "child_id": child_id,
        "role": edge["role"].strip(),
        "rationale": edge["rationale"].strip(),
        "result": result,
    }


def apply_bootstrap(state: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    fail_unless(response["response_type"] == "bootstrap", "expected bootstrap response")
    fail_unless(response["batch_number"] == 0, "bootstrap batch_number must be 0")
    fail_unless(response["cases"] == [], "bootstrap cases must be empty")
    proposed = copy.deepcopy(state)
    graph = proposed["graph"]
    temporary: dict[str, str] = {}
    nodes = response["bootstrap"]["nodes"]
    fail_unless(nodes, "bootstrap must decompose the supplied Problem Solving root")
    for node in nodes:
        add_node(graph, temporary, node, problem_id=None, batch_number=0)
    applied_edges = [
        apply_edge_proposal(graph, temporary, edge, problem_id=None)
        for edge in response["bootstrap"]["edges"]
    ]
    fail_unless(applied_edges, "bootstrap must connect its conceptual decomposition")
    validate_graph(graph)
    validate_rooted(graph)
    proposed["bootstrap_topology"] = {
        "created_node_ids": [temporary[node["temp_id"]] for node in nodes],
        "edges": applied_edges,
        "rationale": response["bootstrap"]["rationale"].strip(),
    }
    checkpoint(proposed, "Sol-derived decomposition of Problem Solving", None)
    return proposed


def apply_case(
    state: dict[str, Any],
    case: dict[str, Any],
    registered: dict[str, Any],
    temporary: dict[str, str],
    batch_number: int,
) -> None:
    graph = state["graph"]
    problem_id = registered["id"]
    fail_unless(case["problem_id"] == problem_id, f"expected problem {problem_id}")

    created_ids = [
        add_node(
            graph,
            temporary,
            node,
            problem_id=problem_id,
            batch_number=batch_number,
        )
        for node in case["new_nodes"]
    ]

    # The model's higher abstractions become persistent before this problem can
    # traverse them. This is the central ordering difference from v1.
    applied_topology_edges = [
        apply_edge_proposal(graph, temporary, edge, problem_id=problem_id)
        for edge in case["topology_edges"]
    ]

    applied_revisions = []
    for revision in case["revisions"]:
        node_id = resolve_ref(graph, temporary, revision["node_ref"])
        fail_unless(node_id != ROOT_ID, "RootSolver's universal contract is fixed for this run")
        node = node_by_id(graph, node_id)
        before = {field: node[field] for field in ("capability", "accepts", "produces", "boundary", "excludes")}
        node["revisions"].append({"problem_id": problem_id, "before": before, "rationale": revision["rationale"]})
        for field in before:
            node[field] = revision[field].strip()
            fail_unless(node[field], f"revision empties {node_id}.{field}")
        applied_revisions.append({"node_id": node_id, "rationale": revision["rationale"]})

    validate_graph(graph)
    validate_rooted(graph)

    invocation_ids: set[str] = set()
    invocation_nodes: dict[str, str] = {}
    applied_invocations = []
    for invocation in case["invocations"]:
        invocation_id = invocation["id"].strip()
        parent_id = invocation["parent_id"].strip()
        edge_kind = invocation["edge_kind"]
        fail_unless(invocation_id and invocation_id not in invocation_ids, f"duplicate invocation {invocation_id}")
        fail_unless(parent_id == "ROOT" or parent_id in invocation_ids, f"invocation {invocation_id} has unknown/later parent {parent_id}")
        node_id = resolve_ref(graph, temporary, invocation["node_ref"])

        if parent_id == "ROOT":
            fail_unless(edge_kind == "root", f"{invocation_id}: ROOT invocation needs edge_kind=root")
            fail_unless(node_id == ROOT_ID, f"{invocation_id}: only {ROOT_ID} may attach to transient ROOT")
            persistent_edge = "root"
        else:
            fail_unless(edge_kind in {"composition", "specialization"}, f"{invocation_id}: non-root invocation needs a typed edge")
            parent_node_id = invocation_nodes[parent_id]
            fail_unless(
                existing_edge(graph, edge_kind, parent_node_id, node_id) is not None,
                f"{invocation_id}: route edge {parent_node_id} -> {node_id} ({edge_kind}) was not declared before descent",
            )
            persistent_edge = add_edge(
                graph,
                kind=edge_kind,
                parent=parent_node_id,
                child=node_id,
                role=invocation["role"],
                problem_id=problem_id,
            )

        invocation_ids.add(invocation_id)
        invocation_nodes[invocation_id] = node_id
        node = node_by_id(graph, node_id)
        action = "create" if node_id in created_ids else "reuse"
        node["invocations"].append(
            {"problem_id": problem_id, "invocation_id": invocation_id, "role": invocation["role"]}
        )
        applied_invocations.append(
            {
                "id": invocation_id,
                "parent_id": parent_id,
                "node_id": node_id,
                "edge_kind": edge_kind,
                "catalog_action": action,
                "role": invocation["role"].strip(),
                "contribution": invocation["contribution"].strip(),
                "persistent_edge": persistent_edge,
            }
        )

    fail_unless(applied_invocations, f"problem {problem_id} has no invocations")
    root_invocations = [item for item in applied_invocations if item["parent_id"] == "ROOT"]
    fail_unless(len(root_invocations) == 1, f"problem {problem_id} must have exactly one ROOT invocation")
    fail_unless(applied_invocations[0]["node_id"] == ROOT_ID, f"problem {problem_id} must traverse {ROOT_ID} first")

    invocation_by_id = {item["id"]: item for item in applied_invocations}
    resolved_ascent = []
    for step in case["abstraction_ascent"]:
        node_id = resolve_ref(graph, temporary, step["node_ref"])
        matching_invocations = [
            item for item in applied_invocations if item["node_id"] == node_id
        ]
        fail_unless(
            len(matching_invocations) == 1,
            f"ascent node {node_id} must have exactly one invocation in problem {problem_id}",
        )
        invocation_id = matching_invocations[0]["id"]
        why = step["why_more_general"].strip()
        effect = step["reframing_effect"].strip()
        fail_unless(why and effect, f"ascent step {invocation_id} needs public abstraction judgment and effect")
        resolved_ascent.append(
            {
                "invocation_id": invocation_id,
                "node_id": node_id,
                "why_more_general": why,
                "reframing_effect": effect,
            }
        )

    fail_unless(len(resolved_ascent) >= 2, f"problem {problem_id} did not climb above its specific capability")
    fail_unless(resolved_ascent[0]["node_id"] != ROOT_ID, f"problem {problem_id} ascent begins too generally")
    fail_unless(resolved_ascent[-1]["node_id"] == ROOT_ID, f"problem {problem_id} ascent does not reach {ROOT_ID}")
    for specific, broader in zip(resolved_ascent, resolved_ascent[1:]):
        specific_invocation = invocation_by_id[specific["invocation_id"]]
        fail_unless(
            specific_invocation["parent_id"] == broader["invocation_id"],
            f"problem {problem_id} ascent is not a direct chain at {specific['invocation_id']}",
        )
        fail_unless(
            specific_invocation["edge_kind"] == "specialization",
            f"problem {problem_id} ascent links must be specialization edges at {specific['invocation_id']}",
        )

    root_invocation_id = root_invocations[0]["id"]
    dimension_invocations = {}
    for dimension_id in bootstrap_root_dimensions(graph):
        matches = [
            item
            for item in applied_invocations
            if item["node_id"] == dimension_id
            and item["parent_id"] == root_invocation_id
            and item["edge_kind"] == "composition"
        ]
        fail_unless(
            matches,
            f"problem {problem_id} bypasses model-derived root dimension {dimension_id}",
        )
        dimension_invocations[dimension_id] = [item["id"] for item in matches]

    specific_invocation_id = resolved_ascent[0]["invocation_id"]
    root_dimensions = set(bootstrap_root_dimensions(graph))
    specific_constituents = [
        item
        for item in applied_invocations
        if item["parent_id"] == specific_invocation_id
        and item["edge_kind"] == "composition"
        and item["node_id"] not in root_dimensions
    ]
    fail_unless(
        len({item["node_id"] for item in specific_constituents}) >= 2,
        f"problem {problem_id} needs at least two conceptual constituents beneath its specific composite",
    )

    validate_graph(graph)
    validate_rooted(graph)
    state["cases"].append(
        {
            "problem_id": problem_id,
            "domain": registered["domain"],
            "problem": registered["problem"],
            "batch_number": batch_number,
            "framing": case["framing"],
            "abstraction_ascent": resolved_ascent,
            "root_dimension_invocations": dimension_invocations,
            "specific_constituent_invocations": [
                item["id"] for item in specific_constituents
            ],
            "topology_edges": applied_topology_edges,
            "invocations": applied_invocations,
            "revisions": applied_revisions,
            "synthesis": case["synthesis"],
            "proposed_solution": case["proposed_solution"],
        }
    )
    checkpoint(state, f"Problem {problem_id}", problem_id)


def apply_batch(
    state: dict[str, Any], response: dict[str, Any], expected: list[dict[str, Any]]
) -> dict[str, Any]:
    batch_number = len(state["batches"]) + 1
    fail_unless(response["response_type"] == "batch", "expected batch response")
    fail_unless(response["batch_number"] == batch_number, f"expected batch_number {batch_number}")
    fail_unless(response["bootstrap"]["nodes"] == [], "batch must not repeat bootstrap nodes")
    fail_unless(response["bootstrap"]["edges"] == [], "batch must not repeat bootstrap edges")
    cases = response["cases"]
    fail_unless([case["problem_id"] for case in cases] == [item["id"] for item in expected], "response problem IDs/order differ from registered batch")
    proposed = copy.deepcopy(state)
    temporary: dict[str, str] = {}
    for case, registered in zip(cases, expected, strict=True):
        apply_case(proposed, case, registered, temporary, batch_number)
    return proposed


def compact_catalog(
    state: dict[str, Any], problems: list[dict[str, Any]], detail_limit: int
) -> dict[str, Any]:
    graph = state["graph"]
    query = words(" ".join(item["problem"] for item in problems))
    scored = []
    for node in graph["nodes"]:
        searchable = words(" ".join((node["name"], node["capability"], node["accepts"], node["produces"])))
        score = len(query & searchable)
        if node["kind"] in {"passive", "abstraction_parent"}:
            score += 2
        if node["id"] == ROOT_ID:
            score += 1000
        score += min(2, len(node["invocations"]) // 2)
        scored.append((score, node["id"], node))
    scored.sort(key=lambda item: (-item[0], item[1]))
    detailed = [item[2] for item in scored[:detail_limit]]
    bootstrap_nodes = [
        node for node in graph["nodes"] if node["created_problem"] is None
    ]
    return {
        "root_node_id": ROOT_ID,
        "required_root_dimensions": bootstrap_root_dimensions(graph),
        "bootstrap_scaffold": [
            {
                field: node[field]
                for field in (
                    "id",
                    "name",
                    "kind",
                    "capability",
                    "accepts",
                    "produces",
                    "boundary",
                    "excludes",
                )
            }
            for node in bootstrap_nodes
        ],
        "counts": graph_counts(graph),
        "node_index": [
            {
                "id": node["id"],
                "name": node["name"],
                "kind": node["kind"],
                "capability": clip(node["capability"], 180),
            }
            for node in graph["nodes"]
        ],
        "detailed_candidates": [
            {field: node[field] for field in ("id", "name", "kind", "capability", "accepts", "produces", "boundary", "excludes")}
            for node in detailed
        ],
        "composition_edges": [
            {field: edge[field] for field in ("parent", "child", "role")}
            for edge in graph["composition_edges"]
        ],
        "specialization_edges": [
            {field: edge[field] for field in ("parent", "member", "dispatch_basis")}
            for edge in graph["specialization_edges"]
        ],
    }


def bootstrap_prompt(base: str) -> str:
    return base + """

## Current task: root-only bootstrap

No concrete problem stream is supplied. `solver-0001` already exists as the
universal Problem Solving root. Apply necessity, independence, universality,
and completeness to derive a compact first-principles decomposition of Problem
Solving itself beneath that root. Recurse where another level adds meaningful
resolution. This is a model-derived initial hypothesis: do not install a
departmental workflow, do not blindly copy either worked example, and do not
treat the paper's General Problem-Solving Protocol as protected truth.

Every proposed node must connect to `solver-0001` through the proposed typed
edges. Composition and specialization are edge properties; a node may organize
both. Passive conceptual routers are allowed where they express a real
abstraction even if they perform no domain work yet. Use no target category
count.

Return `response_type` = `bootstrap`, `batch_number` = 0, proposed non-root
nodes and typed edges in `bootstrap`, an empty `cases` array, and a concise
public summary. Existing root references use `solver-0001`; new nodes use
bootstrap-local `temp_id` references.
"""


def batch_prompt(
    base: str,
    state: dict[str, Any],
    batch_number: int,
    problems: list[dict[str, Any]],
    detail_limit: int,
) -> str:
    catalog = compact_catalog(state, problems, detail_limit)
    payload = {
        "batch_number": batch_number,
        "ordered_problems": problems,
        "current_catalog": catalog,
    }
    return base + f"""

## Current task: problem batch {batch_number}

Before emitting each case, inspect only the current problem and the graph state
available from earlier cases; do not use later problems in the batch as
evidence. Infer any broad non-universal mode of problem solving already
evidenced by that current problem; derive it rather than choosing from a list,
and do not invent sibling modes for which there is no evidence. For every
ascent, distinguish that broad mode from narrower reusable families defined by
the object being shaped, a mechanism, or a recurring constraint.

A specialization may attach directly to `RootSolver` only if its contract
names a broad kind of resolution and contrastively excludes fundamentally
different kinds of problem solving. If it is still a family within such a
mode, ascend again and preserve that family beneath the mode. It is valid for
an evidenced mode to begin with one observed child; no member count justifies
or forbids it. The final step to `RootSolver` may not be justified merely by
saying that Root contains the family or supplies the universal scaffold.

Process all registered problems below in the exact order supplied. Later cases
in this response may use nodes introduced by earlier cases. For each case,
perform the specific-to-root abstraction ascent first. Declare all new nodes and
typed `topology_edges` needed by that judgment; they are installed before the
case's descent. Then invoke `solver-0001` and traverse the exact reverse ascent
chain before branching into constituent dimensions.

Existing catalog nodes use stable `solver-####` references. Every new node uses
a unique batch-local `temp_id`; it becomes available after its declaration and
may be referenced by later cases. An invocation parent must be `ROOT` or an
earlier invocation in that case. Only the first RootSolver invocation may use
`ROOT` and `edge_kind=root`; all other invocation edges must already exist in
the catalog or in that case's `topology_edges` and must name their actual type.

Return `response_type` = `batch`, `batch_number` = {batch_number}, empty arrays
inside `bootstrap`, exactly one case for every ordered problem, and a concise
public summary.

INPUT JSON:
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
"""


def invoke_sol(
    *,
    codex: str,
    model: str,
    effort: str,
    prompt: str,
    output_path: Path,
    timeout_seconds: int,
) -> float:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fi-sol-fast-") as isolated:
        command = [
            codex,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-m",
            model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            "-s",
            "read-only",
            "-C",
            isolated,
            "--output-schema",
            str(SCHEMA_FILE),
            "-o",
            str(output_path),
            "-",
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise HarnessError(f"Sol call exceeded {timeout_seconds} seconds") from error
        duration = time.monotonic() - started
        if completed.returncode != 0:
            diagnostic = clip(completed.stderr or "no diagnostic", 1200)
            raise HarnessError(f"Codex exited {completed.returncode}: {diagnostic}")
    fail_unless(output_path.is_file(), "Codex returned no structured response file")
    return duration


def response_path(run_dir: Path, label: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = run_dir / "responses" / f"{label}-{stamp}.json"
    suffix = 1
    while candidate.exists():
        candidate = run_dir / "responses" / f"{label}-{stamp}-{suffix}.json"
        suffix += 1
    return candidate


def update_metrics(state: dict[str, Any]) -> None:
    batch_times = [batch["duration_seconds"] for batch in state["batches"]]
    bootstrap_time = state.get("bootstrap", {}).get("duration_seconds", 0.0)
    average = sum(batch_times) / len(batch_times) if batch_times else None
    processed = sum(len(batch["problem_ids"]) for batch in state["batches"])
    average_per_problem = sum(batch_times) / processed if processed else None
    projection = (
        bootstrap_time + average_per_problem * len(state["problems"])
        if average_per_problem is not None
        else None
    )
    state["metrics"] = {
        "model_call_seconds_so_far": round(bootstrap_time + sum(batch_times), 3),
        "average_problem_batch_seconds": None if average is None else round(average, 3),
        "average_seconds_per_problem": None if average_per_problem is None else round(average_per_problem, 3),
        "projected_total_seconds": None if projection is None else round(projection, 3),
        "target_total_seconds": TARGET_SECONDS,
        "projection_meets_target": None if projection is None else projection <= TARGET_SECONDS,
    }


def initialize_state(args: argparse.Namespace, problems: list[dict[str, Any]]) -> dict[str, Any]:
    graph = root_graph()
    return {
        "format_version": "seed-free-sol-fast-v2",
        "run_id": args.run_dir.name,
        "root_node_id": ROOT_ID,
        "status": "initialized",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "config": {
            "model": args.model,
            "bootstrap_reasoning_effort": args.bootstrap_effort,
            "batch_reasoning_effort": args.effort,
            "batch_size": args.batch_size,
            "batch_size_history": [
                {"from_problem_index": 0, "batch_size": args.batch_size}
            ],
            "problem_count": len(problems),
            "problem_ids": [item["id"] for item in problems],
            "problem_source": "prototype/problems.json",
            "problem_source_sha256": digest_file(args.problems),
            "semantic_reviews_per_problem": 0,
            "raw_event_traces_saved": False,
        },
        "problems": problems,
        "graph": graph,
        "bootstrap": {},
        "bootstrap_topology": {},
        "cases": [],
        "batches": [],
        "checkpoints": [{"index": 0, "label": "RootSolver only", "problem_id": None, "counts": graph_counts(graph)}],
        "metrics": {},
    }


def check_resume_compatibility(
    state: dict[str, Any], args: argparse.Namespace, selected: list[dict[str, Any]]
) -> None:
    expected = {
        "model": args.model,
        "bootstrap_reasoning_effort": args.bootstrap_effort,
        "batch_reasoning_effort": args.effort,
        "problem_count": len(selected),
        "problem_ids": [item["id"] for item in selected],
        "problem_source_sha256": digest_file(args.problems),
    }
    for key, value in expected.items():
        fail_unless(state["config"][key] == value, f"resume mismatch for {key}: {state['config'][key]!r} != {value!r}")
    fail_unless(
        args.allow_batch_size_change or state["config"]["batch_size"] == args.batch_size,
        f"resume mismatch for batch_size: {state['config']['batch_size']!r} != {args.batch_size!r}",
    )


def relative_to_run(path: Path, run_dir: Path) -> str:
    return str(path.relative_to(run_dir))


def select_problems(
    all_problems: list[dict[str, Any]], args: argparse.Namespace
) -> list[dict[str, Any]]:
    if not args.problem_ids:
        fail_unless(1 <= args.count <= len(all_problems), f"--count must be 1..{len(all_problems)}")
        return all_problems[: args.count]

    try:
        requested = [int(value.strip()) for value in args.problem_ids.split(",") if value.strip()]
    except ValueError as error:
        raise HarnessError("--problem-ids must be a comma-separated integer list") from error
    fail_unless(requested, "--problem-ids is empty")
    fail_unless(len(requested) == len(set(requested)), "--problem-ids contains duplicates")
    by_id = {item["id"]: item for item in all_problems}
    missing = [problem_id for problem_id in requested if problem_id not in by_id]
    fail_unless(not missing, f"unknown problem IDs: {missing}")
    return [by_id[problem_id] for problem_id in requested]


def run(args: argparse.Namespace) -> None:
    all_problems = read_json(args.problems)
    fail_unless(isinstance(all_problems, list), "problem source must be a JSON array")
    selected = select_problems(all_problems, args)
    state_path = args.run_dir / "state.json"
    args.run_dir.mkdir(parents=True, exist_ok=True)
    base_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    codex = find_codex(args.codex)

    if state_path.exists():
        state = read_json(state_path)
        check_resume_compatibility(state, args, selected)
        if state["config"]["batch_size"] != args.batch_size:
            state["config"].setdefault(
                "batch_size_history",
                [{"from_problem_index": 0, "batch_size": state["config"]["batch_size"]}],
            )
            state["config"]["batch_size_history"].append(
                {
                    "from_problem_index": len(state["cases"]),
                    "batch_size": args.batch_size,
                    "changed_at": utc_now(),
                }
            )
            state["config"]["batch_size"] = args.batch_size
            state["updated_at"] = utc_now()
            update_metrics(state)
            atomic_write_json(state_path, state)
    else:
        state = initialize_state(args, selected)
        atomic_write_json(state_path, state)

    if not state["bootstrap"]:
        output = response_path(args.run_dir, "bootstrap")
        print(f"Bootstrap: Sol/{args.bootstrap_effort} (blind to the problem stream)", flush=True)
        duration = invoke_sol(
            codex=codex,
            model=args.model,
            effort=args.bootstrap_effort,
            prompt=bootstrap_prompt(base_prompt),
            output_path=output,
            timeout_seconds=args.timeout,
        )
        response = read_json(output)
        proposed = apply_bootstrap(state, response)
        proposed["bootstrap"] = {
            "duration_seconds": round(duration, 3),
            "response_file": relative_to_run(output, args.run_dir),
            "summary": response["summary"],
            "accepted_at": utc_now(),
        }
        proposed["status"] = "running"
        proposed["updated_at"] = utc_now()
        update_metrics(proposed)
        state = proposed
        atomic_write_json(state_path, state)
        print(f"Bootstrap accepted in {duration:.1f}s: {graph_counts(state['graph'])}", flush=True)

    remaining = state["problems"][len(state["cases"]) :]
    if args.replay_response is not None:
        fail_unless(remaining, "replay requested but the run is already complete")
        current = remaining[: args.batch_size]
        batch_number = len(state["batches"]) + 1
        response = read_json(args.replay_response)
        proposed = apply_batch(state, response, current)
        proposed["batches"].append(
            {
                "batch_number": batch_number,
                "problem_ids": [item["id"] for item in current],
                "duration_seconds": round(args.replay_duration_seconds, 3),
                "response_file": relative_to_run(args.replay_response, args.run_dir),
                "summary": response["summary"],
                "accepted_at": utc_now(),
                "replayed_after_validator_fix": True,
            }
        )
        proposed["status"] = "complete" if len(proposed["cases"]) == len(proposed["problems"]) else "running"
        proposed["updated_at"] = utc_now()
        update_metrics(proposed)
        atomic_write_json(state_path, proposed)
        print(
            f"Replayed batch {batch_number}: {len(proposed['cases'])}/{len(proposed['problems'])} "
            f"problems accepted; graph {graph_counts(proposed['graph'])}",
            flush=True,
        )
        return

    allowed = args.max_new_batches
    completed_now = 0
    while remaining and (allowed is None or completed_now < allowed):
        batch_number = len(state["batches"]) + 1
        current = remaining[: args.batch_size]
        prompt = batch_prompt(base_prompt, state, batch_number, current, args.catalog_detail_limit)
        output = response_path(args.run_dir, f"batch-{batch_number:03d}")
        print(
            f"Batch {batch_number}: problems {','.join(str(item['id']) for item in current)}, "
            f"prompt {len(prompt.encode('utf-8')) / 1024:.1f} KiB",
            flush=True,
        )
        duration = invoke_sol(
            codex=codex,
            model=args.model,
            effort=args.effort,
            prompt=prompt,
            output_path=output,
            timeout_seconds=args.timeout,
        )
        response = read_json(output)
        proposed = apply_batch(state, response, current)
        proposed["batches"].append(
            {
                "batch_number": batch_number,
                "problem_ids": [item["id"] for item in current],
                "duration_seconds": round(duration, 3),
                "response_file": relative_to_run(output, args.run_dir),
                "summary": response["summary"],
                "accepted_at": utc_now(),
            }
        )
        proposed["status"] = "complete" if len(proposed["cases"]) == len(proposed["problems"]) else "running"
        proposed["updated_at"] = utc_now()
        update_metrics(proposed)
        state = proposed
        atomic_write_json(state_path, state)
        projection = state["metrics"]["projected_total_seconds"]
        print(
            f"Batch {batch_number} accepted in {duration:.1f}s; "
            f"projected total {projection / 60:.1f} min; graph {graph_counts(state['graph'])}",
            flush=True,
        )
        completed_now += 1
        remaining = state["problems"][len(state["cases"]) :]

    if not remaining:
        print(f"Complete: {len(state['cases'])} problems in {state['metrics']['model_call_seconds_so_far'] / 60:.1f} model-call minutes", flush=True)
    elif allowed is not None and completed_now >= allowed:
        print(f"Pilot stop: {len(state['cases'])}/{len(state['problems'])} problems accepted. Resume with the same command without --max-new-batches.", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--problem-ids", help="comma-separated IDs; overrides --count")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--allow-batch-size-change", action="store_true", help="record a new checkpoint size when resuming")
    parser.add_argument("--max-new-batches", type=int)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"), default="low", help="reasoning effort for problem batches")
    parser.add_argument("--bootstrap-effort", choices=("low", "medium", "high", "xhigh", "max"), default="medium")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--catalog-detail-limit", type=int, default=120)
    parser.add_argument("--codex")
    parser.add_argument("--replay-response", type=Path, help="apply one saved batch response without another model call")
    parser.add_argument("--replay-duration-seconds", type=float, default=0.0)
    args = parser.parse_args()
    args.run_dir = args.run_dir.resolve()
    args.problems = args.problems.resolve()
    if args.replay_response is not None:
        args.replay_response = args.replay_response.resolve()
        fail_unless(args.replay_response.is_file(), "--replay-response must name an existing file")
        fail_unless(args.replay_duration_seconds >= 0, "--replay-duration-seconds must be non-negative")
    fail_unless(args.batch_size > 0, "--batch-size must be positive")
    fail_unless(args.max_new_batches is None or args.max_new_batches > 0, "--max-new-batches must be positive")
    fail_unless(args.catalog_detail_limit > 0, "--catalog-detail-limit must be positive")
    return args


if __name__ == "__main__":
    try:
        run(parse_args())
    except (HarnessError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error
