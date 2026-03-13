#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path("/home/node/.openclaw/workspace/llm-native-lang")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.example_app_flow import build_example_run_artifact
from runtime.replay_conformance import evaluate_batch_replay_conformance
from runtime.grammar_contract import parse_expr


DEFAULT_EXPECTED_PATH = Path("/home/node/.openclaw/workspace/llm-native-lang/runtime/examples/canonical_public_demo_expected.json")
DEFAULT_PROGRAMS = [
    "let x = 1 in x",
    "let x = 2 in x",
    "let y = 7 in y",
]


def _build_demo_output() -> dict:
    artifact = build_example_run_artifact(programs=DEFAULT_PROGRAMS)
    # Parse programs to AST nodes before passing to replay conformance
    parsed_programs = [parse_expr(prog) for prog in DEFAULT_PROGRAMS]
    conformance = evaluate_batch_replay_conformance(parsed_programs, repeats=3)
    return {
        "demo": "LLM -> LNC -> Runtime -> Replay",
        "artifact": artifact,
        "batch_conformance": conformance,
    }


def _to_canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run canonical one-click public demo and optionally verify expected output artifact."
    )
    parser.add_argument(
        "--expected",
        type=Path,
        default=DEFAULT_EXPECTED_PATH,
        help="Path to canonical expected output artifact JSON.",
    )
    parser.add_argument(
        "--write-expected",
        action="store_true",
        help="Write current output to --expected and exit 0.",
    )
    parser.add_argument(
        "--verify-expected",
        action="store_true",
        help="Fail if current output does not byte-match --expected.",
    )
    args = parser.parse_args()

    output = _to_canonical_json(_build_demo_output())

    if args.write_expected:
        args.expected.parent.mkdir(parents=True, exist_ok=True)
        args.expected.write_text(output, encoding="utf-8")

    if args.verify_expected:
        if not args.expected.exists():
            print(f"EXPECTED_ARTIFACT_MISSING: {args.expected}", file=sys.stderr)
            return 2
        expected = args.expected.read_text(encoding="utf-8")
        if expected != output:
            print(f"EXPECTED_ARTIFACT_MISMATCH: {args.expected}", file=sys.stderr)
            return 1

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
