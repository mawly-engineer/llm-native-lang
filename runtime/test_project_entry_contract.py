import unittest
from pathlib import Path

REPO_ROOT = Path("/home/node/.openclaw/workspace/llm-native-lang")
ENTRY = REPO_ROOT / "evolution" / "PROJECT_ENTRY.lnd"


def _collect_paths(lines, section):
    paths = []
    in_section = False
    for line in lines:
        if line.startswith(section + ":"):
            in_section = True
            continue
        if in_section:
            if line.startswith("  - "):
                paths.append(line.replace("  - ", "", 1).strip())
                continue
            if line and not line.startswith(" "):
                break
    return paths


class ProjectEntryContractTest(unittest.TestCase):
    def test_core_and_agent_paths_exist(self):
        lines = ENTRY.read_text(encoding="utf-8").splitlines()
        core = _collect_paths(lines, "core_file_set")
        agent = _collect_paths(lines, "agent_and_cron_control_files")

        self.assertGreater(len(core), 0)
        self.assertGreater(len(agent), 0)

        for rel in core + agent:
            path = REPO_ROOT / rel
            self.assertTrue(path.exists(), f"missing path from PROJECT_ENTRY: {rel}")


if __name__ == "__main__":
    unittest.main()
