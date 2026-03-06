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

    def test_query_supports_sorting_and_limit(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "n3", "type": "Node"}},
                    {"op": "add_node", "value": {"id": "n1", "type": "Node"}},
                    {"op": "add_node", "value": {"id": "n2", "type": "Node"}},
                ],
            }
        )

        result = self.rt.query("modules", sort_by="id", limit=2)

        self.assertEqual([node["id"] for node in result], ["n1", "n2"])

    def test_query_supports_descending_sort_for_attrs(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "n1", "type": "Node"}},
                    {"op": "add_node", "value": {"id": "n2", "type": "Node"}},
                    {"op": "set_attr", "value": {"node_id": "n1", "key": "display.order", "value": 1}},
                    {"op": "set_attr", "value": {"node_id": "n2", "key": "display.order", "value": 9}},
                ],
            }
        )

        result = self.rt.query("modules", sort_by="attr.display.order", descending=True)

        self.assertEqual([node["id"] for node in result], ["n2", "n1"])

    def test_query_rejects_invalid_limit(self) -> None:
        with self.assertRaises(PatchError) as ctx:
            self.rt.query("modules", limit=-1)

        self.assertIn("E_QUERY_LIMIT", str(ctx.exception))

    def test_query_rejects_invalid_selector(self) -> None:
        graph = self.rt.state.revisions[self.rt.state.head].graph
        with self.assertRaises(PatchError) as ctx:
            self.rt.query(graph, "modules[foo=bar]")

        self.assertIn("E_QUERY_KEY", str(ctx.exception))

    def test_ui_ops_normalize_deterministic_order(self) -> None:
        ops = [
            {"op": "set_prop", "path": "/root/a", "key": "text", "value": "Hallo"},
            {"op": "insert", "path": "/root/b", "value": {"kind": "label"}},
            {"op": "remove", "path": "/root/a"},
            {"op": "move", "path": "/root/c", "value": {"to": "/root/a"}},
            {"op": "replace", "path": "/root/c", "value": {"kind": "button"}},
        ]

        result = self.rt.normalize_ui_ops(ops)

        self.assertEqual(
            result,
            [
                {"op": "remove", "path": "/root/a"},
                {"op": "insert", "path": "/root/b", "value": {"kind": "label"}},
                {"op": "replace", "path": "/root/c", "value": {"kind": "button"}},
                {"op": "move", "path": "/root/c", "value": {"to": "/root/a"}},
            ],
        )

    def test_ui_ops_normalize_last_write_wins_for_set_prop(self) -> None:
        ops = [
            {"op": "set_prop", "path": "/root/title", "key": "text", "value": "A"},
            {"op": "set_prop", "path": "/root/title", "key": "text", "value": "B"},
        ]

        result = self.rt.normalize_ui_ops(ops)

        self.assertEqual(result, [{"op": "set_prop", "path": "/root/title", "key": "text", "value": "B"}])

    def test_ui_ops_parent_remove_drops_child_ops(self) -> None:
        ops = [
            {"op": "set_prop", "path": "/root/a/b", "key": "text", "value": "X"},
            {"op": "insert", "path": "/root/a/b", "value": {"kind": "label"}},
            {"op": "remove", "path": "/root/a"},
            {"op": "replace", "path": "/root/a/c", "value": {"kind": "button"}},
        ]

        result = self.rt.normalize_ui_ops(ops)

        self.assertEqual(result, [{"op": "remove", "path": "/root/a"}])

    def test_ui_ops_child_remove_ignored_after_parent_remove(self) -> None:
        ops = [
            {"op": "remove", "path": "/root/a"},
            {"op": "remove", "path": "/root/a/b"},
            {"op": "set_prop", "path": "/root/a/b", "key": "text", "value": "ignored"},
            {"op": "insert", "path": "/root/x", "value": {"kind": "label"}},
        ]

        result = self.rt.normalize_ui_ops(ops)

        self.assertEqual(
            result,
            [
                {"op": "remove", "path": "/root/a"},
                {"op": "insert", "path": "/root/x", "value": {"kind": "label"}},
            ],
        )

    def test_ui_timeline_replay_uses_append_only_events(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        u1 = self.rt.apply_ui_patch(
            [
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "A"},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "B"},
            ],
            base_revision=u0,
        )

        replayed = self.rt.replay_ui_timeline(u1)

        self.assertEqual(
            replayed,
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "B"},
            ],
        )

    def test_ui_rollback_changes_replay_head(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Live"}],
            base_revision=u0,
        )

        self.rt.rollback_ui(u0)

        replayed = self.rt.replay_ui_timeline()
        self.assertEqual(replayed, [{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])

    def test_apply_patch_supports_ui_patch_and_couples_revisions(self) -> None:
        revision = self.rt.apply_patch(
            {
                "patch_id": "p-ui-1",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
                    {
                        "op": "ui_patch",
                        "value": {
                            "ops": [
                                {"op": "insert", "path": "/root/title", "value": {"kind": "label"}},
                                {
                                    "op": "set_prop",
                                    "path": "/root/title",
                                    "key": "text",
                                    "value": "Hallo",
                                },
                            ]
                        },
                    },
                ],
            }
        )

        self.assertEqual(revision, "r-1")
        self.assertEqual(self.rt.state.revisions[revision].ui_revision, "u-0")
        self.assertEqual(self.rt.ui_head, "u-0")
        self.assertEqual(
            self.rt.replay_ui_timeline(),
            [
                {"op": "insert", "path": "/root/title", "value": {"kind": "label"}},
                {"op": "set_prop", "path": "/root/title", "key": "text", "value": "Hallo"},
            ],
        )

    def test_apply_patch_supports_multiple_ui_patch_ops(self) -> None:
        revision = self.rt.apply_patch(
            {
                "patch_id": "p-ui-multi",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [
                    {"op": "add_node", "value": {"id": "ui.shared", "type": "UIEngine"}},
                    {
                        "op": "ui_patch",
                        "value": {
                            "ops": [
                                {"op": "insert", "path": "/root/title", "value": {"kind": "label"}},
                            ]
                        },
                    },
                    {
                        "op": "ui_patch",
                        "value": {
                            "ops": [
                                {
                                    "op": "set_prop",
                                    "path": "/root/title",
                                    "key": "text",
                                    "value": "Hallo 2",
                                },
                            ]
                        },
                    },
                ],
            }
        )

        self.assertEqual(revision, "r-1")
        self.assertEqual(self.rt.state.revisions[revision].ui_revision, "u-1")
        self.assertEqual(self.rt.ui_head, "u-1")
        self.assertEqual(len(self.rt.ui_timeline), 2)
        self.assertEqual(
            self.rt.replay_ui_timeline(),
            [
                {"op": "insert", "path": "/root/title", "value": {"kind": "label"}},
                {"op": "set_prop", "path": "/root/title", "key": "text", "value": "Hallo 2"},
            ],
        )

    def test_apply_patch_rejects_ui_base_mismatch_transactionally(self) -> None:
        self.rt.apply_patch(
            {
                "patch_id": "p-setup",
                "base_revision": "r-0",
                "target": "program_graph",
                "ops": [{"op": "add_node", "value": {"id": "n1", "type": "Node"}}],
            }
        )
        self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])

        with self.assertRaises(PatchError) as ctx:
            self.rt.apply_patch(
                {
                    "patch_id": "p-ui-bad",
                    "base_revision": "r-1",
                    "target": "program_graph",
                    "ops": [
                        {"op": "add_node", "value": {"id": "n2", "type": "Node"}},
                        {
                            "op": "ui_patch",
                            "value": {
                                "base_revision": "u-404",
                                "ops": [{"op": "set_prop", "path": "/root/a", "key": "text", "value": "X"}],
                            },
                        },
                    ],
                }
            )

        self.assertIn("E_UI_BASE_MISMATCH", str(ctx.exception))
        self.assertEqual(self.rt.state.head, "r-1")
        self.assertEqual(len(self.rt.state.revisions[self.rt.state.head].graph["modules"]), 1)
        self.assertEqual(self.rt.ui_head, "u-0")
        self.assertEqual(len(self.rt.ui_timeline), 1)

    def test_ui_snapshot_replay_matches_head_state(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Live"}],
            base_revision=u0,
        )

        snapshot_id = self.rt.create_ui_snapshot()

        self.assertEqual(snapshot_id, "s-0")
        self.assertEqual(self.rt.ui_snapshots[snapshot_id].event_head, self.rt.ui_head)
        self.assertEqual(
            self.rt.ui_snapshots[snapshot_id].ops,
            self.rt.replay_ui_timeline(),
        )

    def test_ui_snapshot_accelerates_descendant_replay_consistently(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        self.rt.create_ui_snapshot(head=u0)
        u1 = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "One"}],
            base_revision=u0,
        )
        self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Two"}],
            base_revision=u1,
        )

        self.assertEqual(
            self.rt.replay_ui_timeline(),
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Two"},
            ],
        )

    def test_replay_ui_timeline_exposes_metrics_without_snapshot(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Live"}],
            base_revision=u0,
        )

        replay = self.rt.replay_ui_timeline(include_metrics=True)

        self.assertEqual(replay["head"], self.rt.ui_head)
        self.assertIsNone(replay["snapshot_head"])
        self.assertEqual(replay["metrics"]["events_replayed"], 2)
        self.assertIsNone(replay["metrics"]["snapshot_seed_distance"])

    def test_replay_ui_timeline_exposes_metrics_with_snapshot_seed(self) -> None:
        u0 = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        self.rt.create_ui_snapshot(head=u0)
        self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Live"}],
            base_revision=u0,
        )

        replay = self.rt.replay_ui_timeline(include_metrics=True)

        self.assertEqual(replay["snapshot_head"], u0)
        self.assertEqual(replay["metrics"]["events_replayed"], 1)
        self.assertEqual(replay["metrics"]["snapshot_seed_distance"], 1)

    def test_validate_ui_merge_accepts_non_conflicting_branches(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"}],
            base_revision=base,
        )

        merge_info = self.rt.validate_ui_merge(left, right, base_revision=base)

        self.assertEqual(merge_info["base_revision"], base)
        self.assertEqual(merge_info["left_revision"], left)
        self.assertEqual(merge_info["right_revision"], right)
        self.assertEqual(
            merge_info["merged_ops"],
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"},
            ],
        )

    def test_validate_ui_merge_detects_conflicting_writes(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
            base_revision=base,
        )

        with self.assertRaises(PatchError) as ctx:
            self.rt.validate_ui_merge(left, right, base_revision=base)

        self.assertIn("E_UI_MERGE_CONFLICT", str(ctx.exception))
        self.assertIsInstance(ctx.exception.details, dict)
        self.assertEqual(len(ctx.exception.details["conflicts"]), 1)

    def test_preview_ui_merge_returns_structured_conflicts(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
            base_revision=base,
        )

        preview = self.rt.preview_ui_merge(left, right, base_revision=base)

        self.assertEqual(preview["base_revision"], base)
        self.assertEqual(len(preview["conflicts"]), 1)
        self.assertEqual(preview["conflicts"][0]["key"]["path"], "/root/a")
        self.assertEqual(preview["conflicts"][0]["key"]["prop"], "title")

    def test_merge_ui_branches_creates_new_ui_head(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"}],
            base_revision=base,
        )

        merged = self.rt.merge_ui_branches(left, right, base_revision=base, resolution_notes="safe auto merge")

        self.assertEqual(merged["merged_revision"], self.rt.ui_head)
        merged_event = self.rt.ui_timeline[merged["merged_revision"]]
        self.assertEqual(merged_event.parent, left)
        self.assertEqual(merged_event.secondary_parent, right)
        self.assertEqual(merged_event.resolution_notes, "safe auto merge")
        self.assertEqual(
            self.rt.replay_ui_timeline(),
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"},
            ],
        )

    def test_replay_ui_timeline_reads_secondary_parent_branch(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"}],
            base_revision=base,
        )

        merged = self.rt.merge_ui_branches(left, right, base_revision=base)
        self.rt.ui_timeline[merged["merged_revision"]].ops = []

        self.assertEqual(
            self.rt.replay_ui_timeline(merged["merged_revision"]),
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"},
            ],
        )

    def test_snapshot_index_can_seed_from_secondary_parent_ancestor(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"}],
            base_revision=base,
        )

        self.rt.create_ui_snapshot(head=right)
        merged = self.rt.merge_ui_branches(left, right, base_revision=base)
        self.rt.ui_timeline[merged["merged_revision"]].ops = []

        self.assertEqual(
            self.rt.replay_ui_timeline(merged["merged_revision"]),
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"},
            ],
        )

    def test_merge_ui_branches_accepts_resolution_for_conflict(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
            base_revision=base,
        )

        merged = self.rt.merge_ui_branches(
            left,
            right,
            base_revision=base,
            resolutions=[
                {
                    "op": "set_prop",
                    "path": "/root/a",
                    "prop": "title",
                    "decision": "accept_right",
                }
            ],
            resolution_notes="manuell: right gewinnt für title",
        )

        self.assertEqual(len(merged["conflicts"]), 0)
        self.assertEqual(len(merged["applied_resolutions"]), 1)
        self.assertEqual(
            self.rt.replay_ui_timeline(),
            [
                {"op": "insert", "path": "/root/a", "value": {"kind": "card"}},
                {"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"},
            ],
        )

    def test_preview_ui_merge_delta_reconstructs_materialized_merge(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "Right"}],
            base_revision=base,
        )

        delta_preview = self.rt.preview_ui_merge_delta(left, right, base_revision=base)

        self.assertEqual(len(delta_preview["conflicts"]), 0)
        self.assertTrue(delta_preview["delta_metrics"]["reconstructs_merged"])
        self.assertEqual(
            self.rt.normalize_ui_ops(delta_preview["base_ops"] + delta_preview["delta_ops"]),
            delta_preview["merged_ops"],
        )

    def test_preview_ui_merge_delta_tracks_resolution_choice(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
            base_revision=base,
        )

        delta_preview = self.rt.preview_ui_merge_delta(
            left,
            right,
            base_revision=base,
            resolutions=[
                {
                    "op": "set_prop",
                    "path": "/root/a",
                    "prop": "title",
                    "decision": "accept_right",
                }
            ],
        )

        self.assertEqual(len(delta_preview["conflicts"]), 0)
        self.assertEqual(delta_preview["delta_metrics"]["delta_ops"], 1)
        self.assertEqual(
            delta_preview["delta_ops"],
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
        )

    def test_merge_ui_branches_rejects_invalid_resolution_decision(self) -> None:
        base = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        left = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Left"}],
            base_revision=base,
        )

        self.rt.rollback_ui(base)
        right = self.rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "Right"}],
            base_revision=base,
        )

        with self.assertRaises(PatchError) as ctx:
            self.rt.preview_ui_merge(
                left,
                right,
                base_revision=base,
                resolutions=[
                    {
                        "op": "set_prop",
                        "path": "/root/a",
                        "prop": "title",
                        "decision": "drop",
                    }
                ],
            )

        self.assertIn("E_UI_MERGE_RESOLUTION", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
