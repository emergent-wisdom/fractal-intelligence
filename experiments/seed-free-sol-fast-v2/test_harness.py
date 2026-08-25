import copy
import unittest

import batch_runner as harness


def node(temp_id: str, name: str, kind: str = "composite") -> dict:
    return {
        "temp_id": temp_id,
        "name": name,
        "kind": kind,
        "capability": f"Provide the bounded {name} capability.",
        "accepts": f"Inputs requiring {name}.",
        "produces": f"A {name} result.",
        "boundary": f"Owns {name} and nothing broader.",
        "excludes": "Unrelated work.",
    }


def edge(kind: str, parent: str, child: str, role: str = "typed role") -> dict:
    return {
        "kind": kind,
        "parent_ref": parent,
        "child_ref": child,
        "role": role,
        "rationale": "This declared relation is needed by the conceptual structure.",
    }


def initial_state() -> dict:
    return {
        "graph": harness.root_graph(),
        "cases": [],
        "checkpoints": [
            {
                "index": 0,
                "label": "RootSolver only",
                "problem_id": None,
                "counts": harness.graph_counts(harness.root_graph()),
            }
        ],
    }


def bootstrapped_state() -> dict:
    response = {
        "response_type": "bootstrap",
        "batch_number": 0,
        "bootstrap": {
            "nodes": [
                node("dimension", "General Resolution Dimension", "composite"),
                node("general", "General Transformation", "abstraction_parent"),
            ],
            "edges": [
                edge("composition", harness.ROOT_ID, "dimension"),
                edge("specialization", harness.ROOT_ID, "general"),
            ],
            "rationale": "Two provisional dimensions illustrate mixed edge semantics.",
        },
        "cases": [],
        "summary": "bootstrap",
    }
    return harness.apply_bootstrap(initial_state(), response)


def valid_case() -> dict:
    return {
        "problem_id": 101,
        "framing": "Treat the concrete request as a state transformation before selecting actions.",
        "new_nodes": [
            node("specific", "Specific State Transition", "composite"),
            node("axis", "State Difference Characterization", "solver"),
            node("axis-two", "Transition Constraint Characterization", "solver"),
        ],
        "topology_edges": [
            edge("specialization", "solver-0003", "specific"),
            edge("composition", "specific", "axis"),
            edge("composition", "specific", "axis-two"),
        ],
        "abstraction_ascent": [
            {
                "node_ref": "specific",
                "why_more_general": "It removes the incidental domain wording.",
                "reframing_effect": "It exposes the state transition that must be designed.",
            },
            {
                "node_ref": "solver-0003",
                "why_more_general": "Transformation includes this and other kinds of change.",
                "reframing_effect": "It makes invariant transition dimensions available.",
            },
            {
                "node_ref": harness.ROOT_ID,
                "why_more_general": "Problem Solving contains every resolvable transformation.",
                "reframing_effect": "It places the request inside the universal resolution boundary.",
            },
        ],
        "invocations": [
            {
                "id": "i-root",
                "parent_id": "ROOT",
                "node_ref": harness.ROOT_ID,
                "edge_kind": "root",
                "role": "Bound and route the complete problem.",
                "contribution": "Treat the request as a problem to resolve.",
            },
            {
                "id": "i-general",
                "parent_id": "i-root",
                "node_ref": "solver-0003",
                "edge_kind": "specialization",
                "role": "Frame the required transformation.",
                "contribution": "Identify the change rather than inherited tasks.",
            },
            {
                "id": "i-specific",
                "parent_id": "i-general",
                "node_ref": "specific",
                "edge_kind": "specialization",
                "role": "Instantiate the relevant transition class.",
                "contribution": "Specify the concrete transition structure.",
            },
            {
                "id": "i-dimension",
                "parent_id": "i-root",
                "node_ref": "solver-0002",
                "edge_kind": "composition",
                "role": "Apply the universal resolution dimension.",
                "contribution": "Give the specific composite a general resolution contribution.",
            },
            {
                "id": "i-axis",
                "parent_id": "i-specific",
                "node_ref": "axis",
                "edge_kind": "composition",
                "role": "Characterize the state difference.",
                "contribution": "Make the before/after difference explicit.",
            },
            {
                "id": "i-axis-two",
                "parent_id": "i-specific",
                "node_ref": "axis-two",
                "edge_kind": "composition",
                "role": "Characterize transition constraints.",
                "contribution": "Expose independent limits on the transition.",
            },
        ],
        "revisions": [],
        "synthesis": "The parent composes the state characterization into a transition design.",
        "proposed_solution": "Use the resulting transition structure to select concrete actions.",
    }


class RootFirstHarnessTests(unittest.TestCase):
    def test_bootstrap_has_one_root_and_mixed_edge_types(self) -> None:
        state = bootstrapped_state()
        harness.validate_rooted(state["graph"])
        self.assertIsNotNone(
            harness.existing_edge(state["graph"], "composition", harness.ROOT_ID, "solver-0002")
        )
        self.assertIsNotNone(
            harness.existing_edge(state["graph"], "specialization", harness.ROOT_ID, "solver-0003")
        )

    def test_same_case_parent_is_installed_before_descent(self) -> None:
        state = bootstrapped_state()
        harness.apply_case(
            state,
            valid_case(),
            {"id": 101, "domain": "test", "problem": "Change a system."},
            {},
            1,
        )
        self.assertEqual(
            [step["node_id"] for step in state["cases"][0]["abstraction_ascent"]],
            ["solver-0004", "solver-0003", harness.ROOT_ID],
        )
        harness.validate_rooted(state["graph"])

    def test_disconnected_new_node_is_rejected(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["new_nodes"].append(node("orphan", "Disconnected Decoration", "passive"))
        with self.assertRaisesRegex(harness.HarnessError, "graph root|disconnected"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_route_must_reverse_the_declared_ascent(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["abstraction_ascent"] = [case["abstraction_ascent"][0], case["abstraction_ascent"][2]]
        with self.assertRaisesRegex(harness.HarnessError, "ascent is not a direct chain"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_ascent_links_must_be_specializations(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["topology_edges"][0]["kind"] = "composition"
        case["invocations"][2]["edge_kind"] = "composition"
        with self.assertRaisesRegex(harness.HarnessError, "ascent links must be specialization"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_root_dimension_may_be_serialized_before_ascent_branch(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        dimension = case["invocations"].pop(3)
        case["invocations"].insert(1, dimension)
        harness.apply_case(
            state,
            case,
            {"id": 101, "domain": "test", "problem": "Change a system."},
            {},
            1,
        )
        self.assertEqual(len(state["cases"]), 1)

    def test_model_derived_root_dimension_cannot_be_bypassed(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["invocations"] = [
            invocation
            for invocation in case["invocations"]
            if invocation["id"] != "i-dimension"
        ]
        with self.assertRaisesRegex(harness.HarnessError, "bypasses model-derived root dimension"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_specific_subject_needs_its_own_conceptual_cut(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["invocations"] = [
            invocation
            for invocation in case["invocations"]
            if invocation["id"] != "i-axis-two"
        ]
        with self.assertRaisesRegex(harness.HarnessError, "at least two conceptual constituents"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_cycle_is_rejected_instead_of_silently_skipped(self) -> None:
        state = bootstrapped_state()
        case = valid_case()
        case["topology_edges"].append(edge("composition", "axis", harness.ROOT_ID))
        with self.assertRaisesRegex(harness.HarnessError, "cycle"):
            harness.apply_case(
                state,
                case,
                {"id": 101, "domain": "test", "problem": "Change a system."},
                {},
                1,
            )

    def test_loaded_graph_cannot_hold_both_edge_kinds_for_one_pair(self) -> None:
        graph = copy.deepcopy(bootstrapped_state()["graph"])
        graph["specialization_edges"].append(
            {
                "id": "edge-corrupt",
                "parent": harness.ROOT_ID,
                "member": "solver-0002",
                "dispatch_basis": "Conflicting relation added outside the normal constructor.",
                "first_problem": None,
                "observed_problems": [],
            }
        )
        with self.assertRaisesRegex(harness.HarnessError, "conflicting edge kinds"):
            harness.validate_graph(graph)

    def test_multi_parent_membership_preserves_one_node(self) -> None:
        state = bootstrapped_state()
        graph = state["graph"]
        temporary = {}
        child_id = harness.add_node(
            graph,
            temporary,
            node("shared", "Shared Capability", "solver"),
            problem_id=101,
            batch_number=1,
        )
        harness.add_edge(
            graph,
            kind="composition",
            parent="solver-0002",
            child=child_id,
            role="First parent-relative role.",
            problem_id=101,
        )
        harness.add_edge(
            graph,
            kind="composition",
            parent="solver-0003",
            child=child_id,
            role="Second parent-relative role.",
            problem_id=101,
        )
        harness.validate_rooted(graph)
        self.assertEqual(sum(n["id"] == child_id for n in graph["nodes"]), 1)


if __name__ == "__main__":
    unittest.main()
