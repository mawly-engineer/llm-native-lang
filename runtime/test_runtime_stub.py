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


if __name__ == "__main__":
    unittest.main()
