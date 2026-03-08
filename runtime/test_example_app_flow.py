import subprocess
import unittest
from pathlib import Path

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

    def test_public_demo_script_matches_committed_expected_artifact(self) -> None:
        repo_root = Path("/home/node/.openclaw/workspace/llm-native-lang")
        script_path = repo_root / "scripts" / "run_public_demo.py"
        expected_path = repo_root / "runtime" / "examples" / "canonical_public_demo_expected.json"

        result = subprocess.run(
            [
                "python3",
                str(script_path),
                "--verify-expected",
                "--expected",
                str(expected_path),
            ],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.stdout, expected_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
