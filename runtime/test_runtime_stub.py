import unittest

from runtime.runtime_stub import KairoRuntime, PatchError


class RuntimeStubPatchOpsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rt = KairoRuntime()

    def test_replace_node_keeps_revision_progression(self) -> None:
        r1 = self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
                ],
            }
        )
        self.assertEqual(r1, "r-1")

        r2 = self.rt.apply_patch(
            {
                "patch_id": "p-2",
                "base_revision": "r-1",
                "target": "program_graph",
                "ops": [
                    {
                        "op": "replace_node",
                        "value": {"id": "ui.shared", "type": "UIEngineV2", "version": "2"},
                    }
                ],
            }
        )
        self.assertEqual(r2, "r-2")
        head_graph = self.rt.state.revisions[r2].graph
        self.assertEqual(head_graph["modules"][0]["type"], "UIEngineV2")

    def test_remove_node_requires_edge_cleanup(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "a", "type": "A"}},
                    {"op": "add_node", "value": {"id": "b", "type": "B"}},
                    {"op": "add_edge", "value": {"from": "a", "to": "b", "contract": "x"}},
                ],
            }
        )

        with self.assertRaises(PatchError) as ctx:
            self.rt.apply_patch(
                {
                    "patch_id": "p-2",
                    "base_revision": "r-1",
                    "target": "program_graph",
                    "ops": [{"op": "remove_node", "value": "a"}],
                }
            )

        self.assertIn("E_NODE_IN_USE", str(ctx.exception))

    def test_remove_edge_then_node_in_same_patch(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "a", "type": "A"}},
                    {"op": "add_node", "value": {"id": "b", "type": "B"}},
                    {"op": "add_edge", "value": {"from": "a", "to": "b", "contract": "x"}},
                ],
            }
        )

        r2 = self.rt.apply_patch(
            {
                "patch_id": "p-2",
                "base_revision": "r-1",
                "target": "program_graph",
                "ops": [
                    {"op": "remove_edge", "value": {"from": "a", "to": "b", "contract": "x"}},
                    {"op": "remove_node", "value": {"id": "a"}},
                ],
            }
        )
        head_graph = self.rt.state.revisions[r2].graph
        self.assertEqual(len(head_graph["edges"]), 0)
        self.assertEqual([m["id"] for m in head_graph["modules"]], ["b"])

    def test_set_attr_updates_node_attrs(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [{"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}}],
            }
        )

        r2 = self.rt.apply_patch(
            {
                "patch_id": "p-2",
                "base_revision": "r-1",
                "target": "program_graph",
                "ops": [
                    {
                        "op": "set_attr",
                        "value": {"node_id": "ui.shared", "key": "render.mode", "value": "incremental"},
                    }
                ],
            }
        )

        node = self.rt.state.revisions[r2].graph["modules"][0]
        self.assertEqual(node["attrs"]["render.mode"], "incremental")

    def test_set_attr_rejects_reserved_key(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [{"op": "add_node", "value": {"id": "n1", "type": "Node"}}],
            }
        )

        with self.assertRaises(PatchError) as ctx:
            self.rt.apply_patch(
                {
                    "patch_id": "p-2",
                    "base_revision": "r-1",
                    "target": "program_graph",
                    "ops": [{"op": "set_attr", "value": {"node_id": "n1", "key": "type", "value": "X"}}],
                }
            )

        self.assertIn("E_ATTR_RESERVED", str(ctx.exception))

    def test_query_modules_by_type(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
                    {"op": "add_node", "value": {"id": "policy.main", "type": "PolicyEngine"}},
                ],
            }
        )

        graph = self.rt.state.revisions[self.rt.state.head].graph
        result = self.rt.query(graph, "modules[type=UIEngine]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "ui.shared")

    def test_query_edges_by_from(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "a", "type": "A"}},
                    {"op": "add_node", "value": {"id": "b", "type": "B"}},
                    {"op": "add_node", "value": {"id": "c", "type": "C"}},
                    {"op": "add_edge", "value": {"from": "a", "to": "b", "contract": "x"}},
                    {"op": "add_edge", "value": {"from": "c", "to": "b", "contract": "x"}},
                ],
            }
        )

        graph = self.rt.state.revisions[self.rt.state.head].graph
        result = self.rt.query(graph, "edges[from=a]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["to"], "b")

    def test_query_modules_by_attr_selector(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
                    {
                        "op": "set_attr",
                        "value": {
                            "node_id": "ui.shared",
                            "key": "render.mode",
                            "value": "incremental",
                        },
                    },
                ],
            }
        )

        graph = self.rt.state.revisions[self.rt.state.head].graph
        result = self.rt.query(graph, "modules[attr.render.mode=incremental]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "ui.shared")

    def test_query_uses_head_by_default(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [{"op": "add_node", "value": {"id": "n1", "type": "Node"}}],
            }
        )

        result = self.rt.query("modules[id=n1]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "Node")

    def test_query_supports_not_equal_operator(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "n1", "type": "Node"}},
                    {"op": "add_node", "value": {"id": "n2", "type": "Service"}},
                ],
            }
        )

        result = self.rt.query("modules[type!=Node]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "n2")

    def test_query_supports_prefix_operator_for_attrs(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "n1", "type": "Node"}},
                    {"op": "add_node", "value": {"id": "n2", "type": "Node"}},
                    {"op": "set_attr", "value": {"node_id": "n1", "key": "display.name", "value": "alpha-ui"}},
                    {"op": "set_attr", "value": {"node_id": "n2", "key": "display.name", "value": "beta-api"}},
                ],
            }
        )

        result = self.rt.query("modules[attr.display.name^=alpha]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "n1")

    def test_query_supports_contains_operator(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "n1", "type": "Renderer"}},
                    {"op": "add_node", "value": {"id": "n2", "type": "Policy"}},
                ],
            }
        )

        result = self.rt.query("modules[type*=ender]")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "n1")

    def test_query_rejects_invalid_selector(self) -> None:
        graph = self.rt.state.revisions[self.rt.state.head].graph
        with self.assertRaises(PatchError) as ctx:
            self.rt.query(graph, "modules[foo=bar]")

        self.assertIn("E_QUERY_KEY", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
