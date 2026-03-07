#!/usr/bin/env python3
import argparse
import os
import sys
from typing import Iterable, Tuple

ERROR_INVALID_HEADER = "LND_PARSE_001"
ERROR_PROFILE_MISMATCH = "ERR_PROFILE_MISMATCH"


def _iter_targets(path: str) -> Iterable[str]:
    if os.path.isfile(path):
        yield path
        return

    for root, _dirs, files in os.walk(path):
        for name in sorted(files):
            if name.endswith(".lnd"):
                yield os.path.join(root, name)


def _validate_file(path: str) -> Tuple[bool, str]:
    with open(path, "r", encoding="utf-8") as handle:
        first_line = handle.readline().strip()

    _, ext = os.path.splitext(path)
    if ext != ".lnd":
        return False, f"{ERROR_PROFILE_MISMATCH}: file extension is '{ext}', expected '.lnd'"

    if not first_line.startswith("@lnd "):
        if first_line.startswith("@lnc "):
            return False, f"{ERROR_PROFILE_MISMATCH}: file extension/header family mismatch (.lnd vs @lnc)"
        return False, f"{ERROR_INVALID_HEADER}: missing '@lnd <version>' header"

    return True, "OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate .lnd headers and profile-extension match.")
    parser.add_argument(
        "target",
        nargs="?",
        default="/home/node/.openclaw/workspace/llm-native-lang/evolution",
        help="File or directory to validate.",
    )
    args = parser.parse_args()

    targets = list(_iter_targets(args.target))
    if not targets:
        print("No .lnd files found.")
        return 0

    failures = []
    for path in targets:
        ok, message = _validate_file(path)
        if not ok:
            failures.append((path, message))

    if failures:
        for path, message in failures:
            print(f"FAIL {path}: {message}")
        return 1

    print(f"PASS validated {len(targets)} .lnd file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
