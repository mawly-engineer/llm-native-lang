import unittest

from runtime.example_app_flow import build_example_run_artifact


class ExampleAppFlowTest(unittest.TestCase):
    def test_build_example_run_artifact_proves_determinism(self) -> None:
        artifact = build_example_run_artifact()

        self.assertEqual(
            artifact["programs"],
            ["let x = 1 in x", "let x = 2 in x", "let y = 7 in y"],
        )
        self.assertEqual(len(artifact["runs"]), 3)

        for run in artifact["runs"]:
            self.assertIn("source", run)
            self.assertIn("revision", run)
            self.assertIn("run_node_id", run)
            self.assertIn("result", run)

        self.assertIn("ops", artifact["replay"])
        self.assertIn("metrics", artifact["replay"])

        proof = artifact["determinism_proof"]
        self.assertTrue(proof["ops_equal"])
        self.assertTrue(proof["events_replayed_equal"])
        self.assertTrue(proof["events_total_equal"])


if __name__ == "__main__":
    unittest.main()
