import unittest

from runtime.replay_conformance import (
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


if __name__ == "__main__":
    unittest.main()
