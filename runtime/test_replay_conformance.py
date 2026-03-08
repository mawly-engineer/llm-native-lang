import unittest

from runtime.replay_conformance import (
    _trace_for_source,
    evaluate_batch_replay_conformance,
    evaluate_replay_conformance,
)


class ReplayConformanceHarnessTest(unittest.TestCase):
    def test_single_source_replay_conformance(self) -> None:
        result = evaluate_replay_conformance("let x = 7 in x", repeats=4)

        self.assertTrue(result.conformance)
        self.assertEqual(len(result.signatures), 4)
        self.assertEqual(len(set(result.signatures)), 1)
        self.assertEqual(result.mismatch_indices, [])

    def test_batch_replay_conformance_for_multiple_programs(self) -> None:
        summary = evaluate_batch_replay_conformance(
            [
                "let x = 1 in x",
                "let x = 2 in x",
                "let y = 3 in y",
            ],
            repeats=3,
        )

        self.assertTrue(summary["conformance"])
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["failed"], 0)

    def test_replay_conformance_requires_repeat_count(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_replay_conformance("let x = 1 in x", repeats=1)

    def test_runtime_trace_metadata_is_emitted_in_patch_and_graph(self) -> None:
        trace = _trace_for_source("let x = 1 in x")
        patch = trace["patch"]
        graph = trace["graph"]

        run_node = next(module for module in graph["modules"] if module["id"] == "language.run")
        attrs = run_node.get("attrs", {})

        self.assertIn("language.trace_ids", attrs)
        self.assertIn("language.trace_count", attrs)

        ui_trace_ops = [op for op in trace["ui_ops"] if op.get("key") == "trace_ids"]
        self.assertEqual(len(ui_trace_ops), 1)
        self.assertIsInstance(ui_trace_ops[0].get("value"), list)


if __name__ == "__main__":
    unittest.main()
