#!/usr/bin/env python3
"""Deterministic onboarding verification for README quickstart and docs links."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"

COMMAND_BLOCK_PATTERN = re.compile(r"```bash\n(.*?)\n```", re.DOTALL)
DOC_LINK_PATTERN = re.compile(r"- `([^`]+)`\s+—")


def _fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def _run_command(command: str) -> int:
    print(f"[RUN] {command}")
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(ROOT),
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    print(result.stdout.rstrip())
    return result.returncode


def main() -> int:
    if not README_PATH.exists():
        return _fail("README.md does not exist")

    readme = README_PATH.read_text(encoding="utf-8")

    command_blocks = COMMAND_BLOCK_PATTERN.findall(readme)
    if not command_blocks:
        return _fail("No bash command blocks found in README quickstart")

    commands: list[str] = []
    for block in command_blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                commands.append(stripped)

    # Skip clone/cd steps because CI already runs in a checked-out repository root.
    executable_commands = [
        command
        for command in commands
        if not command.startswith("git clone ") and not command.startswith("cd ")
    ]

    if not executable_commands:
        return _fail("No executable quickstart commands found after filtering clone/cd")

    for command in executable_commands:
        exit_code = _run_command(command)
        if exit_code != 0:
            return _fail(f"Quickstart command failed: {command}")

    links = DOC_LINK_PATTERN.findall(readme)
    if not links:
        return _fail("No machine-readable contract links found in README")

    missing_links = [link for link in links if not (ROOT / link).exists()]
    if missing_links:
        return _fail(f"README docs links missing targets: {', '.join(missing_links)}")

    print("[OK] README quickstart commands succeeded")
    print("[OK] README docs links are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
