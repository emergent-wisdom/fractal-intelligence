"""
Solver Graph — SQLite + embeddings for the Universal Solver Tree.

Purpose-built for fractal intelligence prototype:
- Nodes are Solvers with five surfaces
- Edges are parent→child (directed, acyclic)
- Semantic search via sentence-transformers embeddings
- Skeleton view for LLM context
- Restructuring: add parents, re-parent children
"""

import sqlite3
import json
import os
import numpy as np
from typing import Optional

# Lazy-load sentence-transformers (heavy import)
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims, fast
        print("[Graph] Embedding model loaded")
    return _model


def _embed(text: str) -> bytes:
    """Embed text and return as bytes for SQLite storage."""
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32).tobytes()


def _bytes_to_vec(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))  # already normalized


class SolverGraph:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._node_counter = self._get_max_counter()

    _in_batch = False  # When True, individual methods skip commit

    def _commit(self):
        """Commit only if not inside a batch operation."""
        if not self._in_batch:
            self.conn.commit()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                concept TEXT NOT NULL,
                description TEXT,
                bounds TEXT,
                not_in_scope TEXT,
                depth INTEGER DEFAULT 1,
                times_invoked INTEGER DEFAULT 1,
                domains_served TEXT DEFAULT '[]',
                problems_routed TEXT DEFAULT '[]',
                test_vectors TEXT DEFAULT '[]',
                quality_gain REAL DEFAULT 0.5,
                created_by_problem INTEGER,
                embedding BLOB,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                problem_id INTEGER,
                edge_type TEXT DEFAULT 'parent_child',
                FOREIGN KEY (source) REFERENCES nodes(id),
                FOREIGN KEY (target) REFERENCES nodes(id)
            );

            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);
            CREATE INDEX IF NOT EXISTS idx_nodes_concept ON nodes(concept);
        """)
        self._commit()

    def _get_max_counter(self) -> int:
        row = self.conn.execute(
            "SELECT id FROM nodes ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            try:
                return int(row["id"].split("_")[1])
            except (IndexError, ValueError):
                pass
        return 0

    # ================================================================
    # Node operations
    # ================================================================

    def create_node(self, concept: str, description: str, bounds: str = "",
                    not_in_scope: str = "", depth: int = 1,
                    quality_gain: float = 0.5, problem_id: int = 0,
                    domain: str = "", dedup_threshold: float = 0.60,
                    origin: str = "", created_after_problem: int = 0) -> str:
        """Create a solver node with auto-embedding. Returns node ID.

        If a semantically similar node already exists (cosine > dedup_threshold),
        returns the existing node's ID instead of creating a duplicate.
        """
        # Auto-generate bounds from description if not provided
        if not bounds and description:
            bounds = description
        if not not_in_scope and description:
            not_in_scope = "Everything outside the scope described above"

        # Block depth-1 creation after seeding (only seeds live at depth 1)
        if depth == 1 and self._node_counter >= 6:
            print(f"    [blocked] Cannot create depth-1 node '{concept}' — forcing to depth 2")
            depth = 2

        # Dedup check: does a similar node already exist?
        embed_text = f"{concept}: {description}"
        matches = self.semantic_search(embed_text, limit=1, min_similarity=dedup_threshold)
        if matches:
            existing = matches[0]
            print(f"    [dedup] {concept} matches existing {existing['node']['concept']} "
                  f"(sim={existing['similarity']}) — reusing {existing['node']['id']}")
            return existing["node"]["id"]

        self._node_counter += 1
        node_id = f"solver_{self._node_counter:04d}"
        embedding = _embed(embed_text)

        domains = json.dumps([domain] if domain else [])
        problems = json.dumps([problem_id] if problem_id else [])
        if not origin:
            origin = "problem" if problem_id else "unspecified"
        metadata = json.dumps({
            "origin": origin,
            "created_after_problem": created_after_problem,
        })

        self.conn.execute(
            """INSERT INTO nodes (id, concept, description, bounds, not_in_scope,
               depth, times_invoked, domains_served, problems_routed,
               quality_gain, created_by_problem, embedding, metadata)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)""",
            (node_id, concept, description, bounds, not_in_scope,
             depth, domains, problems, quality_gain, problem_id, embedding, metadata)
        )
        self._commit()
        return node_id

    def get_node(self, node_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    def invoke_node(self, node_id: str, domain: str, problem_id: int):
        """Record that a node was invoked (reused) for a problem."""
        node = self.get_node(node_id)
        if not node:
            return

        domains = node["domains_served"]
        if domain not in domains:
            domains.append(domain)

        problems = node["problems_routed"]
        problems.append(problem_id)

        self.conn.execute(
            """UPDATE nodes SET times_invoked = times_invoked + 1,
               domains_served = ?, problems_routed = ? WHERE id = ?""",
            (json.dumps(domains), json.dumps(problems), node_id)
        )
        self._commit()

    def set_test_vectors(self, node_id: str, vectors: list[str]):
        self.conn.execute(
            "UPDATE nodes SET test_vectors = ? WHERE id = ?",
            (json.dumps(vectors), node_id)
        )
        self._commit()

    def update_depth(self, node_id: str, new_depth: int):
        self.conn.execute(
            "UPDATE nodes SET depth = ? WHERE id = ?",
            (new_depth, node_id)
        )
        self._commit()

    # ================================================================
    # Edge operations
    # ================================================================

    def add_edge(self, source: str, target: str, problem_id: int = 0,
                 edge_type: str = "parent_child") -> bool:
        """Add directed edge. Returns False if it would create a cycle or violate seed protection."""
        # Prevent self-loops
        if source == target:
            return False

        # Protect seeds: depth-1 seeds (first 6 nodes) cannot be targets of parent_child edges
        # They must remain root-level
        if edge_type == "parent_child" and target in {f"solver_{i:04d}" for i in range(1, 7)}:
            print(f"    [blocked] Cannot make seed {target} a child of {source}")
            return False

        # Prevent duplicate edges
        existing = self.conn.execute(
            "SELECT 1 FROM edges WHERE source = ? AND target = ?",
            (source, target)
        ).fetchone()
        if existing:
            return True  # already exists, not an error

        # Simple cycle check: can we reach source from target?
        if self._can_reach(target, source):
            return False  # would create cycle

        self.conn.execute(
            "INSERT INTO edges (source, target, problem_id, edge_type) VALUES (?, ?, ?, ?)",
            (source, target, problem_id, edge_type)
        )
        self._commit()
        return True

    def remove_edge(self, source: str, target: str):
        self.conn.execute(
            "DELETE FROM edges WHERE source = ? AND target = ?",
            (source, target)
        )
        self._commit()

    def get_children(self, node_id: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT n.* FROM nodes n
               JOIN edges e ON e.target = n.id
               WHERE e.source = ? AND e.edge_type = 'parent_child'""",
            (node_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_parents(self, node_id: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT n.* FROM nodes n
               JOIN edges e ON e.source = n.id
               WHERE e.target = ? AND e.edge_type = 'parent_child'""",
            (node_id,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def _can_reach(self, from_id: str, to_id: str) -> bool:
        """BFS: can we reach to_id starting from from_id via child edges?"""
        visited = set()
        queue = [from_id]
        while queue:
            current = queue.pop(0)
            if current == to_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            rows = self.conn.execute(
                "SELECT target FROM edges WHERE source = ? AND edge_type = 'parent_child'",
                (current,)
            ).fetchall()
            for row in rows:
                queue.append(row[0])
        return False

    # ================================================================
    # Semantic search
    # ================================================================

    def semantic_search(self, query: str, limit: int = 10,
                        min_similarity: float = 0.3) -> list[dict]:
        """Find nodes most similar to query text by embedding cosine similarity."""
        query_vec = _bytes_to_vec(_embed(query))

        rows = self.conn.execute(
            "SELECT * FROM nodes WHERE embedding IS NOT NULL"
        ).fetchall()

        results = []
        for row in rows:
            node = self._row_to_dict(row)
            node_vec = _bytes_to_vec(row["embedding"])
            sim = _cosine_sim(query_vec, node_vec)
            if sim >= min_similarity:
                results.append({"node": node, "similarity": round(sim, 4)})

        results.sort(key=lambda x: -x["similarity"])
        return results[:limit]

    # ================================================================
    # Restructuring
    # ================================================================

    def add_parent(self, new_concept: str, new_description: str,
                   children_ids: list[str], problem_id: int = 0,
                   domain: str = "", bounds: str = "", not_in_scope: str = "",
                   origin: str = "", created_after_problem: int = 0) -> str:
        """Create a new parent node and re-parent existing children under it.

        - Creates the new parent at min(children depths) - 1
        - Moves children's root edges to go through the new parent
        - Adds parent→child edges
        """
        # Find minimum depth among children
        children = [self.get_node(cid) for cid in children_ids]
        children = [c for c in children if c is not None]
        if not children:
            return ""

        min_depth = min(c["depth"] for c in children)
        parent_depth = max(2, min_depth)  # never depth 1 — seeds are sacred

        # Update children to depth + 1
        for child in children:
            self.update_depth(child["id"], parent_depth + 1)

        # Create parent
        parent_id = self.create_node(
            new_concept, new_description, depth=parent_depth,
            problem_id=problem_id, domain=domain,
            bounds=bounds, not_in_scope=not_in_scope, origin=origin,
            created_after_problem=created_after_problem
        )

        # Remove children's edges from root-level sources
        for child in children:
            # Remove any root_ edges pointing to this child
            self.conn.execute(
                "DELETE FROM edges WHERE target = ? AND source LIKE 'root_%'",
                (child["id"],)
            )

        # Add parent→child edges
        for child in children:
            self.add_edge(parent_id, child["id"], problem_id)

        self._commit()
        return parent_id

    def merge_nodes(self, keep_id: str, absorb_id: str, new_description: str = ""):
        """Merge two solvers into one. The 'keep' node absorbs the 'absorb' node.

        - All edges pointing to/from absorb are redirected to keep
        - Invocation counts and domains are merged
        - Absorb node is deleted
        - Re-embeds the kept node with updated description
        """
        keep = self.get_node(keep_id)
        absorb = self.get_node(absorb_id)
        if not keep or not absorb:
            return False

        # Merge feedback data
        domains = list(set(keep["domains_served"] + absorb["domains_served"]))
        problems = keep["problems_routed"] + absorb["problems_routed"]
        total_invocations = keep["times_invoked"] + absorb["times_invoked"]

        # Update description if provided
        desc = new_description or keep["description"]

        # Re-embed with merged description
        embed_text = f"{keep['concept']}: {desc}"
        embedding = _embed(embed_text)

        self.conn.execute(
            """UPDATE nodes SET description = ?, times_invoked = ?,
               domains_served = ?, problems_routed = ?, embedding = ?
               WHERE id = ?""",
            (desc, total_invocations, json.dumps(domains),
             json.dumps(problems), embedding, keep_id)
        )

        # Redirect all edges from absorb to keep
        self.conn.execute(
            "UPDATE edges SET source = ? WHERE source = ?",
            (keep_id, absorb_id)
        )
        self.conn.execute(
            "UPDATE edges SET target = ? WHERE target = ?",
            (keep_id, absorb_id)
        )

        # Remove self-loops created by redirect
        self.conn.execute(
            "DELETE FROM edges WHERE source = target"
        )

        # Remove duplicate edges
        self.conn.execute("""
            DELETE FROM edges WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM edges GROUP BY source, target, edge_type
            )
        """)

        # Delete absorbed node
        self.conn.execute("DELETE FROM nodes WHERE id = ?", (absorb_id,))
        self._commit()
        return True

    def split_node(self, node_id: str, new_concepts: list[dict],
                   problem_id: int = 0, domain: str = "", origin: str = "",
                   created_after_problem: int = 0) -> list[str]:
        """Split a solver into multiple more specific solvers.

        Each entry in new_concepts: {"concept": "Name", "description": "..."}
        The original node is kept as the parent of the new nodes.
        Children of the original are reassigned to the most semantically similar new node.
        """
        original = self.get_node(node_id)
        if not original:
            return []

        new_ids = []
        for nc in new_concepts:
            nid = self.create_node(
                nc.get("concept", nc.get("solver", "UnknownSolver")), nc.get("description", ""),
                depth=original["depth"] + 1,
                problem_id=problem_id, domain=domain, origin=origin,
                created_after_problem=created_after_problem
            )
            self.add_edge(node_id, nid, problem_id)
            new_ids.append(nid)

        # Reassign existing children to the most similar new node
        old_children = self.get_children(node_id)
        for child in old_children:
            if child["id"] in new_ids:
                continue  # skip the new nodes themselves

            # Find most similar new node by embedding
            child_text = f"{child['concept']}: {child['description']}"
            child_vec = _bytes_to_vec(_embed(child_text))

            best_id = None
            best_sim = -1
            for nid in new_ids:
                row = self.conn.execute(
                    "SELECT embedding FROM nodes WHERE id = ?", (nid,)
                ).fetchone()
                if row and row["embedding"]:
                    sim = _cosine_sim(child_vec, _bytes_to_vec(row["embedding"]))
                    if sim > best_sim:
                        best_sim = sim
                        best_id = nid

            if best_id:
                # Remove old edge from parent to child
                self.remove_edge(node_id, child["id"])
                # Add new edge from new node to child
                self.add_edge(best_id, child["id"], problem_id)

        self._commit()
        return new_ids

    # ================================================================
    # Skeleton view
    # ================================================================

    def get_skeleton(self, max_depth: int = 3) -> str:
        """Compact tree view of the UST for LLM context.
        Shows node names, invocation counts, domain counts, and tree structure."""
        all_nodes = self.get_all_nodes()
        if not all_nodes:
            return "Empty graph. No solvers exist yet."

        # Build parent→children map
        edges = self.conn.execute(
            "SELECT source, target FROM edges WHERE edge_type = 'parent_child'"
        ).fetchall()

        children_map = {}
        has_parent = set()
        for e in edges:
            children_map.setdefault(e[0], []).append(e[1])
            has_parent.add(e[1])

        # Root nodes = no parent
        roots = [n for n in all_nodes if n["id"] not in has_parent]
        roots.sort(key=lambda x: -x["times_invoked"])

        node_map = {n["id"]: n for n in all_nodes}

        lines = [f"Universal Solver Tree: {len(all_nodes)} solvers"]

        def render(node_id, depth, prefix=""):
            if depth > max_depth:
                return
            n = node_map.get(node_id)
            if not n:
                return
            inv = n["times_invoked"]
            dc = len(n["domains_served"])
            lines.append(f"{prefix}{n['concept']} [{n['id']}] {inv}x {dc}dom")
            kids = children_map.get(node_id, [])
            kids_sorted = sorted(kids,
                key=lambda x: -node_map.get(x, {}).get("times_invoked", 0))
            for kid in kids_sorted:
                render(kid, depth + 1, prefix + "  ")

        for root in roots[:40]:  # show top 40 root branches
            render(root["id"], 1, "  ")

        remaining = len(roots) - 40
        if remaining > 0:
            lines.append(f"  ... and {remaining} more branches")

        return "\n".join(lines)

    def get_node_detail(self, node_id: str) -> str:
        """Full detail view of a single node for LLM inspection."""
        node = self.get_node(node_id)
        if not node:
            return f"[{node_id}] NOT FOUND"

        children = self.get_children(node_id)
        parents = self.get_parents(node_id)

        child_str = ", ".join(f"{c['concept']}({c['times_invoked']}x)" for c in children)
        parent_str = ", ".join(f"{p['concept']}" for p in parents)

        return (
            f"[{node['id']}] {node['concept']}\n"
            f"  Description: {node['description']}\n"
            f"  Bounds: {node['bounds']}\n"
            f"  Not in scope: {node['not_in_scope']}\n"
            f"  Invoked: {node['times_invoked']}x across {len(node['domains_served'])} domains: "
            f"{', '.join(node['domains_served'][:10])}\n"
            f"  Depth: {node['depth']}\n"
            f"  Parents: {parent_str or 'root'}\n"
            f"  Children: {child_str or 'none (leaf)'}\n"
            f"  Test vectors: {'; '.join(node['test_vectors'])}"
        )

    # ================================================================
    # Atomic batch operations
    # ================================================================

    def batch(self, operations: list[dict], commit_message: str = "") -> dict:
        """Execute multiple graph operations atomically.

        Pattern from understanding-graph:
        1. Pre-validate: check no orphans will be created
        2. Execute: run operations, resolve $N.field references
        3. Post-validate: clean up any orphans
        4. Single commit at end

        Each operation: {"action": "create|connect|invoke|merge|split|add_parent|delete_edge", ...params}
        Variable references: "$0.id" refers to the id from operation 0's result.
        """
        results = []
        created_node_ids = []
        errors = []

        # PRE-VALIDATION: check that every create has a corresponding connect
        create_indices = []
        connect_targets = set()
        for i, op in enumerate(operations):
            action = op.get("action", "")
            if action == "create":
                create_indices.append(i)
            elif action == "connect":
                target = op.get("target", "")
                connect_targets.add(target)
                # Also catch $N.id references
                if target.startswith("$"):
                    import re
                    m = re.match(r'^\$(\d+)\.id$', target)
                    if m:
                        connect_targets.add(f"${m.group(1)}")

        for ci in create_indices:
            ref = f"${ci}"
            ref_id = f"${ci}.id"
            # Check if there's a connect that references this create
            has_connect = ref_id in connect_targets or ref in connect_targets
            # Also check if it's a seed (seeds don't need connects)
            if not has_connect:
                # Check if any connect uses this as source (parent creating children is ok)
                is_source = any(
                    op.get("action") == "connect" and
                    (op.get("source", "") == ref_id or op.get("source", "") == f"${ci}.id")
                    for op in operations
                )
                if not is_source and self.node_count() > 0:
                    # Allow if it's connecting to an existing node as source
                    pass  # We'll catch orphans in post-validation

        # EXECUTE
        self._in_batch = True
        try:
            for i, op in enumerate(operations):
                try:
                    params = self._resolve_refs(op, results)
                    action = params.pop("action")

                    if action == "create":
                        node_id = self.create_node(**params)
                        results.append({"id": node_id, "action": "create"})
                        created_node_ids.append(node_id)

                    elif action == "connect":
                        ok = self.add_edge(params["source"], params["target"],
                                           params.get("problem_id", 0))
                        results.append({"ok": ok, "action": "connect"})

                    elif action == "invoke":
                        self.invoke_node(params["node_id"], params.get("domain", ""),
                                        params.get("problem_id", 0))
                        results.append({"ok": True, "action": "invoke"})

                    elif action == "merge":
                        ok = self.merge_nodes(params["keep_id"], params["absorb_id"],
                                              params.get("description", ""))
                        results.append({"ok": ok, "action": "merge"})

                    elif action == "split":
                        new_ids = self.split_node(params["node_id"], params["into"],
                                                  params.get("problem_id", 0),
                                                  params.get("domain", ""),
                                                  params.get("origin", ""),
                                                  params.get("created_after_problem", 0))
                        results.append({"ids": new_ids, "action": "split"})

                    elif action == "add_parent":
                        pid = self.add_parent(params["concept"], params.get("description", ""),
                                              params["children_ids"],
                                              params.get("problem_id", 0),
                                              params.get("domain", ""),
                                              params.get("bounds", ""),
                                              params.get("not_in_scope", ""),
                                              params.get("origin", ""),
                                              params.get("created_after_problem", 0))
                        results.append({"id": pid, "action": "add_parent"})

                    elif action == "delete_edge":
                        self.remove_edge(params["source"], params["target"])
                        results.append({"ok": True, "action": "delete_edge"})

                    else:
                        raise ValueError(f"Unknown action: {action}")

                except Exception as e:
                    errors.append({"index": i, "action": op.get("action"), "error": str(e)})
                    results.append({"error": str(e), "action": op.get("action")})

            # POST-VALIDATION: check for orphan nodes created in this batch
            seed_ids = {f"solver_{i:04d}" for i in range(1, 7)}
            edge_set = set()
            for e in self.get_all_edges():
                edge_set.add(e["source"])
                edge_set.add(e["target"])

            orphans = []
            for nid in created_node_ids:
                if nid in seed_ids:
                    continue
                if nid not in edge_set:
                    orphans.append(nid)
                    # Archive the orphan
                    self.conn.execute("DELETE FROM nodes WHERE id = ?", (nid,))
                    print(f"    [orphan removed] {nid}")

            # COMMIT — batch always commits directly
            self.conn.commit()

            return {
                "success": len(errors) == 0 and len(orphans) == 0,
                "results": results,
                "errors": errors if errors else None,
                "orphans_removed": orphans if orphans else None,
                "commit_message": commit_message,
            }

        finally:
            self._in_batch = False

    def _resolve_refs(self, op: dict, results: list[dict]) -> dict:
        """Resolve $N.field references in operation params."""
        resolved = {}
        for key, value in op.items():
            if isinstance(value, str) and value.startswith("$"):
                import re
                m = re.match(r'^\$(\d+)\.(\w+)$', value)
                if m:
                    idx, field = int(m.group(1)), m.group(2)
                    if idx < len(results):
                        resolved[key] = results[idx][field]
                    else:
                        raise ValueError(f"Reference {value}: only {len(results)} results")
                else:
                    resolved[key] = value
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_refs({"_": v}, results)["_"] if isinstance(v, str) and v.startswith("$")
                    else v for v in value
                ]
            else:
                resolved[key] = value
        return resolved

    # ================================================================
    # Graph analytics (ported from understanding-graph)
    # ================================================================

    def _to_networkx(self):
        """Build a NetworkX graph from the SQLite data."""
        import networkx as nx
        G = nx.DiGraph()
        for n in self.get_all_nodes():
            G.add_node(n["id"], **{k: v for k, v in n.items() if k != "embedding"})
        for e in self.get_all_edges():
            G.add_edge(e["source"], e["target"], **e)
        return G

    def detect_communities(self) -> dict[int, list[dict]]:
        """Louvain community detection. Returns {community_id: [nodes]}."""
        import networkx as nx
        from networkx.algorithms.community import louvain_communities
        G = self._to_networkx().to_undirected()
        if G.number_of_nodes() == 0:
            return {}
        communities = louvain_communities(G, resolution=1.0)
        result = {}
        node_map = {n["id"]: n for n in self.get_all_nodes()}
        for i, comm in enumerate(communities):
            result[i] = [node_map[nid] for nid in comm if nid in node_map]
        return result

    def get_importance(self) -> list[dict]:
        """PageRank importance scoring. Returns nodes sorted by importance."""
        import networkx as nx
        G = self._to_networkx()
        if G.number_of_nodes() == 0:
            return []
        pr = nx.pagerank(G, alpha=0.85)
        node_map = {n["id"]: n for n in self.get_all_nodes()}
        results = [{"node": node_map[nid], "importance": round(score, 4)}
                    for nid, score in pr.items() if nid in node_map]
        results.sort(key=lambda x: -x["importance"])
        return results

    def link_prediction_score(self, node_id1: str, node_id2: str) -> dict:
        """Link prediction using multiple metrics."""
        import networkx as nx
        G = self._to_networkx().to_undirected()
        if not G.has_node(node_id1) or not G.has_node(node_id2):
            return {"combined": 0}

        # Common neighbors
        cn = len(list(nx.common_neighbors(G, node_id1, node_id2)))

        # Jaccard
        n1 = set(G.neighbors(node_id1))
        n2 = set(G.neighbors(node_id2))
        union = n1 | n2
        jac = len(n1 & n2) / len(union) if union else 0

        # Adamic-Adar
        aa = sum(1.0 / max(np.log(G.degree(w)), 0.01)
                 for w in nx.common_neighbors(G, node_id1, node_id2))

        # Preferential attachment
        pa = G.degree(node_id1) * G.degree(node_id2)
        pa_norm = min(pa / 400, 1)

        combined = 0.4 * min(aa / 3, 1) + 0.3 * jac + 0.2 * min(cn / 5, 1) + 0.1 * pa_norm

        return {
            "common_neighbors": cn, "jaccard": round(jac, 3),
            "adamic_adar": round(aa, 3), "preferential_attachment": pa,
            "combined": round(combined, 3),
        }

    def spreading_activation(self, seed_ids: list[str], decay: float = 0.5,
                              max_steps: int = 3) -> list[dict]:
        """Propagate activation energy from seed nodes through the graph.
        Returns nodes ranked by activation energy — use for finding relevant
        solvers for a new problem."""
        G = self._to_networkx().to_undirected()
        activation = {}

        # Initialize seeds
        for sid in seed_ids:
            if G.has_node(sid):
                activation[sid] = {"energy": 1.0, "depth": 0, "source": sid}

        # Spread
        for step in range(max_steps):
            current = [(nid, data) for nid, data in activation.items() if data["depth"] == step]
            for nid, data in current:
                neighbors = list(G.neighbors(nid))
                spread = (data["energy"] * decay) / max(len(neighbors), 1)
                for neighbor in neighbors:
                    if neighbor not in activation:
                        activation[neighbor] = {"energy": spread, "depth": step + 1, "source": data["source"]}
                    else:
                        activation[neighbor]["energy"] += spread

        node_map = {n["id"]: n for n in self.get_all_nodes()}
        results = [{"node": node_map[nid], "activation": round(data["energy"], 4), "depth": data["depth"]}
                    for nid, data in activation.items() if nid in node_map and nid not in seed_ids]
        results.sort(key=lambda x: -x["activation"])
        return results

    def find_semantic_gaps(self, min_similarity: float = 0.7, limit: int = 10) -> list[dict]:
        """Find node pairs with high embedding similarity but no edge.
        These are merge candidates or missing connections."""
        rows = self.conn.execute(
            "SELECT id, concept, embedding FROM nodes WHERE embedding IS NOT NULL"
        ).fetchall()

        # Build edge set
        edge_set = set()
        for e in self.get_all_edges():
            edge_set.add((e["source"], e["target"]))
            edge_set.add((e["target"], e["source"]))

        gaps = []
        for i, r1 in enumerate(rows):
            v1 = _bytes_to_vec(r1["embedding"])
            for r2 in rows[i+1:]:
                if (r1["id"], r2["id"]) in edge_set:
                    continue
                v2 = _bytes_to_vec(r2["embedding"])
                sim = _cosine_sim(v1, v2)
                if sim >= min_similarity:
                    gaps.append({
                        "node_a": {"id": r1["id"], "concept": r1["concept"]},
                        "node_b": {"id": r2["id"], "concept": r2["concept"]},
                        "similarity": round(sim, 3),
                    })
        gaps.sort(key=lambda x: -x["similarity"])
        return gaps[:limit]

    def suggest_edges(self, limit: int = 10) -> list[dict]:
        """Suggest edges using link prediction + embedding similarity.
        High structural support + high semantic similarity = strong suggestion.
        High structural support + LOW semantic similarity = surprising bridge."""
        all_nodes = self.get_all_nodes()
        if len(all_nodes) < 4:
            return []

        edge_set = set()
        for e in self.get_all_edges():
            edge_set.add((e["source"], e["target"]))
            edge_set.add((e["target"], e["source"]))

        rows = self.conn.execute(
            "SELECT id, concept, embedding FROM nodes WHERE embedding IS NOT NULL"
        ).fetchall()
        node_map = {n["id"]: n for n in all_nodes}

        suggestions = []
        for i, r1 in enumerate(rows):
            for r2 in rows[i+1:]:
                if (r1["id"], r2["id"]) in edge_set:
                    continue

                lp = self.link_prediction_score(r1["id"], r2["id"])
                if lp["combined"] < 0.05:
                    continue

                v1 = _bytes_to_vec(r1["embedding"])
                v2 = _bytes_to_vec(r2["embedding"])
                emb_sim = _cosine_sim(v1, v2)

                # Novelty: high structural support + semantically distant = surprising
                emb_dist = 1 - emb_sim
                if emb_dist > 0.5 and lp["combined"] > 0.2:
                    score = 0.6 * emb_dist + 0.4 * lp["combined"]
                    reason = "Surprising bridge"
                elif emb_sim > 0.5:
                    score = 0.5 * emb_sim + 0.5 * lp["combined"]
                    reason = "Natural connection"
                else:
                    score = lp["combined"]
                    reason = "Structural"

                suggestions.append({
                    "node_a": {"id": r1["id"], "concept": r1["concept"]},
                    "node_b": {"id": r2["id"], "concept": r2["concept"]},
                    "structural_score": lp["combined"],
                    "embedding_similarity": round(emb_sim, 3),
                    "novelty_score": round(score, 3),
                    "reason": reason,
                })

        suggestions.sort(key=lambda x: -x["novelty_score"])
        return suggestions[:limit]

    # ================================================================
    # Tree diagnostics — uses analytics above
    # ================================================================

    def diagnose_tree(self) -> dict:
        """Comprehensive tree health check using graph analytics."""
        all_nodes = self.get_all_nodes()
        if len(all_nodes) < 5:
            return {"issues": [], "summary": "Tree too small for diagnostics."}

        issues = []

        # 1. MERGE CANDIDATES — semantic gaps (high similarity, no edge)
        gaps = self.find_semantic_gaps(min_similarity=0.75, limit=5)
        for gap in gaps:
            issues.append({
                "type": "merge_candidate",
                "node_a": gap["node_a"],
                "node_b": gap["node_b"],
                "similarity": gap["similarity"],
                "reason": f"High semantic similarity ({gap['similarity']}) but not connected.",
            })

        # 2. COMMUNITY-BASED PARENT CANDIDATES
        communities = self.detect_communities()
        # Find communities with multiple root-level nodes that lack a shared parent
        child_ids = set(e["target"] for e in self.get_all_edges() if e.get("edge_type") == "parent_child")
        for comm_id, nodes in communities.items():
            root_nodes_in_comm = [n for n in nodes if n["id"] not in child_ids]
            if len(root_nodes_in_comm) >= 3:
                issues.append({
                    "type": "parent_candidate",
                    "nodes": [{"id": n["id"], "concept": n["concept"]} for n in root_nodes_in_comm],
                    "reason": f"Community of {len(root_nodes_in_comm)} root-level solvers detected by Louvain — they share structural connections and likely need a parent concept.",
                })

        # 3. SPLIT CANDIDATES — high-use nodes with children in non-overlapping domains
        for n in all_nodes:
            if n["times_invoked"] >= 5 and len(n["domains_served"]) >= 3:
                children = self.get_children(n["id"])
                if len(children) >= 4:
                    child_domains = [set(c["domains_served"]) for c in children]
                    # Check pairwise overlap
                    low_overlap = 0
                    total_pairs = 0
                    for ci in range(len(child_domains)):
                        for cj in range(ci+1, len(child_domains)):
                            total_pairs += 1
                            if not child_domains[ci] & child_domains[cj]:
                                low_overlap += 1
                    if total_pairs > 0 and low_overlap / total_pairs > 0.6:
                        issues.append({
                            "type": "split_candidate",
                            "node": {"id": n["id"], "concept": n["concept"]},
                            "children_count": len(children),
                            "domains": n["domains_served"],
                            "reason": f"Has {len(children)} children with low domain overlap — may be doing multiple conceptually distinct jobs.",
                        })

        # 4. SURPRISING BRIDGES — edges that should exist
        bridges = self.suggest_edges(limit=3)
        for b in bridges:
            if b["reason"] == "Surprising bridge":
                issues.append({
                    "type": "bridge_suggestion",
                    "node_a": b["node_a"],
                    "node_b": b["node_b"],
                    "reason": f"Structurally supported but semantically distant — may reveal a non-obvious cross-domain connection.",
                })

        # 5. SPRAWL WARNING
        root_count = len([n for n in all_nodes if n["id"] not in child_ids])
        if root_count > 12:
            issues.append({
                "type": "sprawl_warning",
                "root_count": root_count,
                "reason": f"{root_count} root-level solvers — tree is too flat.",
            })

        summary_parts = []
        for t in ["merge_candidate", "parent_candidate", "split_candidate", "bridge_suggestion", "sprawl_warning"]:
            count = sum(1 for i in issues if i["type"] == t)
            if count:
                summary_parts.append(f"{count} {t.replace('_', ' ')}s")

        return {
            "issues": issues,
            "summary": f"Found: {', '.join(summary_parts)}" if summary_parts else "Tree looks healthy.",
        }

    # ================================================================
    # Stats & export
    # ================================================================

    def get_all_nodes(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM nodes").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_all_edges(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM edges").fetchall()
        return [dict(r) for r in rows]

    def node_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def edge_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    def export_tree_json(self) -> dict:
        """Export to tree.json format for the visualization."""
        nodes = self.get_all_nodes()
        edges = self.get_all_edges()

        vis_nodes = []
        for n in nodes:
            vis_nodes.append({
                "id": n["id"],
                "concept": n["concept"],
                "description": n["description"],
                "depth": n["depth"],
                "parent_ids": [p["id"] for p in self.get_parents(n["id"])],
                "manifest": {"bounds": n["bounds"], "not_in_scope": n["not_in_scope"]},
                "execute": {"status": "simulated", "approach_summary": ""},
                "consult": {"estimated_quality_gain": n["quality_gain"],
                            "estimated_cost": 0, "should_decompose": False},
                "verify": {"test_vectors": n["test_vectors"]},
                "feedback": {
                    "times_invoked": n["times_invoked"],
                    "domains_served": n["domains_served"],
                    "problems_routed": n["problems_routed"],
                    "success_rate": None,
                },
                "children": [c["id"] for c in self.get_children(n["id"])],
                "created_by_problem": n["created_by_problem"],
                "created_at_step": n["created_by_problem"],
                "origin": n["metadata"].get("origin", "legacy"),
                "created_after_problem": n["metadata"].get("created_after_problem", 0),
            })

        vis_edges = [
            {"source": e["source"], "target": e["target"],
             "problem_id": e["problem_id"]}
            for e in edges
        ]

        return {"nodes": vis_nodes, "edges": vis_edges}

    # ================================================================
    # Internal
    # ================================================================

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        # Parse JSON fields
        for field in ("domains_served", "problems_routed", "test_vectors"):
            if isinstance(d.get(field), str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    d[field] = []
        if isinstance(d.get("metadata"), str):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except json.JSONDecodeError:
                d["metadata"] = {}
        # Remove embedding from dict (large binary)
        d.pop("embedding", None)
        return d

    def close(self):
        self.conn.close()
