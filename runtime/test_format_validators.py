import subprocess
import tempfile
import unittest
from pathlib import Path


CANONICAL_EXAMPLES_DIR = Path("/home/node/.openclaw/workspace/llm-native-lang/runtime/examples")


REPO_ROOT = Path("/home/node/.openclaw/workspace/llm-native-lang")
LND_VALIDATE = REPO_ROOT / "scripts" / "lnd_validate.py"
LNC_VALIDATE = REPO_ROOT / "scripts" / "lnc_validate.py"


class FormatValidatorToolingTest(unittest.TestCase):
    def test_lnd_validator_passes_existing_docs(self) -> None:
        result = subprocess.run(
            ["python3", str(LND_VALIDATE), str(REPO_ROOT / "evolution")],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("PASS validated", result.stdout)

    def test_lnc_validator_handles_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(LNC_VALIDATE), tmp],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("No .lnc files found.", result.stdout)

    def test_lnd_validator_detects_profile_mismatch_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_file = Path(tmp) / "bad.lnd"
            bad_file.write_text("@lnc 0.1\nkind: code_unit\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(LND_VALIDATE), str(bad_file)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("ERR_PROFILE_MISMATCH", result.stdout)

    def test_lnc_validator_detects_profile_mismatch_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_file = Path(tmp) / "bad.lnc"
            bad_file.write_text("@lnd 0.2\nkind: task\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(LNC_VALIDATE), str(bad_file)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("ERR_PROFILE_MISMATCH", result.stdout)

    def test_runtime_examples_have_at_least_three_canonical_lnc_units(self) -> None:
        canonical_units = sorted(CANONICAL_EXAMPLES_DIR.glob("*.lnc"))
        self.assertGreaterEqual(
            len(canonical_units),
            3,
            "Expected at least 3 canonical .lnc units in runtime/examples.",
        )


if __name__ == "__main__":
    unittest.main()
