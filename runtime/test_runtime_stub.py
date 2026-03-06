import random
import unittest
from copy import deepcopy
from typing import Any, Dict, List

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
        self.assertEqual(replay["metrics"]["events_from_snapshot_seed"], 2)
        self.assertEqual(replay["metrics"]["events_total"], 2)
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
        self.assertEqual(replay["metrics"]["events_from_snapshot_seed"], 1)
        self.assertEqual(replay["metrics"]["events_total"], 2)
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

    def test_merge_ui_branches_supports_delta_mode(self) -> None:
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

        merged = self.rt.merge_ui_branches(left, right, base_revision=base, mode="delta")

        merged_event = self.rt.ui_timeline[merged["merged_revision"]]
        self.assertEqual(merged["merge_mode"], "delta")
        self.assertEqual(merged_event.merge_mode, "delta")
        self.assertEqual(merged_event.delta_base_revision, base)
        self.assertEqual(
            self.rt.replay_ui_timeline(merged["merged_revision"]),
            merged["merged_ops"],
        )

    def test_replay_ui_timeline_supports_mixed_materialized_and_delta_history(self) -> None:
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

        materialized = self.rt.merge_ui_branches(left, right, base_revision=base, mode="materialized")
        self.rt.rollback_ui(materialized["merged_revision"])
        delta_merge = self.rt.merge_ui_branches(
            materialized["merged_revision"],
            right,
            base_revision=right,
            mode="delta",
        )

        self.assertEqual(
            self.rt.replay_ui_timeline(delta_merge["merged_revision"]),
            delta_merge["merged_ops"],
        )

    def test_replay_metrics_for_delta_merge_are_base_seeded(self) -> None:
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

        merged = self.rt.merge_ui_branches(left, right, base_revision=base, mode="delta")
        replay = self.rt.replay_ui_timeline(head=merged["merged_revision"], include_metrics=True)

        self.assertEqual(replay["metrics"]["events_replayed"], 2)

    def test_replay_metrics_for_delta_merge_with_snapshot_seed(self) -> None:
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

        self.rt.create_ui_snapshot(head=base)
        merged = self.rt.merge_ui_branches(left, right, base_revision=base, mode="delta")
        replay = self.rt.replay_ui_timeline(head=merged["merged_revision"], include_metrics=True)

        self.assertEqual(replay["snapshot_head"], base)
        self.assertEqual(replay["metrics"]["events_replayed"], 3)
        self.assertEqual(replay["metrics"]["events_from_snapshot_seed"], 3)
        self.assertEqual(replay["metrics"]["events_total"], 2)
        self.assertEqual(replay["metrics"]["snapshot_seed_distance"], 2)

    def test_merge_ui_branches_rejects_unknown_mode_with_dedicated_error(self) -> None:
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

        with self.assertRaises(PatchError) as ctx:
            self.rt.merge_ui_branches(left, right, mode="fast-forward")

        self.assertIn("E_UI_MERGE_MODE", str(ctx.exception))

    def test_preview_ui_merge_auto_lca_supports_implicit_root(self) -> None:
        preview = self.rt.preview_ui_merge(None, None)

        self.assertIsNone(preview["base_revision"])
        self.assertEqual(preview["merged_ops"], [])

    def test_preview_ui_merge_auto_lca_rejects_none_and_branch_head_without_explicit_base(self) -> None:
        right = self.rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])

        with self.assertRaises(PatchError) as ctx:
            self.rt.preview_ui_merge(None, right)

        self.assertIn("E_UI_MERGE_BASE", str(ctx.exception))

    def test_replay_delta_event_requires_base_revision(self) -> None:
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

        merged = self.rt.merge_ui_branches(left, right, base_revision=base, mode="delta")
        self.rt.ui_timeline[merged["merged_revision"]].delta_base_revision = None

        with self.assertRaises(PatchError) as ctx:
            self.rt.replay_ui_timeline(merged["merged_revision"])

        self.assertIn("E_UI_DELTA_BASE", str(ctx.exception))

    def test_replay_delta_event_rejects_unknown_base_revision(self) -> None:
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

        merged = self.rt.merge_ui_branches(left, right, base_revision=base, mode="delta")
        self.rt.ui_timeline[merged["merged_revision"]].delta_base_revision = "u-404"

        with self.assertRaises(PatchError) as ctx:
            self.rt.replay_ui_timeline(merged["merged_revision"])

        self.assertIn("E_UI_DELTA_BASE", str(ctx.exception))

    def _build_fanin_replay_metrics(self, first_mode: str, second_mode: str) -> Dict[str, Any]:
        rt = KairoRuntime()
        base = rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])
        rt.create_ui_snapshot(head=base)

        left = rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "title", "value": "L"}],
            base_revision=base,
        )
        rt.rollback_ui(base)
        right = rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "subtitle", "value": "R"}],
            base_revision=base,
        )

        first_merge = rt.merge_ui_branches(left, right, base_revision=base, mode=first_mode)["merged_revision"]

        rt.rollback_ui(first_merge)
        top = rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "badge", "value": "TOP"}],
            base_revision=first_merge,
        )
        rt.rollback_ui(right)
        side = rt.apply_ui_patch(
            [{"op": "set_prop", "path": "/root/a", "key": "footer", "value": "SIDE"}],
            base_revision=right,
        )

        second_merge = rt.merge_ui_branches(top, side, base_revision=right, mode=second_mode)
        return rt.replay_ui_timeline(head=second_merge["merged_revision"], include_metrics=True)

    def test_replay_metrics_compare_fanin_materialized_vs_nested_delta(self) -> None:
        materialized = self._build_fanin_replay_metrics("materialized", "materialized")
        nested_delta = self._build_fanin_replay_metrics("delta", "delta")

        self.assertEqual(materialized["ops"], nested_delta["ops"])
        self.assertEqual(materialized["snapshot_head"], "u-0")
        self.assertEqual(nested_delta["snapshot_head"], "u-0")
        self.assertEqual(materialized["metrics"]["events_from_snapshot_seed"], 6)
        self.assertEqual(nested_delta["metrics"]["events_from_snapshot_seed"], 6)
        self.assertEqual(materialized["metrics"]["events_total"], 7)
        self.assertEqual(nested_delta["metrics"]["events_total"], 3)

    def test_replay_metrics_compare_fanin_mixed_merge_modes(self) -> None:
        materialized_materialized = self._build_fanin_replay_metrics("materialized", "materialized")
        materialized_delta = self._build_fanin_replay_metrics("materialized", "delta")
        delta_materialized = self._build_fanin_replay_metrics("delta", "materialized")
        delta_delta = self._build_fanin_replay_metrics("delta", "delta")

        self.assertEqual(materialized_materialized["ops"], materialized_delta["ops"])
        self.assertEqual(materialized_materialized["ops"], delta_materialized["ops"])
        self.assertEqual(materialized_materialized["ops"], delta_delta["ops"])

        self.assertEqual(materialized_materialized["metrics"]["events_from_snapshot_seed"], 6)
        self.assertEqual(materialized_delta["metrics"]["events_from_snapshot_seed"], 6)
        self.assertEqual(delta_materialized["metrics"]["events_from_snapshot_seed"], 6)
        self.assertEqual(delta_delta["metrics"]["events_from_snapshot_seed"], 6)

        self.assertEqual(materialized_materialized["metrics"]["events_total"], 7)
        self.assertEqual(materialized_delta["metrics"]["events_total"], 3)
        self.assertEqual(delta_materialized["metrics"]["events_total"], 6)
        self.assertEqual(delta_delta["metrics"]["events_total"], 3)

    def _random_merge_case(self, seed: int, include_structural_ops: bool = False) -> Dict[str, Any]:
        rng = random.Random(seed)
        rt = KairoRuntime()
        base = rt.apply_ui_patch([{"op": "insert", "path": "/root/a", "value": {"kind": "card"}}])

        left_head = base
        right_head = base
        keys: List[str] = ["title", "subtitle", "badge", "footer"]
        item_paths: List[str] = ["/root/a/items/left", "/root/a/items/right"]

        def branch_op(prefix: str, step: int) -> Dict[str, Any]:
            if not include_structural_ops:
                key = rng.choice(keys)
                return {"op": "set_prop", "path": "/root/a", "key": key, "value": f"{prefix}{seed}-{step}-{key}"}

            op_kind = rng.choice(["set_prop", "insert", "remove"])
            if op_kind == "set_prop":
                key = rng.choice(keys)
                return {
                    "op": "set_prop",
                    "path": "/root/a",
                    "key": key,
                    "value": f"{prefix}{seed}-{step}-{key}",
                }

            item_path = rng.choice(item_paths)
            if op_kind == "insert":
                return {
                    "op": "insert",
                    "path": item_path,
                    "value": {"kind": "tag", "source": prefix.lower(), "step": step},
                }

            return {"op": "remove", "path": item_path}

        for i in range(rng.randint(1, 4)):
            left_head = rt.apply_ui_patch([branch_op("L", i)], base_revision=left_head)

        rt.rollback_ui(base)

        for i in range(rng.randint(1, 4)):
            right_head = rt.apply_ui_patch([branch_op("R", i)], base_revision=right_head)

        preview = rt.preview_ui_merge(left_head, right_head)
        resolutions_right = [
            {
                "op": conflict["key"]["op"],
                "path": conflict["key"]["path"],
                "prop": conflict["key"]["prop"],
                "decision": "accept_right",
            }
            for conflict in preview["conflicts"]
        ]
        resolutions_left = [
            {
                "op": conflict["key"]["op"],
                "path": conflict["key"]["path"],
                "prop": conflict["key"]["prop"],
                "decision": "accept_left",
            }
            for conflict in preview["conflicts"]
        ]

        return {
            "runtime": rt,
            "base": base,
            "left": left_head,
            "right": right_head,
            "preview": preview,
            "resolutions": resolutions_right,
            "resolutions_left": resolutions_left,
            "resolutions_right": resolutions_right,
        }

    def test_randomized_merge_preview_base_is_common_ancestor(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(seed)
            rt = case["runtime"]
            preview = case["preview"]
            base = preview["base_revision"]

            self.assertIn(base, rt._ui_ancestors(case["left"]))
            self.assertIn(base, rt._ui_ancestors(case["right"]))

    def test_randomized_merge_conflict_resolution_roundtrip(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(100 + seed)
            rt = case["runtime"]
            left = case["left"]
            right = case["right"]

            if case["preview"]["conflicts"]:
                with self.assertRaises(PatchError) as ctx:
                    rt.merge_ui_branches(left, right)
                self.assertIn("E_UI_MERGE_CONFLICT", str(ctx.exception))

            merged = rt.merge_ui_branches(
                left,
                right,
                resolutions=case["resolutions"],
                mode="delta" if seed % 2 else "materialized",
            )
            self.assertEqual(rt.replay_ui_timeline(merged["merged_revision"]), merged["merged_ops"])

    def test_randomized_merge_rejects_explicit_base_mismatch(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(200 + seed)
            rt = case["runtime"]
            left = case["left"]
            right = case["right"]

            with self.assertRaises(PatchError) as ctx:
                rt.preview_ui_merge(left, right, base_revision=left)

            self.assertIn("E_UI_MERGE_BASE", str(ctx.exception))

    def test_randomized_merge_materialized_vs_delta_end_state_equivalence(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(300 + seed)
            rt_materialized = deepcopy(case["runtime"])
            rt_delta = deepcopy(case["runtime"])
            left = case["left"]
            right = case["right"]
            resolutions = case["resolutions"]

            merged_materialized = rt_materialized.merge_ui_branches(
                left,
                right,
                resolutions=resolutions,
                mode="materialized",
            )
            merged_delta = rt_delta.merge_ui_branches(
                left,
                right,
                resolutions=resolutions,
                mode="delta",
            )

            self.assertEqual(merged_materialized["merged_ops"], merged_delta["merged_ops"])
            self.assertEqual(
                rt_materialized.replay_ui_timeline(merged_materialized["merged_revision"]),
                rt_delta.replay_ui_timeline(merged_delta["merged_revision"]),
            )

    def test_randomized_merge_with_structural_ops_roundtrip(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(400 + seed, include_structural_ops=True)
            rt = case["runtime"]

            merged = rt.merge_ui_branches(
                case["left"],
                case["right"],
                resolutions=case["resolutions_right"],
                mode="delta" if seed % 2 else "materialized",
            )
            self.assertEqual(rt.replay_ui_timeline(merged["merged_revision"]), merged["merged_ops"])

    def test_randomized_merge_resolution_profiles_are_replayable(self) -> None:
        for seed in range(25):
            case = self._random_merge_case(500 + seed, include_structural_ops=True)
            left = case["left"]
            right = case["right"]

            rt_accept_left = deepcopy(case["runtime"])
            rt_accept_right = deepcopy(case["runtime"])

            merged_left = rt_accept_left.merge_ui_branches(
                left,
                right,
                resolutions=case["resolutions_left"],
                mode="materialized",
            )
            merged_right = rt_accept_right.merge_ui_branches(
                left,
                right,
                resolutions=case["resolutions_right"],
                mode="materialized",
            )

            self.assertEqual(
                rt_accept_left.replay_ui_timeline(merged_left["merged_revision"]),
                merged_left["merged_ops"],
            )
            self.assertEqual(
                rt_accept_right.replay_ui_timeline(merged_right["merged_revision"]),
                merged_right["merged_ops"],
            )

            conflicts = case["preview"]["conflicts"]
            if conflicts:
                self.assertNotEqual(merged_left["merged_ops"], merged_right["merged_ops"])


if __name__ == "__main__":
    unittest.main()
